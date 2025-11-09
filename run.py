# run.py
import uvicorn
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url:
        logger.error("SUPABASE_URL environment variable is not set")
        return False
    
    if not supabase_key:
        logger.error("SUPABASE_KEY environment variable is not set")
        return False
    
    logger.info("Environment variables check passed")
    return True

def main():
    """Main function to run the FastAPI server"""
    print("🚀 Starting Privacy-First AI Server...")
    
    # Check environment first
    if not check_environment():
        print("\n❌ Missing required environment variables!")
        print("Please set these environment variables:")
        print("  SUPABASE_URL=your_supabase_project_url")
        print("  SUPABASE_KEY=your_supabase_anon_key")
        print("\nYou can set them in a .env file or directly in your terminal:")
        print("Windows (PowerShell):")
        print('  $env:SUPABASE_URL = "your_url"')
        print('  $env:SUPABASE_KEY = "your_key"')
        print("\nLinux/Mac:")
        print('  export SUPABASE_URL="your_url"')
        print('  export SUPABASE_KEY="your_key"')
        return
    
    print("✅ Environment check passed")
    print("📦 Loading AI models and initializing server...")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API documentation: http://localhost:8000/docs")
    print("⏹️  Press Ctrl+C to stop the server\n")
    
    try:
        # Start the FastAPI server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",      # Allow connections from any IP
            port=8000,           # Port to run on
            reload=True,         # Auto-reload on code changes (development)
            log_level="info",    # Logging level
            access_log=True      # Enable access logs
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("Please check:")
        print("1. Are all dependencies installed?")
        print("2. Is port 8000 available?")
        print("3. Are Supabase credentials correct?")

if __name__ == "__main__":
    main()