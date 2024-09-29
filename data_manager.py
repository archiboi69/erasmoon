from __future__ import annotations

import os
import json
import pandas as pd
import logging
from sqlalchemy.orm import joinedload
from sqlalchemy import desc
from models import City, TransportBudget
from database import SessionLocal
from contextlib import contextmanager
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import re
from sqlalchemy import func


logger = logging.getLogger(__name__)

@dataclass
class Config:
    DATA_DIR: str
    SUPPORTED_CITIES_FILE: str
    LANGUAGE_SKILLS_FILE: str
    SUPPORTED_LANGUAGES_FILE: str
    
    

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

    def import_eurostat_data(self, theme_dir: str) -> pd.DataFrame:
        """
        Imports or updates Eurostat data from CSV files in a specific theme directory.

        Args:
            theme_dir (str): Name of the theme directory (e.g., 'transport-budget').

        Returns:
            pd.DataFrame: Processed Eurostat data.
        """
        try:
            dfs = []
            theme_path = os.path.join(self.eurostat_data_dir, theme_dir)
            for file_name in os.listdir(theme_path):
                if file_name.endswith('.csv'):
                    file_path = os.path.join(theme_path, file_name)
                    logging.info(f"Importing Eurostat data from {file_path}")

                    # Read the CSV file
                    df = pd.read_csv(file_path)
                    dfs.append(df)

            # Concatenate all dataframes
            combined_df = pd.concat(dfs, ignore_index=True)

            # Process the combined data
            processed_df = self._process_eurostat_data(combined_df, theme_dir)

            logging.info(f"Eurostat data for {theme_dir} imported and processed successfully.")
            return processed_df
        except FileNotFoundError as e:
            logging.error(f"Eurostat file not found: {e.filename}")
            return pd.DataFrame()
        except pd.errors.EmptyDataError:
            logging.error(f"One of the files is empty.")
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Error importing Eurostat data: {e}")
            return pd.DataFrame()

    def _process_eurostat_data(self, df: pd.DataFrame, theme_dir: str) -> pd.DataFrame:
        """
        Process the Eurostat data based on the theme directory.
        This method should be customized based on the specific needs of each dataset.
        """
        # Ensure the DataFrame has the expected columns
        expected_columns = ['DATAFLOW', 'LAST UPDATE', 'freq', 'indic_ur', 'cities', 'TIME_PERIOD', 'OBS_VALUE']
        df = df[expected_columns]

        # Drop rows with missing values in OBS_VALUE
        df = df.dropna(subset=['OBS_VALUE'])

        # Convert the TIME_PERIOD column to datetime
        df['TIME_PERIOD'] = pd.to_datetime(df['TIME_PERIOD'], format='%Y')

        # Convert the OBS_VALUE column to numeric, coercing errors to NaN
        df['OBS_VALUE'] = pd.to_numeric(df['OBS_VALUE'], errors='coerce')

        if theme_dir == 'transport-budget':
            # Drop rows where OBS_VALUE is 0
            df = df[df['OBS_VALUE'] != 0]
            
            # Group by cities and TIME_PERIOD, keeping only the newest data for each city
            df = df.sort_values('TIME_PERIOD', ascending=False).groupby('cities').first().reset_index()
            
            # Process data specifically for transport budget
            transport_budget_df = pd.DataFrame(columns=expected_columns)
            for city in self.supported_cities:
                city_data = df[df['cities'] == city]
                if city_data.empty:
                    # Fallback to the Functional Urban Area
                    city_data = df[df['cities'] == city[:-1] + 'F']
                    if city_data.empty:
                        # Fallback to the Country
                        city_data = df[df['cities'] == city[:2]]
                
                if not city_data.empty:
                    transport_budget_df = pd.concat([transport_budget_df, city_data], ignore_index=True)
                else:
                    # Add a row for the city with empty values
                    empty_row = pd.DataFrame({
                        'DATAFLOW': [None],
                        'LAST UPDATE': [None],
                        'freq': [None],
                        'indic_ur': [None],
                        'cities': [city],
                        'TIME_PERIOD': [None],
                        'OBS_VALUE': [None]
                    })
                    transport_budget_df = pd.concat([transport_budget_df, empty_row], ignore_index=True)
                    logging.warning(f"No data found for city {city} or its fallbacks.")
            
            return transport_budget_df

        # For other themes, you can add more processing logic here
        return df


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

    def update_transport_budget(self):
        """
        Updates the transport budget data in the database.
        """
        theme_dir = 'transport-budget'
        transport_budget_df = self.data_loader.import_eurostat_data(theme_dir)
        self._update_transport_budget_table(transport_budget_df)

    def _update_transport_budget_table(self, df: pd.DataFrame):
        """
        Updates the transport_budget table with new data from a DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame containing the transport budget data to update.
        """
        with self.database_manager.get_session() as session:
            for _, row in df.iterrows():
                city = row['cities']
                existing_record = session.query(TransportBudget).filter_by(eurostat_code=city).first()
                
                # Convert NaT (Not a Time) to None for source_date
                source_date = None if pd.isna(row['TIME_PERIOD']) else row['TIME_PERIOD']
                
                # Convert NaN to None for monthly_ticket
                monthly_ticket = None if pd.isna(row['OBS_VALUE']) else float(row['OBS_VALUE'])
                
                if existing_record:
                    # Update existing record
                    existing_record.source = row['DATAFLOW']
                    existing_record.source_date = source_date
                    existing_record.monthly_ticket = monthly_ticket
                    existing_record.last_updated = func.now()  # Update the last_updated timestamp
                else:
                    # Insert new record
                    new_record = TransportBudget(
                        eurostat_code=city,
                        source=row['DATAFLOW'],
                        source_date=source_date,
                        monthly_ticket=monthly_ticket,
                        last_updated=func.now()  # Set the initial last_updated timestamp
                    )
                    session.add(new_record)
            
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                logging.error(f"Error committing changes to transport_budget table: {e}")
                raise


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
            logging.error(f"Session rollback due to exception: {e}")
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
                    'lon': getattr(uni, 'lon', None)
                })
            except Exception as e:
                logging.error(f"Error processing university {uni.name}: {e}")
                continue
        
        return sorted(processed_unis, key=lambda x: x['size_class'], reverse=True)

    @staticmethod
    def _round_to_euro(value: Optional[float]) -> Optional[int]:
        return round(value) if value is not None else None