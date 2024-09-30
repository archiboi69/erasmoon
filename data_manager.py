from __future__ import annotations

import os
import json
import pandas as pd
import logging
from sqlalchemy.orm import joinedload
from sqlalchemy import desc
from models import City, Metrics
from database import SessionLocal
from contextlib import contextmanager
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import re
from sqlalchemy import func
from datetime import date

logger = logging.getLogger(__name__)

@dataclass
class Config:
    DATA_DIR: str
    SUPPORTED_CITIES_FILE: str
    LANGUAGE_SKILLS_FILE: str
    SUPPORTED_LANGUAGES_FILE: str
    DATABASE_URL: str
    

class DataLoader:
    """
    Handles loading of data from various sources such as CSV and JSON files.
    """

    def __init__(self, data_dir: str, language_skills_file: str, supported_languages_file: str, supported_cities_file: str):
        """
        Initializes the DataLoader with specified directories and file names.

        Args:
            data_dir (str): Directory where data files are located.
            LANGUAGE_SKILLS_FILE (str): CSV file containing language data.
            country_emojis_file (str): JSON file containing country emojis.
            supported_cities_file (str): JSON file containing supported cities.
        """
        self.data_dir = data_dir
        self.language_skills_file = language_skills_file
        self.supported_languages_file = supported_languages_file
        self.eurostat_data_dir = os.path.join(data_dir, 'eurostat')
        self.supported_cities_file = supported_cities_file
        self.supported_cities = self.load_supported_cities()

    def load_supported_languages(self) -> List[str]:
        """
        Loads supported languages from a JSON file.

        Returns:
            List[str]: List of supported languages.
        """
        try:
            with open(self.supported_languages_file, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            logging.error(f"Supported languages file not found: {self.supported_languages_file}")
            return []
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from {self.supported_languages_file}: {e}")
            return []

    def load_supported_cities(self) -> List[str]:
        """
        Loads supported cities from a JSON file.

        Returns:
            List[str]: List of supported city Eurostat codes.
        """
        try:
            with open(self.supported_cities_file, 'r') as file:
                cities = json.load(file)
                return [city['eurostat_code'] for city in cities]
        except FileNotFoundError:
            logging.error(f"Supported cities file not found: {self.supported_cities_file}")
            return []
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from {self.supported_cities_file}: {e}")
            return []

    def load_language_skills_data(self) -> Dict[str, Dict[str, float]]:
        """
        Loads language data from a CSV file into a nested dictionary.

        Returns:
            Dict[str, Dict[str, float]]: Nested dictionary with country as the outer key
                                         and language as the inner key.
        """
        try:
            file_path = os.path.join(self.data_dir, self.language_skills_file)
            logging.info(f"Loading language data from {file_path}")
            
            df = pd.read_csv(file_path, index_col='Language')
            language_data = df.astype(float).to_dict()

            logging.info(f"Language data loaded successfully. {len(language_data)} countries processed.")
            return language_data
        except FileNotFoundError:
            logging.error(f"Language file not found: {self.language_skills_file}")
            return {}
        except pd.errors.ParserError as e:
            logging.error(f"Error parsing CSV file {self.language_skills_file}: {e}")
            return {}
        except Exception as e:
            logging.error(f"Unexpected error loading language data: {e}")
            return {}

    def import_eurostat_urb_percep(self, topic: str = None) -> pd.DataFrame:
        """
        Imports Eurostat data for a given topic or all topics if no topic is specified.

        Args:
            topic (str): The topic to import.

        Returns:
            pd.DataFrame: The Eurostat data with one row per city.
        """
        def fallbacks(group):
            for pair in indicator_pairs:
                pair_data = group[group['indic_ur'].isin(pair)]
                if len(pair_data) == 2:
                    return pair_data['OBS_VALUE'].sum()
            return None
        
        file_path = os.path.join(self.data_dir, 'eurostat', 'urb_percep_linear.csv')
        
        # Initialize an empty DataFrame
        result_df = pd.DataFrame({'eurostat_code': self.supported_cities})
        
        if topic == 'safety' or topic is None:
            safety_indicators = ['PS3290V', 'PS3291V', 'PS3300V', 'PS3301V', 'PS3514V', 'PS3515V', 'PS3519V', 'PS3520V']
            safety_df = self._load_eurostat_linear_csv(file_path, safety_indicators)

            if not safety_df.empty:
                # Define indicator pairs in order of preference
                indicator_pairs = [('PS3514V', 'PS3515V'), ('PS3290V', 'PS3291V'), 
                                   ('PS3519V', 'PS3520V'), ('PS3300V', 'PS3301V')]

                # Apply fallbacks to each group
                safety_data = safety_df.groupby('cities').apply(fallbacks).reset_index()
                
                safety_data.columns = ['eurostat_code', 'safety_index']
                safety_data['safety_index'] = safety_data['safety_index'].round(1)

                # Merge with result_df
                result_df = result_df.merge(safety_data, on='eurostat_code', how='left')
            else:
                # If no data was found, add an empty 'safety_index' column
                result_df['safety_index'] = None
                logging.warning("No safety data found for any city.")
    
        if topic == 'public_transport' or topic is None:
            public_transport_indicators = ['PS1012V', 'PS1013V']
            public_transport_df = self._load_eurostat_linear_csv(file_path, public_transport_indicators)

            if not public_transport_df.empty:
                # Sum the values for both indicators for each city
                public_transport_data = public_transport_df.groupby('cities')['OBS_VALUE'].sum().reset_index()
                public_transport_data = public_transport_data.rename(columns={'cities': 'eurostat_code', 'OBS_VALUE': 'public_transport_satisfaction'})
                public_transport_data['public_transport_satisfaction'] = public_transport_data['public_transport_satisfaction'].round(1)

                # Merge with result_df
                result_df = result_df.merge(public_transport_data, on='eurostat_code', how='left')
            else:
                # If no data was found, add an empty 'public_transport_satisfaction' column
                result_df['public_transport_satisfaction'] = None
                logging.warning("No public transport data found for any city.")

        # Sort the result DataFrame by eurostat_code
        result_df = result_df.sort_values('eurostat_code').reset_index(drop=True)
        
        # Remove rows where only eurostat_code is present (all other columns are null)
        result_df = result_df.dropna(subset=result_df.columns.difference(['eurostat_code']), how='all')
        
        return result_df

    def _load_eurostat_linear_csv(self, file_path: str, indicators: List[str] = None) -> pd.DataFrame:
        """
        Loads Eurostat linear data from a CSV file.
        """
        try:
            df = pd.read_csv(file_path)
            # Ensure the DataFrame has the expected columns
            expected_columns = ['DATAFLOW', 'indic_ur', 'cities', 'TIME_PERIOD', 'OBS_VALUE']
            df = df[expected_columns]
            
            # Filter the DataFrame for the specified indicators
            if indicators:
                df = df[df['indic_ur'].isin(indicators)]

            # Create a set of supported cities and countries for faster lookup
            supported_cities_set = set(self.supported_cities)
            supported_countries_set = {city[:2] for city in self.supported_cities}
            
            # Use numpy's vectorized operations for filtering
            mask = df['cities'].isin(supported_cities_set) | (df['cities'].isin(supported_countries_set))
            df = df[mask]
            
            # Convert the TIME_PERIOD column to datetime
            df['TIME_PERIOD'] = pd.to_datetime(df['TIME_PERIOD'], format='%Y')
            
            # Convert the OBS_VALUE column to numeric, coercing errors to NaN
            df['OBS_VALUE'] = pd.to_numeric(df['OBS_VALUE'], errors='coerce')
            
            # Drop rows with missing values in OBS_VALUE
            df = df.dropna(subset=['OBS_VALUE'])

            # Group by cities and indic_ur, then sort within each group by TIME_PERIOD
            # to get the newest value for each indicator for each city
            df = df.sort_values(['cities', 'indic_ur', 'TIME_PERIOD'], ascending=[True, True, False])
            # Keep only the first (newest) row for each city-indicator combination
            df = df.groupby(['cities', 'indic_ur']).first().reset_index()
            
            return df

        except FileNotFoundError as e:
            logging.error(f"File not found: {e.filename}")
            return pd.DataFrame()
        except pd.errors.ParserError as e:
            logging.error(f"Error parsing CSV file {file_path}: {e}")
            return pd.DataFrame()
        except pd.errors.EmptyDataError:
            logging.error(f"Eurostat linear file is empty {file_path}")
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Error loading Eurostat linear file {file_path}: {e}")
            return pd.DataFrame()

class DataManager:
    """
    Coordinates data loading, processing, and database interactions.
    """
    def __init__(self, config: Config):
        """
        Initializes the DataManager with configuration settings.

            Args:
            config (Config): Configuration object.
        """
        self.database_manager = DatabaseManager(session_factory=SessionLocal)
        self.data_loader = DataLoader(
            data_dir=config.DATA_DIR,
            language_skills_file=config.LANGUAGE_SKILLS_FILE,
            supported_languages_file=config.SUPPORTED_LANGUAGES_FILE,
            supported_cities_file=config.SUPPORTED_CITIES_FILE
        )
        self.language_data = self.data_loader.load_language_skills_data()
        self.supported_languages = self.data_loader.load_supported_languages()
        
        self.data_processor = DataProcessor(
            language_data=self.language_data,
            database_manager=self.database_manager,
            supported_languages=self.supported_languages
        )

    def get_cities_overview(self) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves enriched general data for all cities for index.html.

        Returns:
            Optional[List[Dict[str, Any]]]: List of enriched cities or None if not found.
        """
        return self.database_manager.fetch_cities_overview(
            data_processor=self.data_processor
        )
    
    def get_city_full_details(self, eurostat_code: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves and enriches detailed data for a specific city for city_detail.html.

        Args:
            eurostat_code (str): Eurostat code of the city.

        Returns:
            Optional[Dict[str, Any]]: Dictionary containing detailed city data or None if not found.
        """
        sanitized_eurostat_code = self.sanitize_eurostat_code(eurostat_code)
        if sanitized_eurostat_code is None:
            logging.warning(f"Invalid eurostat_code provided: {eurostat_code}")
            return None

        return self.database_manager.fetch_city_full_details(
            eurostat_code=sanitized_eurostat_code,
            data_processor=self.data_processor
        )

    def update_eurostat_urb_percep(self, topic: str = None) -> pd.DataFrame:
        """
        Updates the Eurostat data for a given topic or all topics if no topic is specified.

        Args:
            topic (str): The topic to update.
    
        Returns:
            pd.DataFrame: The updated Eurostat data.
        """
        urb_percep_df = self.data_loader.import_eurostat_urb_percep(topic)
        self.database_manager.update_metrics_db(urb_percep_df)


    @staticmethod
    def sanitize_eurostat_code(eurostat_code: str) -> Optional[str]:
        """
        Sanitizes and validates the eurostat_code.

        Args:
            eurostat_code (str): The eurostat_code to sanitize and validate.

        Returns:
            Optional[str]: The sanitized eurostat_code if valid, None otherwise.
        """
        # Remove any whitespace and convert to uppercase
        sanitized = eurostat_code.strip().upper()

        # Validate the format (e.g., "AT001C" - two letters followed by 3 digits and "C")
        if re.match(r'^[A-Z]{2}\d{3}C$', sanitized):
            return sanitized
        else:
            return None

    def close(self):
        """
        Closes any resources held by DataManager.
        """
        self.database_manager.close()
        logging.info("DataManager resources have been released.")


class DatabaseManager:
    """
    Manages database connections and operations.
    """

    def __init__(self, session_factory):
        """
        Initializes the DatabaseManager with a session factory.

        Args:
            session_factory: SQLAlchemy session factory.
        """
        self.session_factory = session_factory

    @contextmanager
    def get_session(self):
        """
        Provides a transactional scope around a series of operations.

        Yields:
            Session: SQLAlchemy session object.
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database connection error: {str(e)}")
            logger.error(f"Current working directory: {os.getcwd()}")
            logger.error(f"Files in current directory: {os.listdir('.')}")
            raise
        finally:
            session.close()

    def fetch_cities_overview(self, data_processor: 'DataProcessor') -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves and enriches general data for all cities for the index view.

        Args:
            data_processor (DataProcessor): Instance for data enrichment.

        Returns:
            Optional[List[Dict[str, Any]]]: List of enriched cities or None if not found.
        """
        try:
            with self.get_session() as session:
                cities = session.query(City).options(
                    joinedload(City.climate),
                    joinedload(City.cost_of_living),
                    joinedload(City.metrics),
                ).order_by(desc(City.erasmus_population)).all()

                if not cities:
                    logging.warning("No cities found in the database.")
                    return []

                enriched_overviews = []
                for city in cities:
                    try:
                        enriched = data_processor.enrich_overview(city)
                        enriched_overviews.append(enriched)
                        logging.debug(f"Enriched data for city: {city.eurostat_code}")
                    except Exception as e:
                        logging.error(f"Error enriching city {city.eurostat_code}: {e}")

                logging.info(f"Successfully enriched overview data for {len(enriched_overviews)} cities.")
                return enriched_overviews
        except Exception as e:
            logging.error(f"Error retrieving enriched cities for index: {e}")
            return None

    def fetch_city_full_details(self, eurostat_code: str, data_processor: DataProcessor) -> Optional[Dict[str, Any]]:
        """
        Retrieves and enriches detailed data for a specific city.

        Args:
            city_id (str): Eurostat code of the city.
            data_processor (DataProcessor): Instance for data enrichment.

        Returns:
            Optional[Dict[str, Any]]: Dictionary containing detailed city data or None if not found.
        """
        try:
            with self.get_session() as session:
                logging.info(f"Attempting to fetch city with eurostat_code: {eurostat_code}")
                city = session.query(City).options(
                    joinedload(City.climate),
                    joinedload(City.cost_of_living),
                    joinedload(City.guide),
                    joinedload(City.housing),
                    joinedload(City.metrics),
                    joinedload(City.universities)
                ).filter(City.eurostat_code == eurostat_code).one_or_none()

                if city is None:
                    logging.warning(f"City with eurostat_code {eurostat_code} not found in the database.")
                    return None

                logging.info(f"City found: {city.english_name} ({city.eurostat_code})")

                # Enrich the city with detailed data
                try:
                    enriched_city_details = data_processor.enrich_full_details(city)
                    logging.info(f"Successfully enriched data for city: {city.english_name}")
                    return enriched_city_details
                except Exception as enrich_error:
                    logging.error(f"Error enriching city data for {city.english_name}: {enrich_error}")
                    return None

        except Exception as e:
            logging.error(f"Error retrieving city detail for {eurostat_code}: {e}")
            return None
    
    def update_metrics_db(self, df: pd.DataFrame):
        """
        Updates the Metrics table with new data from a DataFrame.
        Only updates the fields that are present in the DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame containing the Eurostat data to update.
        """
        with self.get_session() as session:
            for _, row in df.iterrows():
                eurostat_code = row['eurostat_code']
                existing_record = session.query(Metrics).filter_by(eurostat_code=eurostat_code).first()
                
                if existing_record:
                    # Update existing record
                    for column, value in row.items():
                        if column != 'eurostat_code' and hasattr(existing_record, column):
                            setattr(existing_record, column, value)
                    existing_record.last_updated = date.today()  # Update the last_updated timestamp
                else:
                    # Create new record with only the data present in the DataFrame
                    new_record_data = {column: value for column, value in row.items() if column != 'eurostat_code'}
                    new_record_data['eurostat_code'] = eurostat_code
                    new_record_data['last_updated'] = date.today()
                    new_record = Metrics(**new_record_data)
                    session.add(new_record)
            
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                logging.error(f"Error committing changes to Metrics table: {e}")
                raise
    
        
    def close(self):
        """
        Closes the DatabaseManager and cleans up resources.
        """
        # If any persistent connections or resources are held, close them here
        logging.info("DatabaseManager has been closed.")


class DataProcessor:
    """
    Processes and enriches data using loaded datasets.
    """

    def __init__(self, language_data: Dict[str, Any], database_manager: 'DatabaseManager', supported_languages: List[str]):
        """
        Initializes the DataProcessor with language data and a DatabaseManager instance.

        Args:
            language_data (Dict[str, Any]): Nested dictionary with language proficiency data.
            database_manager (DatabaseManager): Instance to interact with the database for emojis.
        """
        self.language_data = language_data
        self.database_manager = database_manager
        self.supported_languages = supported_languages

    def enrich_overview(self, city: Any) -> Dict[str, Any]:
        """
        Enriches a single city's data with general information for the index view.

        Args:
            city (Any): SQLAlchemy City model instance.

        Returns:
            Dict[str, Any]: Dictionary containing enriched city data for index.
        """
        enriched_city = {
            'rank': None,
            'eurostat_code': city.eurostat_code,
            'local_name': city.local_name,
            'english_name': city.english_name,
            'local_country': city.local_country,
            'english_country': city.english_country,
            'country_emoji': city.country_emoji,
            'population': city.population,
            'erasmus_population': city.erasmus_population,
            'monthly_budget': self._round_to_euro(getattr(city.cost_of_living, 'monthly_budget', None)),
            'cost_of_living_plus_rent': getattr(city.cost_of_living, 'cost_of_living_plus_rent_index', None),
            'mean_feb_min': getattr(city.climate, 'mean_feb_min', None),
            'mean_jul_max': getattr(city.climate, 'mean_jul_max', None),
            'safety_index': getattr(city.metrics, 'safety_index', None),
            'university_count': getattr(city.metrics, 'university_count', None),
            'public_transport_satisfaction': getattr(city.metrics, 'public_transport_satisfaction', None),
            'language_percentages': self._compute_language_proficiency(city)
        }

        return enriched_city

    def enrich_full_details(self, city: Any) -> Dict[str, Any]:
        """
        Enriches a single city's data with detailed information for the detail view.

        Args:
            city (Any): SQLAlchemy City model instance.

        Returns:
            Dict[str, Any]: Dictionary containing enriched city data for detail.
        """
        try:
            # First, get the general data
            enriched_city = self.enrich_overview(city)

            # Add climate data
            climate_data = {}
            for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']:
                climate_data[f'mean_{month}_min'] = getattr(city.climate, f'mean_{month}_min', None)
                climate_data[f'mean_{month}_max'] = getattr(city.climate, f'mean_{month}_max', None)
            
            enriched_city.update(climate_data)

            # Add detailed fields
            enriched_city.update({
                'lat': city.lat,
                'lon': city.lon,
                'rent_budget': self._round_to_euro(self._compute_rent_budget(
                    rent_per_sqm=getattr(city.housing, 'rent_per_sqm', None), 
                    area_per_person=getattr(city.housing, 'area_per_person', None), 
                    erasmus_factor=getattr(city.housing, 'erasmus_factor', None),
                    monthly_budget=getattr(city.cost_of_living, 'monthly_budget', None),
                    rent_index=getattr(city.cost_of_living, 'rent_index', None)
                )),
                'groceries_budget': self._round_to_euro(self._compute_groceries_budget(getattr(city.cost_of_living, 'groceries_index', None))),
                'transport_budget': self._round_to_euro(getattr(city.transport_budget, 'monthly_ticket', None)),
                'overview_text': getattr(city.guide, 'text', None),
                'housing': {
                    'rent_per_sqm': getattr(city.housing, 'rent_per_sqm', None),
                },
                'universities': self._process_universities(city.universities)
            })

            return enriched_city

        except AttributeError as ae:
            logging.error(f"AttributeError in enrich_full_details for city {city.english_name}: {ae}")
            raise
        except TypeError as te:
            logging.error(f"TypeError in enrich_full_details for city {city.english_name}: {te}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in enrich_full_details for city {city.english_name}: {e}")
            raise

    def _compute_language_proficiency(self, city: Any) -> Dict[str, Optional[float]]:
        """
        Computes language percentages based on the city's country and language data.

        Args:
            city (Any): SQLAlchemy City model instance.

        Returns:
            Dict[str, Optional[float]]: Dictionary mapping languages to their proficiency percentages.
        """
        language_percentages = {language: None for language in self.supported_languages}

        try:
            if city.english_country in self.language_data:
                country_language_skills = self.language_data[city.english_country]
                for language, skill in country_language_skills.items():
                    if skill is not None and language in self.supported_languages:
                        language_percentages[language] = skill * 100  # skill is a float between 0 and 1
            else:
                logging.warning(f"Language data for country {city.english_country} not found.")
        except KeyError as ke:
            logging.error(f"KeyError in _compute_language_proficiency for city {city.english_name}: {ke}")
        except Exception as e:
            logging.error(f"Unexpected error in _compute_language_proficiency for city {city.english_name}: {e}")

        return language_percentages


    def _compute_rent_budget(self, rent_per_sqm, area_per_person, erasmus_factor, rent_index, monthly_budget) -> int:
        """
        Calculates the rent budget based on the provided parameters.

        Args:
            rent_per_sqm (float): Rent per square meter.
            area_per_person (float): Area per person in square meters.
            erasmus_factor (float): Erasmus factor.
            rent_index (float): Rent index.
            monthly_budget (integer): Monthly budget.
        """
        if rent_per_sqm and area_per_person and erasmus_factor:
            return int(round(rent_per_sqm * area_per_person * erasmus_factor))
        elif rent_index:
            return int(round(18.5 * rent_index))
        elif monthly_budget:
            return int(round(monthly_budget * 0.6))
        else:
            logging.warning("No parameters provided to compute rent budget.")
            return 0

    def _compute_groceries_budget(self, groceries_index):
        """
        Calculates the groceries budget based on the provided parameters.

        Args:
            groceries_index (float): Groceries index.

        Returns:
            int: Calculated groceries budget.
        """
        if groceries_index is None:
            return 0
        return int(round(2.68 * groceries_index))

    def _process_universities(self, universities):
        """
        Processes university data for the detail view.

        Args:
            universities (list): List of SQLAlchemy University model instances.

        Returns:
            list: List of processed university data.
        """
        if not universities:
            return []
        
        processed_unis = []
        for uni in universities:
            size_class = getattr(uni, 'size_class', None)
            # Convert size_class to int if possible, otherwise use a default value
            try:
                size_class = int(size_class) if size_class is not None else 0
            except ValueError:
                size_class = 0
            
            try:
                processed_unis.append({
                    'erasmus_code': uni.erasmus_code,
                    'name': uni.name,
                    'english_name': getattr(uni, 'english_name', None),
                    'category': getattr(uni, 'category', None),
                    'size_class': size_class,
                    'url': getattr(uni, 'url', None),
                    'lat': getattr(uni, 'lat', None),
                    'lon': getattr(uni, 'lon', None),
                    'total_students': getattr(uni, 'total_students', None),
                })
            except Exception as e:
                logging.error(f"Error processing university {uni.name}: {e}")
                continue
        
        return sorted(processed_unis, key=lambda x: x['size_class'], reverse=True)

    @staticmethod
    def _round_to_euro(value: Optional[float]) -> Optional[int]:
        return round(value) if value is not None else None