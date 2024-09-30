import os
from dotenv import load_dotenv
import logging
import sys
from flask import Flask, render_template, request, redirect, jsonify, url_for, session
from data_manager import DataManager, Config
from models import Feedback, Subscriber
from datetime import datetime, timedelta
import re
from helpers import sanitize_filename
from flask_mail import Mail, Message
from sqlalchemy.exc import IntegrityError
from functools import wraps
import secrets

# Load environment variables from .env file for local development
if os.environ.get('FLASK_ENV') != 'production':
    load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

config = Config(
    DATA_DIR=os.environ.get('DATA_DIR', 'data'),
    SUPPORTED_CITIES_FILE=os.environ.get('SUPPORTED_CITIES_FILE', 'config/supported_cities.json'),
    SUPPORTED_LANGUAGES_FILE=os.environ.get('SUPPORTED_LANGUAGES_FILE', 'config/supported_languages.json'),
    DATABASE_URL=os.environ.get('DATABASE_URL', 'sqlite:///instance/cities.db')
)
data_manager = DataManager(config)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

@app.before_request
def redirect_www():
    if request.headers.get('X-Forwarded-Proto', 'http') == 'https':
        if request.host.startswith('www.'):
            return redirect(
                'https://' + request.host[4:] + request.path,
                code=301
            )
            
# Add this decorator to routes that require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("Checking if user is logged in...")  # Add this line
        if 'subscriber_id' not in session:
            print("User is not logged in, returning 401")  # Add this line
            return jsonify({'redirect': 'auth_popup'}), 401
        print("User is logged in, proceeding to view")  # Add this line
        return f(*args, **kwargs)
    return decorated_function
           
@app.route('/')
def index():
    """
    Renders the landing page with a grid of cities.
    """
    
    cities_overview = data_manager.get_cities_overview()
    selected_language = request.args.get('language', 'English')
    supported_languages = data_manager.supported_languages

    if selected_language not in supported_languages:
        selected_language = 'English'
    
    return render_template('index.html', 
                           cities=cities_overview, 
                           supported_languages=supported_languages, 
                           selected_language=selected_language)

@app.route('/city/<eurostat_code>')
@login_required
def city_detail(eurostat_code):
    """
    Renders the city detail page with comprehensive information about the city.
    """
    city_full_details = data_manager.get_city_full_details(eurostat_code)
    if city_full_details is None:
        return render_template('city_not_found.html', eurostat_code=eurostat_code), 404
    else:   
        return render_template('city_detail.html', city=city_full_details)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    content = request.json.get('feedback')
    if content:
        with data_manager.database_manager.get_session() as db:
            try:
                new_feedback = Feedback(content=content, timestamp=datetime.utcnow())
                db.add(new_feedback)
                db.commit()
                logger.info(f"Feedback submitted: {content[:50]}...")
                return jsonify({"message": "Feedback submitted successfully"}), 200
            except Exception as e:
                db.rollback()
                logger.error(f"Error submitting feedback: {str(e)}")
                return jsonify({"message": 'An error occurred while submitting your feedback'}), 500
    return jsonify({"message": "No feedback content provided"}), 400

@app.route('/join_waitlist', methods=['POST'])
def join_waitlist():
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400
    
    # Server-side email validation
    email_regex = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    if not email_regex.match(email):
        return jsonify({'success': False, 'message': 'Invalid email format'}), 400
    
    with data_manager.database_manager.get_session() as db:
        try:
            existing_subscriber = db.query(Subscriber).filter_by(email=email).first()
            if existing_subscriber:
                return jsonify({'success': False, 'message': 'This email is already subscribed'}), 400

            new_subscriber = Subscriber(email=email)
            db.add(new_subscriber)
            db.commit()
            logger.info(f"New subscriber added: {email}")
            return jsonify({'success': True, 'message': 'Successfully added to waitlist'}), 200
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding subscriber: {str(e)}")
            return jsonify({'success': False, 'message': 'Error adding to waitlist'}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            email = request.json.get('email')
        else:
            email = request.form.get('email')

        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400

        with data_manager.database_manager.get_session() as db:
            subscriber = db.query(Subscriber).filter_by(email=email).first()
            if not subscriber:
                subscriber = Subscriber(email=email)
                db.add(subscriber)
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()
                    return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500

            token = Subscriber.generate_token()
            subscriber.login_token = token
            subscriber.token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.commit()

        login_link = url_for('verify_login', token=token, _external=True)
        send_login_email(email, login_link)

        # Check if the request wants a JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Login link sent to your email'}), 200
        else:
            return redirect(url_for('index'))

    # If it's a GET request or doesn't want JSON, render the login template
    return render_template('login.html')

@app.route('/verify-login/<token>')
def verify_login(token):
    with data_manager.database_manager.get_session() as db:
        subscriber = db.query(Subscriber).filter_by(login_token=token).first()
        if subscriber and subscriber.token_expiry > datetime.utcnow():
            subscriber.last_login = datetime.utcnow()
            subscriber.login_token = None
            subscriber.token_expiry = None
            db.commit()
            session['subscriber_id'] = subscriber.id
            return redirect(url_for('index'))
        else:
            return render_template('invalid_token.html'), 400

@app.route('/logout')
def logout():
    session.pop('subscriber_id', None)
    return redirect(url_for('index'))

def send_login_email(email, login_link):
       try:
           msg = Message('Your Login Link', recipients=[email])
           msg.body = f'Click the following link to log in: {login_link}'
           mail.send(msg)
           logger.info(f"Login email sent to {email}")
       except Exception as e:
           logger.error(f"Failed to send login email to {email}. Error: {str(e)}")
           raise



@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Make this function available in templates
app.jinja_env.filters['sanitize_filename'] = sanitize_filename

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    debug = os.environ.get('FLASK_DEBUG', False)
    app.run(debug=debug, host='0.0.0.0', port=port)