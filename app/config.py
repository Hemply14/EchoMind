# app/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.data_dir = Path(os.getenv("DATA_DIR", "./data"))
        self.model_cache_dir = self.data_dir / "models"
        
        # Supabase configuration
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        # Model settings
        self.embedding_model = "all-MiniLM-L6-v2"
        self.similarity_threshold = 0.7
        self.max_memories = 10000
        
        # Create directories
        self.data_dir.mkdir(exist_ok=True)
        self.model_cache_dir.mkdir(exist_ok=True)
        
        # Validate Supabase config
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and Key must be set in environment variables")

settings = Settings()