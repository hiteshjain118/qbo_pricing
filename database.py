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

SANDBOX_TABLE_SUFFIX = '_sandbox'
PROD_TABLE_SUFFIX = '_production'

def is_prod_environment():
    """Get current environment (sandbox or production)"""
    return os.getenv('VERCEL') != None

def get_table_name(base_name):
    """Get table name based on environment"""
    if is_prod_environment():
        return f"{base_name}{PROD_TABLE_SUFFIX}"
    else:
        return f"{base_name}{SANDBOX_TABLE_SUFFIX}"

class QBOCompany(Base):
    """Model for storing QuickBooks company tokens"""
    __tablename__ = get_table_name('qbo_companies')
    
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
    __tablename__ = get_table_name('qbo_jobs')
    
    id = Column(Integer, primary_key=True)
    realm_id = Column(String(50), nullable=False)
    email = Column(String(1000), nullable=False)  # Comma-separated list of email addresses
    # user local time
    # schedule_time = Column(DateTime, nullable=False)
    daily_schedule_time = Column(String(100), nullable=True)
    user_timezone = Column(String(100), nullable=True)
    
    # system time (UTC)
    # next_run = Column(DateTime, nullable=True)
    last_run_ts = Column(Integer, nullable=True)
    # last_run = Column(DateTime, nullable=True)
    created_at_ts = Column(Integer, nullable=True)
    # created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<QBOJob(realm_id='{self.realm_id}', email='{self.email}')>"


class DBInstance:
    def __init__(self):
        self.engine = create_engine(
            self.get_database_url(),
            # Configure connection pooling
            pool_pre_ping=True,
            pool_recycle=300,
            # Disable echo for production
            echo=False
        )
        Base.metadata.create_all(bind=self.engine)
        self.session_maker = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.engine,
            # Disable lazy loading
            expire_on_commit=False
        )
        logger.info(
            "DB initalized and tables created successfully. DB URL: %s, table_names: %s", 
            self.get_database_url(), 
            [table.name for table in Base.metadata.tables.values()]
        )

    def get_session(self):
        return self.session_maker() 

    def get_database_url(self):
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

class DB:
    INSTANCE = None

    @staticmethod
    def initialize():
        if DB.INSTANCE is None:
            DB.INSTANCE = DBInstance()

    @staticmethod
    def get_session():
        if DB.INSTANCE is None:
            DB.initialize()
        return DB.INSTANCE.get_session()
    
    @staticmethod
    def get_company_model():
        """Get the appropriate company model based on environment"""
        if DB.INSTANCE is None:
            DB.initialize()
        return QBOCompany
        
    @staticmethod
    def get_job_model():
        """Get the appropriate job model based on environment"""
        if DB.INSTANCE is None:
            DB.initialize()
        return QBOJob
    
