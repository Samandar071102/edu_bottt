import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./education_bot.db")
    
    # AI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # openai, local, etc.
    
    # File handling
    MAX_FILE_SIZE_MB = 50
    ALLOWED_EXTENSIONS = {
        'pdf', 'docx', 'pptx', 'txt', 
        'jpg', 'jpeg', 'png', 'gif',
        'mp3', 'mp4', 'm4a'
    }
    
    # Bot settings
    SUPPORTED_LANGUAGES = ['uz', 'en']
    DEFAULT_LANGUAGE = 'uz'
    
    # Scheduler
    CHECK_REMINDERS_INTERVAL = 60  # seconds
    
    # Security
    SALT_ROUNDS = 12