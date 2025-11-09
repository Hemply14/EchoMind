# app/core/auto_learner.py
import schedule
import time
import threading
from typing import List, Dict, Set, Tuple
import logging
from datetime import datetime, timedelta, timezone
import json
import os
import re

logger = logging.getLogger(__name__)

class AutoLearner:
    def __init__(self, ai_engine):
        self.ai_engine = ai_engine
        self.learning_topics: Set[Tuple[str, int]] = set()  # (topic, interval_hours)
        self.is_running = False
        self.learning_thread = None
        self.last_research_time = {}
        self.learning_stats = {
            "total_topics_learned": 0,
            "last_learning_session": None,
            "topics_learned": [],
            "discovered_topics": []
        }
        
        # Dynamic learning settings
        self.max_discovered_topics = 100
        self.min_topic_mentions = 2
        self.topic_mention_count = {}
        
        # Create data directory for persistence
        self.data_dir = os.path.join(os.path.dirname(__file__), "../../data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.stats_file = os.path.join(self.data_dir, "learning_stats.json")
        
        # Load previous stats
        self._load_stats()
        
    def _load_stats(self):
        """Load learning statistics from file"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    self.learning_stats = data
                    # Restore discovered topics
                    for topic_data in data.get("discovered_topics", []):
                        topic = topic_data["topic"]
                        count = topic_data["mention_count"]
                        self.topic_mention_count[topic] = count
                logger.info("📊 Loaded previous learning statistics")
        except Exception as e:
            logger.warning(f"Could not load learning stats: {e}")
            
    def _save_stats(self):
        """Save learning statistics to file"""
        try:
            # Update discovered topics in stats
            self.learning_stats["discovered_topics"] = [
                {"topic": topic, "mention_count": count}
                for topic, count in self.topic_mention_count.items()
            ]
            
            with open(self.stats_file, 'w') as f:
                json.dump(self.learning_stats, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save learning stats: {e}")
    
    def add_learning_topic(self, topic: str, research_interval_hours: int = 24):
        """Add a topic for continuous learning"""
        # Clean and normalize the topic
        clean_topic = self._clean_topic(topic)
        if not clean_topic or len(clean_topic) < 3:
            return False
            
        self.learning_topics.add((clean_topic, research_interval_hours))
        self.last_research_time[clean_topic] = datetime.now(timezone.utc) - timedelta(hours=research_interval_hours + 1)
        logger.info(f"📚 Added auto-learning topic: {clean_topic} (every {research_interval_hours}h)")
        return True
        
    def remove_learning_topic(self, topic: str):
        """Remove a topic from auto-learning"""
        self.learning_topics = {(t, i) for t, i in self.learning_topics if t != topic}
        if topic in self.last_research_time:
            del self.last_research_time[topic]
        logger.info(f"🗑️ Removed auto-learning topic: {topic}")
        
    def get_learning_topics(self) -> List[Dict]:
        """Get list of current learning topics"""
        return [{"topic": topic, "interval_hours": interval, 
                "last_researched": self.last_research_time.get(topic, "Never"),
                "discovered": topic in self.topic_mention_count}
                for topic, interval in self.learning_topics]
    
    def start_continuous_learning(self):
        """Start the continuous learning background thread"""
        if self.is_running:
            logger.warning("Auto-learning already running")
            return False
            
        self.is_running = True
        self.learning_thread = threading.Thread(target=self._learning_loop, daemon=True)
        self.learning_thread.start()
        logger.info("🚀 Started continuous auto-learning")
        return True
        
    def stop_continuous_learning(self):
        """Stop continuous learning"""
        self.is_running = False
        if self.learning_thread:
            self.learning_thread.join(timeout=5)
        logger.info("🛑 Stopped continuous auto-learning")
        self._save_stats()
        
    def _learning_loop(self):
        """Main learning loop that runs in background"""
        logger.info("🔄 Auto-learning loop started")
        
        while self.is_running:
            try:
                topics_researched = 0
                
                # Research predefined topics
                for topic, interval in list(self.learning_topics):
                    if not self.is_running:
                        break
                        
                    if self._should_research_topic(topic, interval):
                        logger.info(f"🔍 Auto-researching topic: {topic}")
                        result = self.ai_engine.research_topic(topic)
                        
                        if result["status"] == "success":
                            self.last_research_time[topic] = datetime.now(timezone.utc)
                            self.learning_stats["total_topics_learned"] += 1
                            self.learning_stats["last_learning_session"] = datetime.now(timezone.utc).isoformat()
                            self.learning_stats["topics_learned"].append({
                                "topic": topic,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "items_learned": result["learned_items"],
                                "sources": result["sources"],
                                "type": "scheduled"
                            })
                            
                            # Keep only last 200 learning sessions
                            if len(self.learning_stats["topics_learned"]) > 200:
                                self.learning_stats["topics_learned"] = self.learning_stats["topics_learned"][-200:]
                                
                            logger.info(f"✅ Auto-learned {result['learned_items']} facts about {topic}")
                            topics_researched += 1
                        else:
                            logger.warning(f"⚠️ Auto-learning failed for {topic}: {result['message']}")
                
                # Research discovered topics that reached threshold
                self._research_discovered_topics()
                
                if topics_researched > 0:
                    self._save_stats()
                    
                # Sleep for 1 hour between checks
                for _ in range(3600):  # Check every second for shutdown
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"❌ Error in learning loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error
                
    def _research_discovered_topics(self):
        """Research topics discovered from conversations"""
        topics_to_research = []
        
        for topic, count in self.topic_mention_count.items():
            if count >= self.min_topic_mentions and topic not in [t for t, _ in self.learning_topics]:
                topics_to_research.append(topic)
        
        for topic in topics_to_research:
            if not self.is_running:
                break
                
            logger.info(f"🎯 Researching discovered topic: {topic} (mentioned {self.topic_mention_count[topic]} times)")
            result = self.ai_engine.research_topic(topic)
            
            if result["status"] == "success":
                self.learning_stats["total_topics_learned"] += 1
                self.learning_stats["last_learning_session"] = datetime.now(timezone.utc).isoformat()
                self.learning_stats["topics_learned"].append({
                    "topic": topic,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "items_learned": result["learned_items"],
                    "sources": result["sources"],
                    "type": "discovered",
                    "mention_count": self.topic_mention_count[topic]
                })
                
                # Add to regular learning schedule
                self.add_learning_topic(topic, 168)  # Weekly updates
                logger.info(f"✅ Learned and scheduled discovered topic: {topic}")
                
                # Remove from discovery tracking
                del self.topic_mention_count[topic]
                
    def _should_research_topic(self, topic: str, interval_hours: int) -> bool:
        """Check if a topic is due for research"""
        last_time = self.last_research_time.get(topic)
        if not last_time:
            return True
            
        time_since_last = datetime.now(timezone.utc) - last_time
        return time_since_last.total_seconds() >= interval_hours * 3600
    
    def discover_topic_from_conversation(self, query: str):
        """Discover new learning topics from user conversations"""
        potential_topics = self._extract_topics_from_query(query)
        
        for topic in potential_topics:
            if self._is_valid_topic(topic):
                if topic in self.topic_mention_count:
                    self.topic_mention_count[topic] += 1
                else:
                    self.topic_mention_count[topic] = 1
                    
                logger.info(f"🔍 Discovered topic: '{topic}' (mentions: {self.topic_mention_count[topic]})")
                
                # If reached threshold, research immediately
                if self.topic_mention_count[topic] >= self.min_topic_mentions:
                    logger.info(f"🚨 Topic '{topic}' reached threshold! Scheduling research...")
        
        self._save_stats()
    
    def _extract_topics_from_query(self, query: str) -> List[str]:
        """Extract potential topics from user query"""
        topics = []
        
        # Remove common question words and phrases
        question_patterns = [
            r'what is (.+?)\??$', r'what are (.+?)\??$', r'explain (.+?)\??$',
            r'tell me about (.+?)\??$', r'how does (.+?) work\??$', 
            r'what do you know about (.+?)\??$', r'information about (.+?)\??$',
            r'define (.+?)\??$', r'can you explain (.+?)\??$',
            r'teach me (.+?)\??$', r'learn about (.+?)\??$'
        ]
        
        for pattern in question_patterns:
            matches = re.findall(pattern, query.lower())
            for match in matches:
                if match:
                    topics.append(match.strip())
        
        # Also look for standalone nouns/noun phrases (simple approach)
        words = query.lower().split()
        if len(words) >= 2 and len(words) <= 6:
            # If it's a short phrase that's not a complete sentence
            if not any(word in words for word in ['you', 'your', 'i', 'my', 'me']):
                potential_topic = ' '.join(words)
                if len(potential_topic) > 5 and not potential_topic.endswith('?'):
                    topics.append(potential_topic)
        
        return list(set(topics))  # Remove duplicates
    
    def _is_valid_topic(self, topic: str) -> bool:
        """Check if a topic is valid for learning"""
        if len(topic) < 3 or len(topic) > 60:
            return False
            
        # Skip personal topics
        personal_keywords = ['you', 'your', 'i', 'my', 'me', 'we', 'us', 'yourself', 'myself']
        if any(word in topic.lower().split() for word in personal_keywords):
            return False
            
        # Skip common small words
        small_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        if all(word in small_words for word in topic.lower().split()):
            return False
            
        return True
    
    def _clean_topic(self, topic: str) -> str:
        """Clean and normalize a topic"""
        # Remove question marks and extra whitespace
        cleaned = topic.strip().rstrip('?')
        # Capitalize first letter
        return cleaned[0].upper() + cleaned[1:] if cleaned else ""
    
    # ===== MASSIVE KNOWLEDGE BASE =====
    
    def learn_programming_development(self):
        """Learn programming languages and development topics"""
        programming_topics = [
            # Programming Languages
            "Python programming language", "Java programming", "JavaScript programming", 
            "TypeScript programming", "C programming language", "C++ programming", 
            "Golang programming", "Rust programming language", "HTML web development",
            "CSS styling", "React framework", "Vue.js framework", "Angular framework",
            "Svelte framework", "Node.js runtime", "Express.js framework", "FastAPI framework",
            "Django framework", "Flask framework", "MongoDB database", "PostgreSQL database",
            "MySQL database", "SQLite database", "Supabase platform", "Firebase platform",
            "Redis caching", "GraphQL API", "REST APIs", "Git version control", "GitHub platform",
            "Docker containerization", "Kubernetes orchestration", "Linux operating system",
            "Bash scripting", "Data Structures", "Algorithms", "Machine Learning",
            "Deep Learning", "Natural Language Processing NLP", "AI Ethics", "Generative AI"
        ]
        
        for topic in programming_topics:
            self.add_learning_topic(topic, 336)  # Bi-weekly updates
        logger.info(f"💻 Added {len(programming_topics)} programming topics")
    
    def learn_pop_culture_entertainment(self):
        """Learn pop culture and entertainment topics"""
        pop_culture_topics = [
            # TV Series
            "DARK TV series", "Breaking Bad TV series", "Stranger Things TV series",
            "Game of Thrones TV series", "Rick and Morty TV series", "The Mandalorian TV series",
            "Marvel Cinematic Universe MCU", "DC Universe", "One Piece anime",
            "Naruto anime", "Attack on Titan anime", "Death Note anime",
            "Fullmetal Alchemist anime", "Cyberpunk 2077 game", "The Witcher series",
            "Harry Potter series", "Lord of the Rings", "Star Wars saga",
            "Avatar: The Last Airbender", "The Legend of Korra", "Black Mirror series",
            "Westworld TV series", "Money Heist TV series", "Sherlock Holmes",
            "Friends TV show", "The Office US TV show", "How I Met Your Mother TV show",
            "Stranger Things 1980s references", "Anime OVAs and Movies", "Studio Ghibli movies"
        ]
        
        for topic in pop_culture_topics:
            self.add_learning_topic(topic, 168)  # Weekly updates
        logger.info(f"🎬 Added {len(pop_culture_topics)} pop culture topics")
    
    def learn_science_math(self):
        """Learn science and mathematics topics"""
        science_topics = [
            # Physics
            "Quantum Mechanics", "Special Relativity", "General Relativity", 
            "Astrophysics", "Black Holes", "Dark Matter", "Particle Physics",
            "Thermodynamics", "Optics and Light", "Electromagnetism", 
            "Classical Mechanics", "Quantum Computing",
            
            # Mathematics
            "Linear Algebra", "Calculus", "Probability and Statistics", 
            "Differential Equations", "Discrete Mathematics", "Number Theory",
            "Chaos Theory",
            
            # Chemistry
            "Organic Chemistry", "Inorganic Chemistry", "Physical Chemistry", 
            "Biochemistry",
            
            # Biology & Life Sciences
            "Molecular Biology", "Genetics", "Human Anatomy", "Physiology",
            "Neuroscience", "Brain-Computer Interfaces", "Cognitive Science",
            "Psychology basics", "AI and Neuroscience", "Evolutionary Biology",
            "Ecology and Environment",
            
            # Space & Exploration
            "Space Exploration", "NASA missions", "Mars Colonization", 
            "SpaceX projects", "Climate Change"
        ]
        
        for topic in science_topics:
            self.add_learning_topic(topic, 336)  # Bi-weekly updates
        logger.info(f"🔬 Added {len(science_topics)} science and math topics")
    
    def learn_lifestyle_self_improvement(self):
        """Learn lifestyle and self-improvement topics"""
        lifestyle_topics = [
            # Fitness & Health
            "Boxing workouts", "Strength training", "Cardio routines", 
            "Diet and Nutrition", "Intermittent Fasting", "Meditation and Mindfulness",
            "Sleep optimization", "Mental health awareness", "Stress management",
            
            # Productivity & Learning
            "Study Techniques", "Productivity hacks", "Pomodoro technique", 
            "Time Management", "Journaling", "Goal Setting", "Morning routines",
            "Evening routines", "Learning new languages", "Self-discipline hacks",
            "Motivation and Mindset",
            
            # Finance & Career
            "Personal Finance basics", "Investing and Stocks", "Cryptocurrency basics",
            "Budgeting apps", "Career planning", "Resume building", 
            "Networking and LinkedIn tips", "Public Speaking",
            
            # Miscellaneous
            "DIY projects", "Travel hacks"
        ]
        
        for topic in lifestyle_topics:
            self.add_learning_topic(topic, 168)  # Weekly updates
        logger.info(f"🌟 Added {len(lifestyle_topics)} lifestyle topics")
    
    def learn_random_fun_miscellaneous(self):
        """Learn random, fun, and miscellaneous topics"""
        random_topics = [
            # Mysteries & Theories
            "Urban Legends", "Conspiracy Theories", 
            "Mythology Greek Norse Egyptian Hittite", "Ancient Civilizations",
            
            # Games & Puzzles
            "Cryptography", "Puzzle games", "Escape Rooms", "Chess strategies",
            "Go board game strategies", "Dystopian Novels", "Gaming culture",
            "eSports", "Indie games", "Board game design", "Card games",
            "Role-playing games RPGs", "Magic: The Gathering", "Trading Card Games",
            
            # Technology & Future
            "Futurism and Technology Trends", "Cybersecurity basics", 
            "Hacking techniques ethical", "Space Colonization theories",
            "AI in movies", "Robotics basics", "Virtual Reality VR", 
            "Augmented Reality AR", "Mixed Reality MR", "3D Printing",
            "DIY electronics", "Arduino projects", "Raspberry Pi projects",
            "Internet of Things IoT", "Smart home tech", "Wearable tech",
            "Futuristic cars", "Electric vehicles", "Solar energy tech",
            "Renewable energy trends", "Space telescopes", "Quantum internet",
            
            # Culture & Art
            "Cyberpunk culture", "Dystopian art", "Hacker culture", 
            "Coding memes", "Anime music videos AMVs", "Digital art",
            "NFTs basics", "Virtual communities", "Metaverse projects",
            "Cryptocurrency trends", "Historical inventions", 
            "Scientific discoveries", "Legendary programmers",
            "Famous AI researchers", "Futuristic architecture",
            
            # Lifestyle
            "Minimalism lifestyle", "Tiny houses", "Urban exploration",
            "Extreme sports"
        ]
        
        for topic in random_topics:
            self.add_learning_topic(topic, 336)  # Bi-weekly updates
        logger.info(f"🎲 Added {len(random_topics)} random/fun topics")
            
    def learn_common_knowledge_base(self):
        """Learn fundamental knowledge automatically"""
        # Using the new categorized methods instead
        pass
            
    def learn_current_events(self):
        """Learn about current events and trends"""
        current_topics = [
            "latest AI developments 2024",
            "new programming languages trends",
            "technology trends 2024",
            "scientific discoveries 2024",
            "space exploration news",
            "renewable energy advances",
            "medical breakthroughs 2024"
        ]
        
        for topic in current_topics:
            self.add_learning_topic(topic, 24)  # Daily updates
        logger.info(f"📰 Added {len(current_topics)} current event topics")
        
    def learn_programming_skills(self):
        """Learn about programming languages and frameworks"""
        # Using the comprehensive programming method instead
        pass
        
    def learn_comprehensive_knowledge(self):
        """Learn ALL knowledge categories"""
        logger.info("🧠 Loading comprehensive knowledge base...")
        
        self.learn_programming_development()
        self.learn_pop_culture_entertainment() 
        self.learn_science_math()
        self.learn_lifestyle_self_improvement()
        self.learn_random_fun_miscellaneous()
        self.learn_current_events()
        
        total_topics = (40 + 30 + 40 + 30 + 60 + 7)  # Your specified counts
        logger.info(f"🎯 Loaded {total_topics} topics across all categories!")
        
    def get_learning_stats(self) -> Dict:
        """Get learning statistics"""
        active_topics = len(self.learning_topics)
        recent_learnings = self.learning_stats.get("topics_learned", [])[-15:]  # Last 15
        discovered_topics = [
            {"topic": topic, "mention_count": count}
            for topic, count in list(self.topic_mention_count.items())[:15]  # Top 15
        ]
        
        # Categorize topics for better stats
        categories = {
            "programming": len([t for t, _ in self.learning_topics if any(keyword in t.lower() for keyword in ['programming', 'code', 'developer', 'framework', 'database'])]),
            "pop_culture": len([t for t, _ in self.learning_topics if any(keyword in t.lower() for keyword in ['tv', 'movie', 'anime', 'series', 'game'])]),
            "science": len([t for t, _ in self.learning_topics if any(keyword in t.lower() for keyword in ['science', 'physics', 'chemistry', 'biology', 'math'])]),
            "lifestyle": len([t for t, _ in self.learning_topics if any(keyword in t.lower() for keyword in ['fitness', 'health', 'productivity', 'finance', 'self-improvement'])]),
            "random": len([t for t, _ in self.learning_topics if any(keyword in t.lower() for keyword in ['game', 'culture', 'technology', 'future', 'art'])]),
            "current_events": len([t for t, _ in self.learning_topics if '2024' in t or 'trend' in t.lower()])
        }
        
        return {
            "auto_learning_enabled": self.is_running,
            "active_topics": active_topics,
            "total_topics_learned": self.learning_stats.get("total_topics_learned", 0),
            "last_learning_session": self.learning_stats.get("last_learning_session"),
            "recent_learnings": recent_learnings,
            "discovered_topics": discovered_topics,
            "learning_topics": self.get_learning_topics(),
            "discovery_stats": {
                "total_discovered": len(self.topic_mention_count),
                "min_mentions_threshold": self.min_topic_mentions,
                "max_discovered_topics": self.max_discovered_topics
            },
            "knowledge_categories": categories
        }
        
    def research_topic_now(self, topic: str) -> Dict:
        """Research a topic immediately (manual trigger)"""
        logger.info(f"🎯 Immediate research triggered for: {topic}")
        result = self.ai_engine.research_topic(topic)
        
        if result["status"] == "success":
            self.learning_stats["total_topics_learned"] += 1
            self.learning_stats["last_learning_session"] = datetime.now(timezone.utc).isoformat()
            self.learning_stats["topics_learned"].append({
                "topic": topic,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "items_learned": result["learned_items"],
                "sources": result["sources"],
                "type": "manual"
            })
            self._save_stats()
            
        return result