from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, BigInteger, Numeric, Index, Text, DateTime, Boolean
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func


Base = declarative_base()

class City(Base):
    __tablename__ = 'cities'
    
    eurostat_code = Column(String(50), primary_key=True)
    local_name = Column(String(255), nullable=False, index=True)
    english_name = Column(String(255), nullable=False, index=True)
    local_country = Column(String(100), nullable=True)
    english_country = Column(String(100), nullable=True, index=True)
    country_emoji = Column(String(10), nullable=True)
    population = Column(BigInteger, nullable=True)
    erasmus_population = Column(Integer, nullable=True)
    lat = Column(Numeric(9, 6), nullable=True)
    lon = Column(Numeric(9, 6), nullable=True)
    last_updated = Column(DateTime, nullable=True, server_default=func.now(), onupdate=func.now())
    
    climate = relationship("Climate", back_populates="city", uselist=False, cascade="all, delete-orphan")
    cost_of_living = relationship("CostOfLiving", back_populates="city", uselist=False, cascade="all, delete-orphan")
    housing = relationship("Housing", back_populates="city", uselist=False, cascade="all, delete-orphan")
    metrics = relationship("Metrics", back_populates="city", uselist=False, cascade="all, delete-orphan")
    universities = relationship("University", back_populates="city", cascade="all, delete-orphan")
    guide = relationship("Guide", back_populates="city", uselist=False, cascade="all, delete-orphan")
    transport_budget = relationship("TransportBudget", back_populates="city", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<City(name='{self.local_name}', country='{self.local_country}')>"

class Climate(Base):
    __tablename__ = 'climate'

    eurostat_code = Column(String(50), ForeignKey('cities.eurostat_code'), primary_key=True)
    mean_jan_min = Column(Integer, nullable=True)
    mean_feb_min = Column(Integer, nullable=True)
    mean_mar_min = Column(Integer, nullable=True)
    mean_apr_min = Column(Integer, nullable=True)
    mean_may_min = Column(Integer, nullable=True)
    mean_jun_min = Column(Integer, nullable=True)
    mean_jul_min = Column(Integer, nullable=True)
    mean_aug_min = Column(Integer, nullable=True)
    mean_sep_min = Column(Integer, nullable=True)
    mean_oct_min = Column(Integer, nullable=True)
    mean_nov_min = Column(Integer, nullable=True)
    mean_dec_min = Column(Integer, nullable=True)
    mean_jan_max = Column(Integer, nullable=True)
    mean_feb_max = Column(Integer, nullable=True)
    mean_mar_max = Column(Integer, nullable=True)
    mean_apr_max = Column(Integer, nullable=True)
    mean_may_max = Column(Integer, nullable=True)
    mean_jun_max = Column(Integer, nullable=True)
    mean_jul_max = Column(Integer, nullable=True)
    mean_aug_max = Column(Integer, nullable=True)
    mean_sep_max = Column(Integer, nullable=True)
    mean_oct_max = Column(Integer, nullable=True)
    mean_nov_max = Column(Integer, nullable=True)
    mean_dec_max = Column(Integer, nullable=True)
    last_updated = Column(DateTime, nullable=True, server_default=func.now(), onupdate=func.now())

    city = relationship("City", back_populates="climate")

    def __repr__(self):
        return f"<Climate(eurostat_code='{self.eurostat_code}')>"

class CostOfLiving(Base):
    __tablename__ = 'cost_of_living'
    
    eurostat_code = Column(String(50), ForeignKey('cities.eurostat_code'), primary_key=True)
    monthly_budget = Column(Float, nullable=True)
    cost_of_living_index = Column(Float, nullable=True)
    rent_index = Column(Float, nullable=True)
    cost_of_living_plus_rent_index = Column(Float, nullable=True)
    groceries_index = Column(Float, nullable=True)
    restaurant_price_index = Column(Float, nullable=True)
    local_purchasing_power_index = Column(Float, nullable=True)
    last_updated = Column(DateTime, nullable=True, server_default=func.now(), onupdate=func.now())
    
    city = relationship("City", back_populates="cost_of_living")

    def __repr__(self):
        return f"<CostOfLiving(eurostat_code='{self.eurostat_code}')>"

class Guide(Base):
    __tablename__ = 'guides'
    
    eurostat_code = Column(String(50), ForeignKey('cities.eurostat_code'), primary_key=True)
    text = Column(String(10000), nullable=True)
    last_updated = Column(DateTime, nullable=True, server_default=func.now(), onupdate=func.now())
    
    city = relationship("City", back_populates="guide")

class Housing(Base):
    __tablename__ = 'housing'
    
    eurostat_code = Column(String(50), ForeignKey('cities.eurostat_code'), primary_key=True)
    rent_per_sqm = Column(Float, nullable=True)
    area_per_person = Column(Float, nullable=True)
    erasmus_factor = Column(Float, nullable=True)
    last_updated = Column(DateTime, nullable=True, server_default=func.now(), onupdate=func.now())
    
    city = relationship("City", back_populates="housing")

    def __repr__(self):
        return f"<Housing(eurostat_code='{self.eurostat_code}')>"

class Metrics(Base):
    __tablename__ = 'metrics'
    
    eurostat_code = Column(String(50), ForeignKey('cities.eurostat_code'), primary_key=True)
    safety_index = Column(Float, nullable=True)
    university_count = Column(Integer, nullable=True)
    public_transport_satisfaction = Column(Float, nullable=True)
    last_updated = Column(DateTime, nullable=True, server_default=func.now(), onupdate=func.now())
    
    city = relationship("City", back_populates="metrics")

    def __repr__(self):
        return f"<Metrics(eurostat_code='{self.eurostat_code}')>"

class TransportBudget(Base):
    __tablename__ = 'transport_budget'
    
    eurostat_code = Column(String(50), ForeignKey('cities.eurostat_code'), primary_key=True, index=True)
    source = Column(String(50), nullable=True)
    source_date = Column(Date, nullable=True)
    monthly_ticket = Column(Float, nullable=True)
    last_updated = Column(DateTime, nullable=True, server_default=func.now(), onupdate=func.now())

    city = relationship("City", back_populates="transport_budget")

    def __repr__(self):
        return f"<TransportBudget(eurostat_code='{self.eurostat_code}', source_date='{self.source_date}', monthly_ticket={self.monthly_ticket})>"

class University(Base):
    __tablename__ = 'universities'
    
    erasmus_code = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    english_name = Column(String(255), nullable=True, index=True)
    eurostat_code = Column(String(50), ForeignKey('cities.eurostat_code'), nullable=False, index=True)
    country_code = Column(String(10), nullable=True)
    category = Column(String(100), nullable=True)
    standardized_category = Column(Integer, nullable=True)
    size_class = Column(Integer, nullable=True)
    url = Column(String(2083), nullable=True)  # 2083 is the maximum URL length in some browsers
    lat = Column(Numeric(9, 6), nullable=True)
    lon = Column(Numeric(9, 6), nullable=True)
    remote_campuses = Column(String(255), nullable=True)  # Consider normalizing if multiple campuses
    total_students = Column(BigInteger, nullable=True)
    mobile_students = Column(BigInteger, nullable=True)
    generic_students = Column(BigInteger, nullable=True)
    education_students = Column(BigInteger, nullable=True)
    arts_humanities_students = Column(BigInteger, nullable=True)
    social_sciences_students = Column(BigInteger, nullable=True)
    business_law_students = Column(BigInteger, nullable=True)
    it_students = Column(BigInteger, nullable=True)
    aec_students = Column(BigInteger, nullable=True)
    agriculture_vet_students = Column(BigInteger, nullable=True)
    med_students = Column(BigInteger, nullable=True)
    services_students = Column(BigInteger, nullable=True)
    women_share = Column(Float, nullable=True)
    foreign_share = Column(Float, nullable=True)
    mobile_share = Column(Float, nullable=True)
    last_updated = Column(DateTime, nullable=True, server_default=func.now(), onupdate=func.now())

    city = relationship("City", back_populates="universities")

    __table_args__ = (
        Index('idx_university_city_id', 'eurostat_code'),
    )

    def __repr__(self):
        return f"<University(name='{self.name}', eurostat_code='{self.eurostat_code}')>"

class Feedback(Base):
    __tablename__ = 'feedback'

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f'<Feedback {self.id}>'

class Language(Base):
    __tablename__ = 'languages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    language = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    percentage = Column(Float, nullable=False)
    last_updated = Column(DateTime, nullable=True, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Language(id={self.id}, language='{self.language}', country='{self.country}', percentage={self.percentage})>"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    auth0_id = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    premium_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f'<User {self.email}>'