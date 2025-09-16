import os
from typing import Optional
from pydantic import BaseSettings
import logging

class Settings(BaseSettings):
    """
    Application configuration settings
    """
    
    # Application Settings
    app_name: str = "Legal Document Analyzer"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Security Settings
    secret_key: str = "your-super-secret-key-here-change-in-production"
    access_token_expire_minutes: int = 30
    
    # File Upload Settings
    max_file_size_mb: int = 50
    allowed_file_extensions: list = [".pdf", ".docx", ".doc"]
    upload_directory: str = "uploads"
    temp_directory: str = "temp"
    
    # AI API Settings
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_model: str = "gemini-pro"
    openai_model: str = "gpt-3.5-turbo"
    
    # Google Cloud Settings (for Document AI)
    google_cloud_project: Optional[str] = None
    google_cloud_location: str = "us"
    google_application_credentials: Optional[str] = None
    
    # Database Settings (for production)
    database_url: Optional[str] = None
    database_echo: bool = False
    
    # Redis Settings (for caching)
    redis_url: Optional[str] = None
    
    # Logging Settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CORS Settings
    cors_origins: list = ["*"]  # In production, specify your frontend domain
    cors_methods: list = ["GET", "POST", "PUT", "DELETE"]
    cors_headers: list = ["*"]
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour in seconds
    
    # Document Processing Settings
    max_clauses_per_document: int = 50
    max_text_length: int = 1000000  # 1MB of text
    text_chunk_size: int = 4000
    text_overlap: int = 200
    
    # Risk Analysis Settings
    default_risk_threshold: float = 7.0
    risk_categories: list = [
        "liability", "termination", "payment", "confidentiality",
        "intellectual_property", "dispute_resolution"
    ]
    
    # Notification Settings (for future use)
    email_enabled: bool = False
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format=self.log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("app.log")
            ]
        )

    def create_directories(self):
        """Create necessary directories"""
        os.makedirs(self.upload_directory, exist_ok=True)
        os.makedirs(self.temp_directory, exist_ok=True)
        os.makedirs("logs", exist_ok=True)

    def validate_api_keys(self) -> dict:
        """Validate API keys and return available services"""
        available_services = {
            'openai': bool(self.openai_api_key),
            'google': bool(self.google_api_key),
            'anthropic': bool(self.anthropic_api_key)
        }
        
        if not any(available_services.values()):
            logging.warning("No AI API keys configured. Using fallback analysis methods.")
        
        return available_services

    @property
    def file_size_limit_bytes(self) -> int:
        """Convert MB to bytes"""
        return self.max_file_size_mb * 1024 * 1024

# Create global settings instance
settings = Settings()

# Environment-specific configurations
class DevelopmentConfig(Settings):
    debug: bool = True
    reload: bool = True
    log_level: str = "DEBUG"

class ProductionConfig(Settings):
    debug: bool = False
    reload: bool = False
    log_level: str = "WARNING"
    cors_origins: list = ["https://yourdomain.com"]  # Replace with your domain

class TestingConfig(Settings):
    debug: bool = True
    database_url: str = "sqlite:///test.db"
    log_level: str = "DEBUG"

# Configuration factory
def get_config() -> Settings:
    """Get configuration based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()

# API Configuration for different providers
class AIProviderConfig:
    """Configuration for different AI providers"""
    
    OPENAI_CONFIG = {
        'max_tokens': 4000,
        'temperature': 0.1,
        'models': {
            'analysis': 'gpt-3.5-turbo',
            'summarization': 'gpt-3.5-turbo',
            'qa': 'gpt-3.5-turbo'
        }
    }
    
    GOOGLE_CONFIG = {
        'max_tokens': 4000,
        'temperature': 0.1,
        'models': {
            'analysis': 'gemini-pro',
            'summarization': 'gemini-pro',
            'qa': 'gemini-pro'
        }
    }
    
    ANTHROPIC_CONFIG = {
        'max_tokens': 4000,
        'temperature': 0.1,
        'models': {
            'analysis': 'claude-3-sonnet-20240229',
            'summarization': 'claude-3-sonnet-20240229',
            'qa': 'claude-3-sonnet-20240229'
        }
    }

# Document type configurations
DOCUMENT_TYPE_CONFIG = {
    'service_agreement': {
        'key_clauses': ['payment', 'termination', 'liability', 'scope_of_work'],
        'risk_factors': ['unlimited_liability', 'immediate_termination'],
        'typical_duration': 'variable'
    },
    'employment_agreement': {
        'key_clauses': ['compensation', 'termination', 'confidentiality', 'non_compete'],
        'risk_factors': ['non_compete_clause', 'broad_confidentiality'],
        'typical_duration': 'indefinite'
    },
    'lease_agreement': {
        'key_clauses': ['rent', 'security_deposit', 'maintenance', 'termination'],
        'risk_factors': ['personal_guarantee', 'unlimited_damages'],
        'typical_duration': 'fixed_term'
    },
    'nda': {
        'key_clauses': ['confidentiality', 'term', 'exceptions', 'return_of_information'],
        'risk_factors': ['overly_broad_definition', 'long_term'],
        'typical_duration': 'fixed_term'
    }
}

# Risk assessment thresholds
RISK_THRESHOLDS = {
    'low': {'min': 1, 'max': 3, 'color': '#10B981', 'description': 'Generally safe terms'},
    'medium': {'min': 4, 'max': 6, 'color': '#F59E0B', 'description': 'Standard terms with some considerations'},
    'high': {'min': 7, 'max': 10, 'color': '#EF4444', 'description': 'Terms requiring careful review'}
}

# Supported jurisdictions and their requirements
JURISDICTION_REQUIREMENTS = {
    'indian': {
        'name': 'Indian Contract Act',
        'required_clauses': ['governing_law', 'dispute_resolution'],
        'restricted_terms': ['penalty_clauses', 'waiver_of_statutory_rights'],
        'compliance_checks': [
            'section_74_penalties', 'unfair_contract_terms', 'consumer_protection'
        ]
    },
    'us': {
        'name': 'United States',
        'required_clauses': ['choice_of_law', 'dispute_resolution'],
        'restricted_terms': ['unconscionable_terms', 'illegal_penalty_clauses'],
        'compliance_checks': [
            'ucc_compliance', 'consumer_protection_laws', 'employment_law'
        ]
    },
    'eu': {
        'name': 'European Union',
        'required_clauses': ['data_protection', 'consumer_rights', 'governing_law'],
        'restricted_terms': ['unfair_contract_terms', 'consumer_right_waivers'],
        'compliance_checks': [
            'gdpr_compliance', 'consumer_directive', 'unfair_terms_directive'
        ]
    },
    'uk': {
        'name': 'United Kingdom',
        'required_clauses': ['governing_law', 'dispute_resolution'],
        'restricted_terms': ['unfair_contract_terms', 'penalty_clauses'],
        'compliance_checks': [
            'unfair_contract_terms_act', 'consumer_rights_act', 'data_protection'
        ]
    }
}

# Language support configuration
LANGUAGE_CONFIG = {
    'supported_languages': ['en', 'hi', 'es', 'fr', 'de', 'zh'],
    'default_language': 'en',
    'translation_service': 'google',  # google, azure, aws
    'legal_terminology_priority': True
}

# Feature flags for advanced features
FEATURE_FLAGS = {
    'multilingual_support': False,
    'document_comparison': True,
    'jurisdiction_compliance': True,
    'ai_qa_system': True,
    'risk_timeline': False,
    'smart_bookmarking': False,
    'obligation_tracking': False,
    'notification_system': False,
    'advanced_analytics': False,
    'custom_risk_profiles': False
}