"""Initial migration

Revision ID: feba1deeed79
Revises: 
Create Date: 2024-09-28 14:26:19.834428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'feba1deeed79'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create new tables with desired schemas
    op.create_table('cities_new',
        sa.Column('eurostat_code', sa.String(length=50), nullable=False),
        sa.Column('local_name', sa.String(length=255), nullable=False),
        sa.Column('english_name', sa.String(length=255), nullable=False),
        sa.Column('local_country', sa.String(length=100), nullable=True),
        sa.Column('english_country', sa.String(length=100), nullable=True),
        sa.Column('country_emoji', sa.String(length=10), nullable=True),
        sa.Column('population', sa.BigInteger(), nullable=True),
        sa.Column('erasmus_population', sa.Integer(), nullable=True),
        sa.Column('lat', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('lon', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('last_updated', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('eurostat_code')
    )
    
    op.create_table('climate_new',
        sa.Column('eurostat_code', sa.String(length=50), nullable=False),
        sa.Column('mean_jan_min', sa.Integer(), nullable=True),
        sa.Column('mean_feb_min', sa.Integer(), nullable=True),
        sa.Column('mean_mar_min', sa.Integer(), nullable=True),
        sa.Column('mean_apr_min', sa.Integer(), nullable=True),
        sa.Column('mean_may_min', sa.Integer(), nullable=True),
        sa.Column('mean_jun_min', sa.Integer(), nullable=True),
        sa.Column('mean_jul_min', sa.Integer(), nullable=True),
        sa.Column('mean_aug_min', sa.Integer(), nullable=True),
        sa.Column('mean_sep_min', sa.Integer(), nullable=True),
        sa.Column('mean_oct_min', sa.Integer(), nullable=True),
        sa.Column('mean_nov_min', sa.Integer(), nullable=True),
        sa.Column('mean_dec_min', sa.Integer(), nullable=True),
        sa.Column('mean_jan_max', sa.Integer(), nullable=True),
        sa.Column('mean_feb_max', sa.Integer(), nullable=True),
        sa.Column('mean_mar_max', sa.Integer(), nullable=True),
        sa.Column('mean_apr_max', sa.Integer(), nullable=True),
        sa.Column('mean_may_max', sa.Integer(), nullable=True),
        sa.Column('mean_jun_max', sa.Integer(), nullable=True),
        sa.Column('mean_jul_max', sa.Integer(), nullable=True),
        sa.Column('mean_aug_max', sa.Integer(), nullable=True),
        sa.Column('mean_sep_max', sa.Integer(), nullable=True),
        sa.Column('mean_oct_max', sa.Integer(), nullable=True),
        sa.Column('mean_nov_max', sa.Integer(), nullable=True),
        sa.Column('mean_dec_max', sa.Integer(), nullable=True),
        sa.Column('last_updated', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['eurostat_code'], ['cities.eurostat_code'], ),
        sa.PrimaryKeyConstraint('eurostat_code')
    )
    
    op.create_table('cost_of_living_new',
        sa.Column('eurostat_code', sa.String(length=50), nullable=False),
        sa.Column('monthly_budget', sa.Float(), nullable=True),
        sa.Column('groceries_budget', sa.Float(), nullable=True),
        sa.Column('transport_budget', sa.Float(), nullable=True),
        sa.Column('cost_of_living_index', sa.Float(), nullable=True),
        sa.Column('rent_index', sa.Float(), nullable=True),
        sa.Column('cost_of_living_plus_rent_index', sa.Float(), nullable=True),
        sa.Column('groceries_index', sa.Float(), nullable=True),
        sa.Column('restaurant_price_index', sa.Float(), nullable=True),
        sa.Column('local_purchasing_power_index', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['eurostat_code'], ['cities.eurostat_code'], ),
        sa.PrimaryKeyConstraint('eurostat_code')
    )
    
    op.create_table('guides_new',
        sa.Column('eurostat_code', sa.String(length=50), nullable=False),
        sa.Column('text', sa.String(length=10000), nullable=True),
        sa.Column('last_updated', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['eurostat_code'], ['cities.eurostat_code'], ),
        sa.PrimaryKeyConstraint('eurostat_code')
    )
    
    op.create_table('housing_new',
        sa.Column('eurostat_code', sa.String(length=50), nullable=False),
        sa.Column('rent_per_sqm', sa.Float(), nullable=True),
        sa.Column('area_per_person', sa.Float(), nullable=True),
        sa.Column('erasmus_factor', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['eurostat_code'], ['cities.eurostat_code'], ),
        sa.PrimaryKeyConstraint('eurostat_code')
    )
    
    op.create_table('metrics_new',
        sa.Column('eurostat_code', sa.String(length=50), nullable=False),
        sa.Column('safety_index', sa.Float(), nullable=True),
        sa.Column('university_count', sa.Integer(), nullable=True),
        sa.Column('public_transport_satisfaction', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['eurostat_code'], ['cities.eurostat_code'], ),
        sa.PrimaryKeyConstraint('eurostat_code')
    )
    
    op.create_table('universities_new',
        sa.Column('erasmus_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('english_name', sa.String(length=255), nullable=True),
        sa.Column('eurostat_code', sa.String(length=50), nullable=False),
        sa.Column('country_code', sa.String(length=10), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('standardized_category', sa.Integer(), nullable=True),
        sa.Column('size_class', sa.Integer(), nullable=True),
        sa.Column('url', sa.String(length=2083), nullable=True),
        sa.Column('lat', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('lon', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('remote_campuses', sa.String(length=255), nullable=True),
        sa.Column('total_students', sa.BigInteger(), nullable=True),
        sa.Column('mobile_students', sa.BigInteger(), nullable=True),
        sa.Column('generic_students', sa.BigInteger(), nullable=True),
        sa.Column('education_students', sa.BigInteger(), nullable=True),
        sa.Column('arts_humanities_students', sa.BigInteger(), nullable=True),
        sa.Column('social_sciences_students', sa.BigInteger(), nullable=True),
        sa.Column('business_law_students', sa.BigInteger(), nullable=True),
        sa.Column('it_students', sa.BigInteger(), nullable=True),
        sa.Column('aec_students', sa.BigInteger(), nullable=True),
        sa.Column('agriculture_vet_students', sa.BigInteger(), nullable=True),
        sa.Column('med_students', sa.BigInteger(), nullable=True),
        sa.Column('services_students', sa.BigInteger(), nullable=True),
        sa.Column('women_share', sa.Float(), nullable=True),
        sa.Column('foreign_share', sa.Float(), nullable=True),
        sa.Column('mobile_share', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['eurostat_code'], ['cities.eurostat_code'], ),
        sa.PrimaryKeyConstraint('erasmus_code')
    )
    
    # Copy data from old tables to new ones
    op.execute('INSERT INTO cities_new SELECT * FROM cities')
    op.execute('INSERT INTO climate_new SELECT * FROM climate')
    op.execute('INSERT INTO cost_of_living_new SELECT * FROM cost_of_living')
    op.execute('INSERT INTO guides_new SELECT * FROM guides')
    op.execute('INSERT INTO housing_new SELECT * FROM housing')
    op.execute('INSERT INTO metrics_new SELECT * FROM metrics')
    op.execute('INSERT INTO universities_new SELECT * FROM universities')
    
    # Drop old tables
    op.drop_table('universities')
    op.drop_table('metrics')
    op.drop_table('housing')
    op.drop_table('guides')
    op.drop_table('cost_of_living')
    op.drop_table('climate')
    op.drop_table('cities')
    
    # Rename new tables to original names
    op.rename_table('cities_new', 'cities')
    op.rename_table('climate_new', 'climate')
    op.rename_table('cost_of_living_new', 'cost_of_living')
    op.rename_table('guides_new', 'guides')
    op.rename_table('housing_new', 'housing')
    op.rename_table('metrics_new', 'metrics')
    op.rename_table('universities_new', 'universities')
    
    # Create the transport_budget table
    op.create_table('transport_budget',
        sa.Column('eurostat_code', sa.String(length=50), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('source_date', sa.Date(), nullable=True),
        sa.Column('monthly_ticket', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.Date(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['eurostat_code'], ['cities.eurostat_code'], ),
        sa.PrimaryKeyConstraint('eurostat_code')
    )
    
    # Create indexes
    op.create_index(op.f('ix_transport_budget_eurostat_code'), 'transport_budget', ['eurostat_code'], unique=False)
    op.create_index(op.f('ix_cities_english_country'), 'cities', ['english_country'], unique=False)
    op.create_index(op.f('ix_cities_english_name'), 'cities', ['english_name'], unique=False)
    op.create_index(op.f('ix_cities_local_name'), 'cities', ['local_name'], unique=False)
    op.create_index('idx_university_city_id', 'universities', ['eurostat_code'], unique=False)
    op.create_index(op.f('ix_universities_english_name'), 'universities', ['english_name'], unique=False)
    op.create_index(op.f('ix_universities_eurostat_code'), 'universities', ['eurostat_code'], unique=False)
    op.create_index(op.f('ix_universities_name'), 'universities', ['name'], unique=False)
    

def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_universities_name'), table_name='universities')
    op.drop_index(op.f('ix_universities_eurostat_code'), table_name='universities')
    op.drop_index(op.f('ix_universities_english_name'), table_name='universities')
    op.drop_index('idx_university_city_id', table_name='universities')
    op.drop_index(op.f('ix_cities_local_name'), table_name='cities')
    op.drop_index(op.f('ix_cities_english_name'), table_name='cities')
    op.drop_index(op.f('ix_cities_english_country'), table_name='cities')
    op.drop_index(op.f('ix_transport_budget_eurostat_code'), table_name='transport_budget')

    # Drop the transport_budget table
    op.drop_table('transport_budget')

    # Recreate the original tables
    op.create_table('cities_old',
        sa.Column('eurostat_code', sa.TEXT(), nullable=True),
        sa.Column('local_name', sa.TEXT(), nullable=False),
        sa.Column('english_name', sa.TEXT(), nullable=False),
        sa.Column('local_country', sa.TEXT(), nullable=True),
        sa.Column('english_country', sa.TEXT(), nullable=True),
        sa.Column('country_emoji', sa.TEXT(), nullable=True),
        sa.Column('population', sa.INTEGER(), nullable=True),
        sa.Column('erasmus_population', sa.INTEGER(), nullable=True),
        sa.Column('lat', sa.REAL(), nullable=True),
        sa.Column('lon', sa.REAL(), nullable=True),
        sa.Column('last_updated', sa.DATE(), nullable=True),
        sa.PrimaryKeyConstraint('eurostat_code')
    )

    # Repeat for other tables (climate, cost_of_living, guides, housing, metrics, universities)
    # Example for climate:
    op.create_table('climate_old',
        sa.Column('eurostat_code', sa.TEXT(), nullable=True),
        sa.Column('mean_jan_min', sa.INTEGER(), nullable=True),
        # ... (other columns)
        sa.Column('last_updated', sa.DATE(), nullable=True),
        sa.ForeignKeyConstraint(['eurostat_code'], ['cities.eurostat_code'], ),
        sa.PrimaryKeyConstraint('eurostat_code')
    )

    # Copy data from new tables to old ones
    op.execute('INSERT INTO cities_old SELECT * FROM cities')
    op.execute('INSERT INTO climate_old SELECT * FROM climate')
    # ... (repeat for other tables)

    # Drop new tables
    op.drop_table('universities')
    op.drop_table('metrics')
    op.drop_table('housing')
    op.drop_table('guides')
    op.drop_table('cost_of_living')
    op.drop_table('climate')
    op.drop_table('cities')

    # Rename old tables to original names
    op.rename_table('cities_old', 'cities')
    op.rename_table('climate_old', 'climate')
    # ... (repeat for other tables)