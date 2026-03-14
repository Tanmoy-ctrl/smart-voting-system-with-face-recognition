# models.py
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    aadhaar = Column(String, unique=True, nullable=False)
    face_encoding = Column(LargeBinary, nullable=False)  # pickled numpy array
    has_voted = Column(Boolean, default=False)

class Candidate(Base):
    __tablename__ = 'candidates'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    party = Column(String, nullable=True)

class Vote(Base):
    __tablename__ = 'votes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User")
    candidate = relationship("Candidate")

def get_engine(path='sqlite:///voting.db'):
    return create_engine(path, connect_args={"check_same_thread": False})

def init_db(path='sqlite:///voting.db'):
    engine = get_engine(path)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    return sessionmaker(bind=engine)()
