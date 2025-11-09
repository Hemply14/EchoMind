# setup.py
import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def install_requirements():
    """Install Python dependencies"""
    print("Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def download_models():
    """Download required models"""
    print("Downloading embedding model...")
    from sentence_transformers import SentenceTransformer
    from app.config import settings
    
    model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=str(settings.model_cache_dir))
    print("Models downloaded successfully!")

def check_supabase_config():
    """Check if Supabase configuration is valid"""
    from app.config import settings
    
    print("Checking Supabase configuration...")
    
    if not settings.supabase_url:
        print("❌ SUPABASE_URL not found in environment variables")
        return False
    
    if not settings.supabase_key:
        print("❌ SUPABASE_KEY not found in environment variables")
        return False
    
    print("✓ Supabase configuration found")
    return True

def test_supabase_connection():
    """Test connection to Supabase"""
    from app.core.memory_store import SupabaseMemoryStore
    
    print("Testing Supabase connection...")
    try:
        store = SupabaseMemoryStore()
        stats = store.get_stats()
        print(f"✓ Supabase connection successful")
        print(f"✓ Current stats: {stats['memory_count']} memories, {stats['rule_count']} rules")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def verify_setup():
    """Verify the complete setup"""
    from app.core.ai_engine import PrivacyFirstAI
    
    print("Verifying complete setup...")
    
    try:
        ai = PrivacyFirstAI()
        print("✓ AI engine initialized successfully")
        
        health = ai.get_health()
        print(f"✓ System health: {health}")
        
        return True
        
    except Exception as e:
        print(f"✗ Setup verification failed: {e}")
        return False

if __name__ == "__main__":
    print("Setting up Privacy-First AI Backend with Supabase...")
    
    try:
        # Check environment first
        if not check_supabase_config():
            print("\nPlease create a .env file with:")
            print("SUPABASE_URL=your_supabase_project_url")
            print("SUPABASE_KEY=your_supabase_anon_key")
            sys.exit(1)
        
        install_requirements()
        download_models()
        
        if test_supabase_connection() and verify_setup():
            print("\n🎉 Setup completed successfully!")
            print("\nTo start the server, run:")
            print("  python run.py")
            print("\nThe API will be available at: http://localhost:8000")
            print("API documentation: http://localhost:8000/docs")
        else:
            print("\n❌ Setup failed. Please check the errors above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)