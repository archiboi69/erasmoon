from data_manager import DataManager, Config
import os
from dotenv import load_dotenv

load_dotenv()

config = Config(
    DATA_DIR=os.environ.get('DATA_DIR', 'data'),
    SUPPORTED_CITIES_FILE=os.environ.get('SUPPORTED_CITIES_FILE', 'config/supported_cities.json'),
    SUPPORTED_LANGUAGES_FILE=os.environ.get('SUPPORTED_LANGUAGES_FILE', 'config/supported_languages.json'),
    LANGUAGE_SKILLS_FILE=os.environ.get('LANGUAGE_SKILLS_FILE', 'europeans_and_their_languages_2024_summed.csv'),
    DATABASE_URL=os.environ.get('DATABASE_URL', 'sqlite:///instance/cities.db')
)
data_manager = DataManager(config)

data_manager.update_eurostat_urb_percep()