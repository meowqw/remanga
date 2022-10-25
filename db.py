from sqlalchemy import create_engine, MetaData, Table, Integer, String, \
    Column, DateTime, ForeignKey, Numeric, CheckConstraint, select
from datetime import datetime
import config

metadata = MetaData()

engine = create_engine(
    f"mysql+pymysql://{config.DB_LOGIN}:{config.DB_PASS}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}?charset=utf8mb4"
)

# items model
items = Table('items', metadata, Column('id', Integer(), primary_key=True),
              Column('link', String(200), nullable=True),
              Column('ru_name', String(200), nullable=True),
              Column('en_name', String(200), nullable=True),
              Column('publisher', String(200), nullable=True),
              Column('year', Integer(), nullable=True),
              Column('status', Integer(), nullable=True),
              Column('count_chapters', Integer(), nullable=True),
              Column('age', Integer(), nullable=True),
              Column('date_first_character', DateTime(), nullable=True),
              Column('date_last_character', DateTime(), nullable=True),
              Column('created_on', DateTime(), default=datetime.now))

# create table
metadata.create_all(engine)

def get_all():
    query = select([items])
    return engine.connect().execute(query).all()


def get_item(id):
    query = select([items]).where(items.c.id == id)
    return engine.connect().execute(query).first()