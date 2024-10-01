import json
import logging
import os
import re
import sys
from datetime import datetime
from functools import wraps
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, redirect, render_template, request, session, url_for
from flask_mail import Mail, Message
from flask.cli import with_appcontext
import click
from alembic.config import Config as AlembicConfig
from alembic import command

from data_manager import Config, DataManager
from helpers import sanitize_filename
from models import Feedback, User

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

# Auth0 configuration
oauth = OAuth(app)
auth0 = oauth.register(
    'auth0',
    client_id=os.environ.get('AUTH0_CLIENT_ID'),
    client_secret=os.environ.get('AUTH0_CLIENT_SECRET'),
    api_base_url=f"https://{os.environ.get('AUTH0_DOMAIN')}",
    client_kwargs={
        'scope': 'openid profile email',
    },
    server_metadata_url=f'https://{os.environ.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)

def is_primary_region():
    return os.environ.get('FLY_REGION') == os.environ.get('PRIMARY_REGION')

def primary_region_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_primary_region():
            response = make_response()
            response.headers['fly-replay'] = f"region={os.environ.get('PRIMARY_REGION')}"
            return response
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def redirect_www():
    if request.headers.get('X-Forwarded-Proto', 'http') == 'https':
        if request.host.startswith('www.'):
            return redirect(
                'https://' + request.host[4:] + request.path,
                code=301
            )

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
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
@login_required
@primary_region_required
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
@primary_region_required
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
            existing_user = db.query(User).filter_by(email=email).first()
            if existing_user:
                return jsonify({'success': False, 'message': 'This email is already registered'}), 400

            new_user = User(email=email, auth0_id=f"waitlist_{email}")
            db.add(new_user)
            db.commit()
            logger.info(f"New user added to waitlist: {email}")
            return jsonify({'success': True, 'message': 'Successfully added to waitlist'}), 200
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding user to waitlist: {str(e)}")
            return jsonify({'success': False, 'message': 'Error adding to waitlist'}), 500

@app.route("/callback")
def callback():
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    session["user"] = {
        "user_id": userinfo["sub"],
        "email": userinfo["email"],
        "name": userinfo['name'],
        "picture": userinfo.get('picture',''),
        "email_verified": userinfo.get('email_verified',False)
    }

    # Create or update user in local database
    with data_manager.database_manager.get_session() as db:
        user = db.query(User).filter_by(auth0_id=userinfo["sub"]).first()
        if not user:
            user = User(
                auth0_id=userinfo["sub"],
                email=userinfo["email"],
                name=userinfo['name'],
                picture=userinfo.get("picture", ""),
                email_verified=userinfo.get("email_verified", False)
            )
            db.add(user)
        else:
            user.name = userinfo['name']
            user.picture = userinfo.get("picture", user.picture)
            user.email_verified = userinfo.get("email_verified", user.email_verified)
        user.last_login = datetime.utcnow()
        db.commit()

    # Set user in sessionStorage and reload the page
    return """
    <script>
        sessionStorage.setItem('user', JSON.stringify({user}));
        window.location.href = '{url}';
    </script>
    """.format(user=json.dumps(session["user"]), url=url_for('index'))

@app.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri=url_for('callback', _external=True))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + os.environ.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("index", _external=True),
                "client_id": os.environ.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Make this function available in templates
app.jinja_env.filters['sanitize_filename'] = sanitize_filename

@app.cli.command("db_upgrade")
@with_appcontext
def db_upgrade():
    """Apply database migrations."""
    alembic_cfg = AlembicConfig("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    click.echo("Database schema updated.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    debug = os.environ.get('FLASK_DEBUG', False)
    app.run(debug=debug, host='0.0.0.0', port=port)