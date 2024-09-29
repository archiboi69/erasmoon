import os
from dotenv import load_dotenv
if os.path.exists('.env'):
    load_dotenv()

import logging
import sys
from flask import Flask, render_template, request, jsonify
from data_manager import DataManager, Config
from models import Feedback, Subscriber
from datetime import datetime
import re

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
    LOG_DIR=os.environ.get('LOG_DIR', 'logs'),
    SUPPORTED_CITIES_FILE=os.environ.get('SUPPORTED_CITIES_FILE', 'config/supported_cities.json'),
    SUPPORTED_LANGUAGES_FILE=os.environ.get('SUPPORTED_LANGUAGES_FILE', 'config/supported_languages.json'),
    LANGUAGE_SKILLS_FILE=os.environ.get('LANGUAGE_SKILLS_FILE', 'europeans_and_their_languages_2024_summed.csv'),
)
data_manager = DataManager(config)

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
