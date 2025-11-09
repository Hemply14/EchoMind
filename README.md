# 🤖 Privacy-First AI Assistant

A fully customizable, privacy-focused AI assistant that learns from you, researches topics online, and evolves based on your interactions - **all while keeping your data encrypted and under your control**.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Supabase](https://img.shields.io/badge/Supabase-Enabled-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🌟 Key Features

### 🔒 Privacy-First Architecture
- **End-to-end encryption** for all your data
- **Local AI processing** - your conversations stay private
- **No cloud tracking** - you control where your data lives
- **Supabase backend** - secure, encrypted storage

### 🧠 Advanced AI Capabilities
- **Semantic search** with sentence transformers
- **Multiple ML models** (Linear Regression, Random Forest, XGBoost, LightGBM)
- **Context-aware conversations** - remembers your chat history
- **User profiling** - learns your interests and adapts

### 🌐 Auto-Learning System
- **200+ Topics** across 6 major categories:
  - 🖥️ Programming & Development (40 topics)
  - 🎬 Pop Culture & Entertainment (30 topics)
  - 🔬 Science & Mathematics (40 topics)
  - 💪 Lifestyle & Self-Improvement (30 topics)
  - 🎲 Random/Fun/Miscellaneous (60 topics)
  - 📰 Current Events (7 topics)
- **Dynamic topic discovery** from conversations
- **Automatic web research** for unknown queries
- **Scheduled learning** - stays updated automatically

### 🔍 Web Research Integration
- **DuckDuckGo & Google search** integration
- **Automatic knowledge extraction** from web sources
- **Real-time fact-checking** with citations
- **Smart caching** to avoid redundant searches

### 💡 Adaptive Learning
- **Feedback system** - learns from your ratings
- **Common sense reasoning** - applies contextual knowledge
- **Personalized responses** based on your interests
- **Conversation continuity** - maintains context

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Configuration](#️-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Architecture](#-architecture)
- [Data Management](#-data-management)
- [Advanced Features](#-advanced-features)
- [Contributing](#-contributing)
- [License](#-license)

## 🔧 Installation

### Prerequisites

```bash
Python 3.8 or higher
pip (Python package manager)
Supabase account (free tier works!)
```

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/privacy-ai-assistant.git
cd privacy-ai-assistant
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `fastapi` - Modern web framework
- `uvicorn` - ASGI server
- `sentence-transformers` - Semantic search
- `scikit-learn` - Machine learning
- `supabase` - Database backend
- `cryptography` - Data encryption
- `streamlit` - Web interface
- And more (see requirements.txt)

### 3. Set Up Supabase

1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to **Settings** → **API**
4. Copy your **Project URL** and **anon/public key**

### 4. Configure Environment

Create a `.env` file in the project root:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
DATA_DIR=./data
```

### 5. Set Up Database Tables

Run these SQL commands in your Supabase SQL editor:

```sql
-- Memories table
CREATE TABLE memories (
    id BIGSERIAL PRIMARY KEY,
    input_text TEXT NOT NULL,
    output_text TEXT NOT NULL,
    context TEXT,
    category VARCHAR(50) DEFAULT 'general',
    embedding JSONB,
    confidence DECIMAL(3,2) DEFAULT 1.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Rules table
CREATE TABLE rules (
    id BIGSERIAL PRIMARY KEY,
    pattern TEXT NOT NULL,
    action TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_memories_active ON memories(is_active);
CREATE INDEX idx_memories_category ON memories(category);
CREATE INDEX idx_rules_active ON rules(is_active);
CREATE INDEX idx_rules_priority ON rules(priority);
```

### 6. Run Setup Script

```bash
python setup.py
```

This will:
- ✅ Verify your Supabase connection
- ✅ Download required AI models
- ✅ Initialize the system
- ✅ Perform health checks

## 🚀 Quick Start

### Start the Backend Server

```bash
python run.py
```

The API will be available at:
- **Main API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Start the Web Interface (Optional)

In a new terminal:

```bash
streamlit run frontend.py
```

Open http://localhost:8501 in your browser

### Quick Test

```bash
# In another terminal
python train_ai.py
```

This will:
1. Add sample rules and memories
2. Test the AI with various questions
3. Show you how everything works

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Your Supabase project URL | Required |
| `SUPABASE_KEY` | Your Supabase anon key | Required |
| `DATA_DIR` | Local data directory | `./data` |

### AI Settings (in `config.py`)

```python
embedding_model = "all-MiniLM-L6-v2"  # Sentence transformer model
similarity_threshold = 0.7             # Minimum confidence for matches
max_memories = 10000                   # Maximum memories to store
```

## 📖 Usage

### 1. Teaching Your AI

#### Via API

```python
import requests

requests.post("http://localhost:8000/teach", json={
    "input_text": "How do you handle coding stress?",
    "output_text": "I take breaks, listen to music, and remember why I started coding!",
    "context": "College student struggling with deadlines",
    "category": "coding_life"
})
```

#### Via Bulk Import

```bash
python bulk_import.py
```

Edit `bulk_import.py` to add your custom data.

#### Via Web Interface

1. Enable "Teaching Mode" in sidebar
2. Fill in the teaching form
3. Click "Teach This Response"

### 2. Asking Questions

#### Via API

```python
response = requests.post("http://localhost:8000/ask", json={
    "query": "How do I handle burnout?",
    "threshold": 0.6
})
print(response.json()["response"])
```

#### With Context & Research

```python
response = requests.post("http://localhost:8000/ask-context", json={
    "query": "What is quantum computing?",
    "user_id": "my_user_id",
    "threshold": 0.6,
    "enable_research": True  # AI will search online if it doesn't know
})
```

### 3. Web Research

#### Research a Topic

```python
response = requests.post("http://localhost:8000/research", json={
    "topic": "Machine Learning basics",
    "depth": "basic"
})
```

The AI will:
1. Search online (DuckDuckGo + Google)
2. Extract key information
3. Save it to memory automatically
4. Return what it learned

### 4. Enable Auto-Learning

#### Comprehensive Knowledge (200+ topics)

```python
requests.post("http://localhost:8000/auto-learning/enable", json={
    "comprehensive_knowledge": True,
    "current_events": True
})
```

This starts background learning across all categories!

#### Add Custom Topics

```python
requests.post("http://localhost:8000/auto-learning/topics", 
    params={"topic": "Rust programming", "interval_hours": 24}
)
```

#### View Learning Stats

```python
response = requests.get("http://localhost:8000/auto-learning/stats")
print(response.json())
```

## 📚 API Documentation

### Core Endpoints

#### 🧠 AI Interaction

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ask` | POST | Ask a question |
| `/ask-context` | POST | Ask with context & optional research |
| `/teach` | POST | Teach new knowledge |
| `/rules` | POST | Add behavior rules |
| `/feedback` | POST | Submit feedback for learning |

#### 🔍 Research & Learning

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/research` | POST | Research a topic online |
| `/auto-learning/enable` | POST | Enable auto-learning |
| `/auto-learning/disable` | POST | Disable auto-learning |
| `/auto-learning/topics` | GET/POST/DELETE | Manage learning topics |
| `/auto-learning/stats` | GET | Get learning statistics |
| `/auto-learning/discovered-topics` | GET | View discovered topics |

#### 💾 Data Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/memories` | GET | List memories |
| `/memories/{id}` | DELETE | Delete a memory |
| `/force-update` | POST | Force knowledge refresh |

#### 📊 System & Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health check |
| `/performance` | GET | Performance metrics |
| `/user-profile` | GET | User profile & insights |
| `/stats` | GET | Comprehensive statistics |

### Example Requests

#### Ask with Research

```bash
curl -X POST "http://localhost:8000/ask-context" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Docker?",
    "user_id": "user123",
    "threshold": 0.6,
    "enable_research": true
  }'
```

#### Enable Comprehensive Auto-Learning

```bash
curl -X POST "http://localhost:8000/auto-learning/enable" \
  -H "Content-Type: application/json" \
  -d '{
    "comprehensive_knowledge": true,
    "current_events": true
  }'
```

#### Get Discovered Topics

```bash
curl "http://localhost:8000/auto-learning/discovered-topics"
```

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (Streamlit)                   │
│  - Chat Interface  - Teaching UI  - Analytics Dashboard │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                 FastAPI Backend (main.py)                │
│  - REST API  - Request Handling  - Response Formation   │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│           Enhanced AI Engine (enhanced_ai_engine.py)     │
│  - Context Management  - User Profiling  - Enhancement   │
└─────┬──────────────┬──────────────┬─────────────────────┘
      │              │              │
┌─────▼────┐  ┌──────▼──────┐  ┌───▼──────────┐
│ Base AI  │  │    Web      │  │ Auto-Learner │
│  Engine  │  │  Searcher   │  │   Module     │
└─────┬────┘  └──────┬──────┘  └───┬──────────┘
      │              │              │
┌─────▼──────────────▼──────────────▼─────────────────────┐
│              Supabase (Cloud Database)                   │
│  - Encrypted Memories  - Rules  - User Data              │
└──────────────────────────────────────────────────────────┘
```

### Key Classes

- **`EnhancedPrivacyAI`**: Main AI engine with all features
- **`AutoLearner`**: Background learning system
- **`WebSearcher`**: Multi-source web search
- **`AutoResearcher`**: Knowledge extraction from web
- **`SupabaseMemoryStore`**: Encrypted data persistence
- **`DataEncryptor`**: End-to-end encryption

## 💾 Data Management

### Encryption

All sensitive data is encrypted using **Fernet symmetric encryption**:

```python
from app.core.encryption import DataEncryptor

encryptor = DataEncryptor()
encrypted = encryptor.encrypt("sensitive data")
decrypted = encryptor.decrypt(encrypted)
```

Keys are stored locally in `data/encryption.key`

### Memory Categories

- `general` - General knowledge
- `coding_life` - Programming experiences
- `productivity` - Productivity tips
- `motivation` - Motivational content
- `college_life` - College experiences
- `learning` - Learning strategies
- `mental_health` - Mental health topics
- `personal_growth` - Self-improvement
- `researched_knowledge` - Web-researched facts

### Data Export

```python
# Get all memories
response = requests.get("http://localhost:8000/memories?limit=100")
memories = response.json()

# Save to file
import json
with open('my_ai_backup.json', 'w') as f:
    json.dump(memories, f, indent=2)
```

### Data Cleanup

```python
# Delete specific memory
requests.delete("http://localhost:8000/memories/123")

# Or via Supabase dashboard
# Navigate to your Supabase project → Table Editor → memories
```

## 🎯 Advanced Features

### 1. Topic Discovery

The AI automatically discovers topics from your conversations:

```python
# User asks: "What is quantum computing?"
# AI automatically tracks "quantum computing" as a potential learning topic
# After 2+ mentions, it researches the topic automatically
```

View discovered topics:
```python
response = requests.get("http://localhost:8000/auto-learning/discovered-topics")
```

### 2. User Profiling

The AI learns your interests:

```python
response = requests.get("http://localhost:8000/user-profile?user_id=my_id")
profile = response.json()

# Returns:
# {
#   "interests": ["coding", "gaming", "fitness"],
#   "topics_discussed": ["python", "react", "boxing"],
#   "conversation_count": 42,
#   "conversation_style": "friendly"
# }
```

### 3. Feedback Learning

Rate responses to improve the AI:

```python
requests.post("http://localhost:8000/feedback", json={
    "query": "How do I learn Python?",
    "response": "Start with basics, practice daily...",
    "rating": 5,  # 1-5 scale
    "comment": "Very helpful advice!"
})
```

### 4. Common Sense Reasoning

The AI applies contextual knowledge:

```python
# User: "I'm feeling stressed"
# AI: *checks common sense rules*
# AI: "Take deep breaths. Break tasks into smaller pieces..."
```

### 5. Conversation Continuity

Maintains context across messages:

```python
# User: "Tell me about Python"
# AI: "Python is a high-level programming language..."
# User: "What can I build with it?"
# AI: "Building on what we discussed... Python is great for..."
```

## 📊 Monitoring & Analytics

### System Health

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "memory_count": 150,
  "rule_count": 10,
  "model_loaded": true,
  "knowledge_base_ready": true,
  "cache_size": 150,
  "pending_updates": 0
}
```

### Performance Stats

```bash
curl http://localhost:8000/performance
```

### Comprehensive Statistics

```bash
curl http://localhost:8000/stats
```

Returns:
- System health
- User insights
- Performance metrics
- Auto-learning statistics
- Discovered topics

## 🐛 Troubleshooting

### Server Won't Start

**Problem**: `Supabase connection failed`

**Solution**:
```bash
# Check your .env file
cat .env

# Verify credentials at supabase.com
# Make sure SUPABASE_URL and SUPABASE_KEY are correct
```

### No Search Results

**Problem**: Web research returns no results

**Solution**:
```bash
# Install search dependencies
pip install duckduckgo-search google-search-python beautifulsoup4

# Check internet connection
ping google.com
```

### Low Response Confidence

**Problem**: AI always returns "I'm not sure..."

**Solution**:
1. Lower the threshold: `threshold=0.5` instead of `0.7`
2. Teach more memories: `python bulk_import.py`
3. Enable research: `enable_research=true`

### Auto-Learning Not Working

**Problem**: Background learning not happening

**Solution**:
```bash
# Check if auto-learning is enabled
curl http://localhost:8000/auto-learning/stats

# Enable it
curl -X POST http://localhost:8000/auto-learning/enable \
  -H "Content-Type: application/json" \
  -d '{"comprehensive_knowledge": true}'
```

## 🔒 Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use strong Supabase credentials**
3. **Keep encryption keys secure** (`data/encryption.key`)
4. **Regularly backup your Supabase database**
5. **Use HTTPS in production** (not HTTP)
6. **Restrict Supabase API access** to your IP if possible

## 🚀 Deployment

### Deploy Backend (Railway/Render/Heroku)

1. Add `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

2. Set environment variables on platform
3. Deploy!

### Deploy Frontend (Streamlit Cloud)

1. Push to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Add secrets (Streamlit secrets manager)

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/privacy-ai-assistant.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run tests
pytest tests/

# Format code
black app/
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.