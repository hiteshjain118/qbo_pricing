#!/usr/bin/env python3
"""
Database models and configuration for Vercel Postgres
"""

import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
if os.getenv("VERCEL") is None:
    load_dotenv()

# Setup logging
from logging_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

Base = declarative_base()

class QBOCompany(Base):
    """Model for storing QuickBooks company tokens"""
    __tablename__ = 'qbo_companies'
    
    id = Column(Integer, primary_key=True)
    realm_id = Column(String(50), unique=True, nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    token_type = Column(String(20), nullable=False)
    expires_in = Column(Integer, nullable=False)
    refresh_token_expires_in = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f"<QBOCompany(realm_id='{self.realm_id}')>"

class QBOJob(Base):
    """Model for storing scheduled jobs"""
    __tablename__ = 'qbo_jobs'
    
    id = Column(Integer, primary_key=True)
    realm_id = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    schedule_time = Column(String(20), nullable=False)
    next_run = Column(DateTime, nullable=True)
    last_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<QBOJob(realm_id='{self.realm_id}', email='{self.email}')>"

def get_database_url():
    """Get database URL from environment variables"""
    # Prisma Postgres environment variables
    database_url = os.getenv('DATABASE_URL')
    postgres_url = os.getenv('POSTGRES_URL')
    prisma_database_url = os.getenv('PRISMA_DATABASE_URL')
    
    # Priority: DATABASE_URL > POSTGRES_URL > PRISMA_DATABASE_URL
    if database_url:
        logger.info("Using DATABASE_URL for database connection")
        # Convert postgres:// to postgresql:// for SQLAlchemy
        return database_url.replace('postgres://', 'postgresql://')
    elif postgres_url:
        logger.info("Using POSTGRES_URL for database connection")
        # Convert postgres:// to postgresql:// for SQLAlchemy
        return postgres_url.replace('postgres://', 'postgresql://')
    elif prisma_database_url:
        logger.info("Using PRISMA_DATABASE_URL for database connection")
        return prisma_database_url
    else:
        # Fallback to SQLite for local development
        logger.warning("No Postgres environment variables found, using SQLite for local development")
        return "sqlite:///qbo_local.db"

def create_engine_and_session():
    """Create database engine and session"""
    database_url = get_database_url()
    logger.info(f"Connecting to database: {database_url.split('@')[0]}@***")
    
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal

def init_database():
    """Initialize database tables"""
    engine, _ = create_engine_and_session()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

def get_db_session():
    """Get database session"""
    _, SessionLocal = create_engine_and_session()
    return SessionLocal() 