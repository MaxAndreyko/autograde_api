from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

# User model
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(64), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

# EssayScoring Model
class EssayScoring(Base):
    __tablename__ = 'essay_scoring'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    input_task = Column(Text, nullable=False)
    input_essay = Column(Text, nullable=False)
    score_content = Column(Integer)
    score_organization = Column(Integer)
    score_grammar = Column(Integer)
    comment = Column(Text)
    submitted_at = Column(TIMESTAMP, default=datetime.utcnow)