# app/core/web_searcher.py
import requests
import json
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from googlesearch import search as google_search
import time
from typing import List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)

class WebSearcher:
    def __init__(self):
        self.search_cache = {}
        self.ddgs = DDGS()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search DuckDuckGo for information"""
        try:
            logger.info(f"🔍 Searching DuckDuckGo for: {query}")
            
            results = []
            search_results = list(self.ddgs.text(query, max_results=max_results))
            
            logger.info(f"📊 DuckDuckGo found {len(search_results)} results")
            
            for i, result in enumerate(search_results):
                if i >= max_results:
                    break
                
                # Clean up the snippet
                snippet = result.get('body', '')
                if snippet:
                    # Remove extra whitespace and truncate
                    snippet = ' '.join(snippet.split())[:250] + "..."
                
                results.append({
                    "title": result.get('title', 'No Title'),
                    "url": result.get('href', ''),
                    "snippet": snippet or "No description available",
                    "source": "duckduckgo"
                })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ DuckDuckGo search failed: {e}")
            return []
    
    def search_google(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search Google for information"""
        try:
            logger.info(f"🔍 Searching Google for: {query}")
            
            results = []
            search_results = list(google_search(query, num_results=max_results, advanced=True))
            
            logger.info(f"📊 Google found {len(search_results)} results")
            
            for i, result in enumerate(search_results):
                if i >= max_results:
                    break
                
                # For google-search package with advanced=True
                title = getattr(result, 'title', 'No Title')
                url = getattr(result, 'url', '')
                snippet = getattr(result, 'description', 'No description available')
                
                if snippet:
                    snippet = ' '.join(snippet.split())[:250] + "..."
                
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "source": "google"
                })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Google search failed: {e}")
            # Fallback to simple search if advanced fails
            try:
                logger.info("🔄 Trying simple Google search...")
                results = []
                search_results = list(google_search(query, num_results=max_results))
                
                for i, url in enumerate(search_results):
                    if i >= max_results:
                        break
                    
                    try:
                        page_content = self._get_page_content(url)
                        results.append({
                            "title": page_content.get('title', 'No Title'),
                            "url": url,
                            "snippet": page_content.get('snippet', 'No description available'),
                            "source": "google"
                        })
                    except Exception as page_error:
                        logger.warning(f"Failed to fetch {url}: {page_error}")
                        continue
                
                return results
            except Exception as fallback_error:
                logger.error(f"❌ Google fallback also failed: {fallback_error}")
                return []
    
    def _get_page_content(self, url: str, timeout: int = 8) -> Dict:
        """Extract title and meaningful content from webpage"""
        try:
            logger.debug(f"🌐 Fetching page content: {url}")
            
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get title
            title = "No Title"
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            else:
                # Try meta title or h1
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text().strip()[:100]
            
            # Get meaningful content - try multiple strategies
            snippet = ""
            
            # Strategy 1: Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                snippet = meta_desc.get('content').strip()
            
            # Strategy 2: First paragraph with substantial text
            if not snippet:
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    text = p.get_text().strip()
                    if len(text) > 50:  # Substantial paragraph
                        snippet = text
                        break
            
            # Strategy 3: Article content
            if not snippet:
                article = soup.find('article')
                if article:
                    text = article.get_text().strip()
                    if text:
                        snippet = text
            
            # Clean and truncate snippet
            if snippet:
                # Remove extra whitespace
                snippet = ' '.join(snippet.split())
                # Truncate to reasonable length
                snippet = snippet[:300] + "..." if len(snippet) > 300 else snippet
            else:
                snippet = "Content preview not available"
            
            return {
                "title": title,
                "snippet": snippet,
                "url": url
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract content from {url}: {e}")
            return {
                "title": "Failed to load page", 
                "snippet": f"Could not fetch content: {str(e)}",
                "url": url
            }
    
    def search_multiple_sources(self, query: str, max_results: int = 3) -> List[Dict]:
        """Search multiple sources and combine results"""
        logger.info(f"🎯 Starting multi-source search for: {query}")
        
        all_results = []
        
        # Try DuckDuckGo first (more reliable, no rate limits)
        try:
            ddg_results = self.search_duckduckgo(query, max_results)
            all_results.extend(ddg_results)
            logger.info(f"🦆 DuckDuckGo returned {len(ddg_results)} results")
        except Exception as e:
            logger.error(f"❌ DuckDuckGo search failed: {e}")
        
        # If not enough results, try Google
        if len(all_results) < max_results:
            try:
                google_results = self.search_google(query, max_results - len(all_results))
                all_results.extend(google_results)
                logger.info(f"🔍 Google returned {len(google_results)} results")
            except Exception as e:
                logger.error(f"❌ Google search failed: {e}")
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        logger.info(f"📦 Total unique results: {len(unique_results)}")
        return unique_results[:max_results]
    
    def extract_knowledge_from_search(self, query: str) -> List[Dict]:
        """Extract structured knowledge from search results"""
        logger.info(f"🧠 Extracting knowledge for: {query}")
        
        search_results = self.search_multiple_sources(query, max_results=3)
        
        knowledge_items = []
        for result in search_results:
            # Create knowledge item from search result
            knowledge_item = {
                "input_text": query,
                "output_text": f"According to {result['source']}: {result['snippet']}",
                "context": f"Source: {result['title']} - {result['url']}",
                "category": "web_research",
                "confidence": 0.8,
                "is_research": True
            }
            knowledge_items.append(knowledge_item)
        
        logger.info(f"📚 Extracted {len(knowledge_items)} knowledge items")
        return knowledge_items

class AutoResearcher:
    def __init__(self, memory_store, ai_engine):
        self.memory_store = memory_store
        self.ai_engine = ai_engine
        self.searcher = WebSearcher()
    
    def _generate_search_queries(self, topic: str) -> List[str]:
        """Generate multiple search queries for better results"""
        # Common variations and corrections
        variations = [
            topic,
            topic.replace("eenvironment", "environment"),  # Fix common typo
            topic.replace("programmming", "programming"),  # Fix common typo
            f"what is {topic}",
            f"explain {topic}",
            f"{topic} tutorial",
            f"{topic} basics"
        ]
        return variations

    def research_and_learn(self, topic: str, depth: str = "basic") -> Dict:
        """Research a topic and automatically learn from it"""
        logger.info(f"🔬 Starting research on topic: {topic}")
        
        try:
            # Generate multiple search queries
            search_queries = self._generate_search_queries(topic)
            all_results = []
            
            for query in search_queries[:2]:  # Try first 2 variations
                if len(all_results) >= 5:  # If we have enough results
                    break
                    
                search_results = self.searcher.search_multiple_sources(query, max_results=3)
                all_results.extend(search_results)
            
            # Remove duplicates
            seen_urls = set()
            unique_results = []
            for result in all_results:
                if result['url'] not in seen_urls:
                    seen_urls.add(result['url'])
                    unique_results.append(result)
            
            logger.info(f"📊 Research found {len(unique_results)} sources from {len(search_queries)} query variations")
            
            if not unique_results:
                return {
                    "status": "no_results", 
                    "message": f"No information found about '{topic}'. The AI will try again later.",
                    "learned_items": 0,
                    "sources": []
                }
            
            # Extract knowledge from results
            learned_count = 0
            research_errors = 0
            
            for i, result in enumerate(unique_results):
                try:
                    # Create different Q&A pairs from the search result
                    questions = [
                        f"What is {topic}?",
                        f"Tell me about {topic}",
                        f"Explain {topic}",
                        f"Information about {topic}"
                    ]
                    
                    question = questions[0]
                    answer = self._format_knowledge(result)
                    
                    logger.debug(f"📝 Learning item {i+1}: {question[:50]}...")
                    
                    # Add to memory
                    memory_id = self.memory_store.add_memory(
                        input_text=question,
                        output_text=answer,
                        context=f"Researched from web: {result['source']} - {result['url']}",
                        category="researched_knowledge",
                        embedding=None
                    )
                    
                    if memory_id:
                        learned_count += 1
                        logger.debug(f"✅ Successfully learned memory ID: {memory_id}")
                    else:
                        research_errors += 1
                        logger.warning(f"⚠️ Failed to add memory for result {i+1}")
                        
                except Exception as e:
                    research_errors += 1
                    logger.error(f"❌ Error processing search result {i+1}: {e}")
                    continue
            
            # Update AI knowledge base
            try:
                self.ai_engine.force_update()
                logger.info("🔄 Knowledge base updated with new research")
            except Exception as e:
                logger.warning(f"⚠️ Failed to force update knowledge base: {e}")
            
            # Prepare response
            if learned_count > 0:
                sources = list(set([r['source'] for r in unique_results]))
                return {
                    "status": "success",
                    "learned_items": learned_count,
                    "sources": sources,
                    "errors": research_errors,
                    "message": f"Successfully learned {learned_count} new facts about '{topic}' from {', '.join(sources)}"
                }
            else:
                return {
                    "status": "error",
                    "learned_items": 0,
                    "sources": [],
                    "errors": research_errors,
                    "message": f"Found {len(unique_results)} sources but failed to learn any information."
                }
            
        except Exception as e:
            logger.error(f"❌ Research failed completely: {e}")
            return {
                "status": "error", 
                "message": f"Research failed: {str(e)}",
                "learned_items": 0,
                "sources": [],
                "errors": 1
            }
    
    def _format_knowledge(self, search_result: Dict) -> str:
        """Format search result into readable knowledge"""
        source = search_result['source']
        title = search_result['title']
        snippet = search_result['snippet']
        url = search_result['url']
        
        # Clean up the formatting
        if snippet.endswith("..."):
            snippet = snippet[:-3]  # Remove trailing ellipsis
        
        return f"Based on research from {source}: {snippet} [Source: {title}]"
    
    def quick_search(self, query: str) -> Dict:
        """Quick search for immediate answers without saving to memory"""
        try:
            logger.info(f"⚡ Quick search for: {query}")
            
            search_results = self.searcher.search_multiple_sources(query, max_results=2)
            
            if not search_results:
                return {
                    "found": False,
                    "answer": f"No information found about '{query}'",
                    "sources": []
                }
            
            # Combine the best results
            best_result = search_results[0]
            answer = self._format_knowledge(best_result)
            
            return {
                "found": True,
                "answer": answer,
                "sources": [r['source'] for r in search_results],
                "confidence": 0.7
            }
            
        except Exception as e:
            logger.error(f"❌ Quick search failed: {e}")
            return {
                "found": False,
                "answer": f"Search failed: {str(e)}",
                "sources": []
            }