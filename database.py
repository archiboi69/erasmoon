from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from models import Base

DATABASE_URL = 'sqlite:///instance/cities.db'

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
db_session = scoped_session(sessionmaker(bind=engine))

def init_db():
    Base.metadata.create_all(bind=engine)