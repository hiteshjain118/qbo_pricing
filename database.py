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

class QBOCompanySandbox(Base):
    """Model for storing QuickBooks company tokens (Sandbox)"""
    __tablename__ = 'qbo_companies_sandbox'
    
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
        return f"<QBOCompanySandbox(realm_id='{self.realm_id}')>"

class QBOCompanyProduction(Base):
    """Model for storing QuickBooks company tokens (Production)"""
    __tablename__ = 'qbo_companies_production'
    
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
        return f"<QBOCompanyProduction(realm_id='{self.realm_id}')>"

class QBOJobSandbox(Base):
    """Model for storing scheduled jobs (Sandbox)"""
    __tablename__ = 'qbo_jobs_sandbox'
    
    id = Column(Integer, primary_key=True)
    realm_id = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    schedule_time = Column(String(20), nullable=False)
    next_run = Column(DateTime, nullable=True)
    last_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<QBOJobSandbox(realm_id='{self.realm_id}', email='{self.email}')>"

class QBOJobProduction(Base):
    """Model for storing scheduled jobs (Production)"""
    __tablename__ = 'qbo_jobs_production'
    
    id = Column(Integer, primary_key=True)
    realm_id = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    schedule_time = Column(String(20), nullable=False)
    next_run = Column(DateTime, nullable=True)
    last_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<QBOJobProduction(realm_id='{self.realm_id}', email='{self.email}')>"

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

def is_prod_environment():
    """Get current environment (sandbox or production)"""
    return os.getenv('VERCEL') != None

def get_company_model():
    """Get the appropriate company model based on environment"""
    if is_prod_environment():
        return QBOCompanyProduction
    else:
        return QBOCompanySandbox

def get_job_model():
    """Get the appropriate job model based on environment"""
    if is_prod_environment():
        return QBOJobProduction
    else:
        return QBOJobSandbox 