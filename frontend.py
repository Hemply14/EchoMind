# frontend.py
import streamlit as st
import requests
import time
from datetime import datetime
import json
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(__file__))

# Configuration
BASE_URL = "http://localhost:8000"
st.set_page_config(
    page_title="Privacy-First AI Assistant", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "teaching_mode" not in st.session_state:
        st.session_state.teaching_mode = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{int(time.time())}"
    if "research_enabled" not in st.session_state:
        st.session_state.research_enabled = False
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Chat"

def get_health():
    """Get system health status"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Health check failed: {e}")
    return {"status": "offline", "memory_count": 0, "rule_count": 0}

def get_performance():
    """Get performance stats"""
    try:
        response = requests.get(f"{BASE_URL}/performance", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {}

def get_user_profile():
    """Get user profile"""
    try:
        response = requests.get(
            f"{BASE_URL}/user-profile",
            params={"user_id": st.session_state.user_id},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {"interests": [], "topics_discussed": [], "conversation_count": 0}

def send_message(query, use_research=False):
    """Send message to AI and get response"""
    try:
        endpoint = "/ask-context" if use_research else "/ask"
        
        if use_research:
            data = {
                "query": query,
                "user_id": st.session_state.user_id,
                "threshold": 0.6,
                "enable_research": True
            }
        else:
            data = {
                "query": query,
                "threshold": 0.6
            }
            
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            json=data,
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"response": f"Error: Server returned {response.status_code}", "confidence": 0.0, "source": "error"}
            
    except requests.exceptions.ConnectionError:
        return {"response": "Error: Cannot connect to backend server. Make sure it's running on localhost:8000", "confidence": 0.0, "source": "error"}
    except requests.exceptions.Timeout:
        return {"response": "Error: Request timeout. The server is taking too long to respond.", "confidence": 0.0, "source": "error"}
    except Exception as e:
        return {"response": f"Error: {str(e)}", "confidence": 0.0, "source": "error"}

def teach_ai(input_text, output_text, context, category):
    """Teach the AI new knowledge"""
    try:
        response = requests.post(
            f"{BASE_URL}/teach",
            json={
                "input_text": input_text,
                "output_text": output_text,
                "context": context,
                "category": category
            },
            timeout=10
        )
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    except Exception as e:
        return False, str(e)

def research_topic(topic):
    """Research a topic online"""
    try:
        response = requests.post(
            f"{BASE_URL}/research",
            json={"topic": topic, "depth": "basic"},
            timeout=30
        )
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    except Exception as e:
        return False, str(e)

def submit_feedback(query, response_text, rating):
    """Submit feedback to AI"""
    try:
        response = requests.post(
            f"{BASE_URL}/feedback",
            json={
                "query": query,
                "response": response_text,
                "rating": rating
            },
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

def get_memories(limit=10):
    """Get recent memories"""
    try:
        response = requests.get(f"{BASE_URL}/memories", params={"limit": limit}, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def delete_memory(memory_id):
    """Delete a memory"""
    try:
        response = requests.delete(f"{BASE_URL}/memories/{memory_id}", timeout=5)
        return response.status_code == 200
    except:
        return False

def force_update():
    """Force knowledge base update"""
    try:
        response = requests.post(f"{BASE_URL}/force-update", timeout=10)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except:
        return False, None

def render_sidebar():
    """Render the sidebar with stats and controls"""
    with st.sidebar:
        st.title("🤖 Control Panel")
        
        # Connection status
        st.subheader("System Status")
        health = get_health()
        
        status_color = "🟢" if health["status"] == "healthy" else "🔴"
        st.write(f"{status_color} **Status:** {health['status'].upper()}")
        
        if health["status"] != "healthy":
            st.error("Backend server not connected!")
            st.info("""
            **To fix this:**
            1. Start the backend: `python run.py`
            2. Wait for it to fully load
            3. Refresh this page
            """)
            return False
        
        # Quick stats
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Memories", health["memory_count"])
        with col2:
            st.metric("Rules", health["rule_count"])
        
        # Performance stats
        with st.expander("📊 Performance"):
            perf = get_performance()
            if perf:
                st.write(f"**Cache:** {perf.get('memory_cache_size', 0)}")
                st.write(f"**Conversations:** {perf.get('conversation_history', 0)}")
                st.write(f"**Pending Updates:** {perf.get('pending_updates', 0)}")
                st.write(f"**User Interests:** {perf.get('user_interests', 0)}")
            else:
                st.write("Performance data unavailable")
        
        st.divider()
        
        # Chat settings
        st.subheader("Chat Settings")
        st.session_state.research_enabled = st.toggle(
            "🌐 Enable Web Research", 
            value=st.session_state.research_enabled,
            help="Allow AI to search online for unknown topics"
        )
        
        st.session_state.teaching_mode = st.toggle(
            "📚 Teaching Mode", 
            value=st.session_state.teaching_mode,
            help="Show teaching interface in chat"
        )
        
        st.divider()
        
        # Quick actions
        st.subheader("Quick Actions")
        
        if st.button("🔄 Refresh Knowledge", use_container_width=True):
            with st.spinner("Refreshing..."):
                success, result = force_update()
                if success:
                    st.success("Knowledge base refreshed!")
                else:
                    st.error("Failed to refresh")
                time.sleep(2)
                st.rerun()
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        if st.button("📋 View Memories", use_container_width=True):
            st.session_state.active_tab = "Memories"
            st.rerun()
        
        st.divider()
        
        # User insights
        st.subheader("👤 Your Profile")
        profile = get_user_profile()
        
        if profile.get('interests'):
            st.write("**Your Interests:**")
            for interest in profile['interests'][:5]:
                st.write(f"• {interest}")
        else:
            st.write("Still learning about you...")
        
        st.write(f"**Total Chats:** {profile.get('conversation_count', 0)}")
        
        st.divider()
        st.caption("🔒 100% Private • 🚀 Fully Local • 🤖 Your AI")
        
        return True

def render_chat_interface():
    """Render the main chat interface"""
    st.header("💬 Chat with Your AI")
    
    # Display chat messages
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show metadata for AI responses
            if message["role"] == "assistant":
                confidence = message.get("confidence", 0)
                source = message.get("source", "unknown")
                
                # Create columns for confidence and feedback
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    confidence_text = f"**Confidence:** {confidence:.0%}"
                    source_text = f"**Source:** {source}"
                    
                    if message.get("enhancement"):
                        enhancement_icons = {
                            "common_sense": "💡",
                            "personalization": "🎯", 
                            "context": "🔄",
                            "web_research": "🌐"
                        }
                        icon = enhancement_icons.get(message["enhancement"], "✨")
                        enhancement_text = f"**Enhanced with:** {message['enhancement']} {icon}"
                        st.caption(f"{confidence_text} • {source_text} • {enhancement_text}")
                    else:
                        st.caption(f"{confidence_text} • {source_text}")
                
                with col2:
                    # Feedback buttons
                    feedback_col1, feedback_col2 = st.columns(2)
                    with feedback_col1:
                        if st.button("👍", key=f"good_{i}", use_container_width=True):
                            if submit_feedback(
                                st.session_state.messages[i-1]["content"] if i > 0 else "",
                                message["content"],
                                5
                            ):
                                st.success("Thanks!")
                            time.sleep(1)
                            st.rerun()
                    with feedback_col2:
                        if st.button("👎", key=f"bad_{i}", use_container_width=True):
                            if submit_feedback(
                                st.session_state.messages[i-1]["content"] if i > 0 else "",
                                message["content"],
                                1
                            ):
                                st.info("Thanks for the feedback!")
                            time.sleep(1)
                            st.rerun()
    
    # Teaching interface (if enabled)
    if st.session_state.teaching_mode:
        render_teaching_interface()
        st.divider()
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about coding, college, productivity..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                response_data = send_message(prompt, st.session_state.research_enabled)
                
                # Display AI response
                st.markdown(response_data["response"])
                
                # Display metadata
                confidence = response_data.get("confidence", 0)
                source = response_data.get("source", "unknown")
                enhancement = response_data.get("enhancement")
                
                metadata_text = f"**Confidence:** {confidence:.0%} • **Source:** {source}"
                if enhancement:
                    enhancement_icons = {
                        "common_sense": "💡",
                        "personalization": "🎯", 
                        "context": "🔄",
                        "web_research": "🌐"
                    }
                    icon = enhancement_icons.get(enhancement, "✨")
                    metadata_text += f" • **Enhanced with:** {enhancement} {icon}"
                
                if response_data.get("research_used"):
                    metadata_text += " • 🔍 **Web Research Used**"
                
                st.caption(metadata_text)
        
        # Add AI response to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_data["response"],
            "confidence": response_data.get("confidence", 0),
            "source": response_data.get("source", "unknown"),
            "enhancement": response_data.get("enhancement")
        })

def render_teaching_interface():
    """Render the teaching interface"""
    st.subheader("📚 Teach Your AI")
    
    with st.form("teaching_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            input_text = st.text_area(
                "When someone asks...",
                placeholder="e.g., 'How do you handle coding stress?'",
                height=100,
                key="teach_input"
            )
            context = st.text_input(
                "Context (optional)",
                placeholder="e.g., 'College student struggling with deadlines'",
                key="teach_context"
            )
        
        with col2:
            output_text = st.text_area(
                "You respond with...",
                placeholder="e.g., 'I take breaks, listen to music, and remember why I started coding!'",
                height=100,
                key="teach_output"
            )
            category = st.selectbox(
                "Category",
                ["general", "coding_life", "productivity", "motivation", "college_life", 
                 "learning", "mental_health", "personal_growth", "project_management"],
                key="teach_category"
            )
        
        submitted = st.form_submit_button("💾 Teach This Response", type="primary", use_container_width=True)
        
        if submitted:
            if not input_text.strip() or not output_text.strip():
                st.error("❌ Please fill in both input and output fields")
            else:
                with st.spinner("Teaching AI..."):
                    success, result = teach_ai(input_text, output_text, context, category)
                    if success:
                        st.success("✅ Successfully taught! Your AI has learned this response.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to teach: {result}")

def render_research_interface():
    """Interface for researching topics"""
    st.header("🔍 Research & Learn")
    st.markdown("Research topics online and automatically add them to your AI's knowledge!")
    
    with st.form("research_form"):
        topic = st.text_input(
            "Topic to research", 
            placeholder="e.g., machine learning basics, Python programming, productivity techniques",
            key="research_topic"
        )
        research_depth = st.selectbox(
            "Research depth", 
            ["basic", "comprehensive"],
            key="research_depth"
        )
        
        submitted = st.form_submit_button("🔬 Research & Learn", type="primary", use_container_width=True)
        
        if submitted:
            if not topic.strip():
                st.error("❌ Please enter a topic to research")
            else:
                with st.spinner("Researching online... This may take a moment."):
                    success, result = research_topic(topic)
                    if success:
                        if result.get("status") == "success":
                            st.success(f"✅ {result['message']}")
                            st.write(f"**Sources used:** {', '.join(result['sources'])}")
                            st.write(f"**Items learned:** {result['learned_items']}")
                        else:
                            st.warning(f"⚠️ {result['message']}")
                    else:
                        st.error(f"❌ Research failed: {result}")
    
    st.divider()
    
    # Sample research topics
    st.subheader("💡 Try Researching These Topics")
    col1, col2, col3 = st.columns(3)
    
    sample_topics = [
        "Python programming basics",
        "Machine learning introduction", 
        "Time management techniques",
        "Web development fundamentals",
        "Data science overview",
        "Healthy study habits"
    ]
    
    for i, topic in enumerate(sample_topics):
        col = col1 if i % 3 == 0 else col2 if i % 3 == 1 else col3
        with col:
            if st.button(topic, key=f"research_{i}", use_container_width=True):
                st.session_state.research_topic = topic
                st.rerun()

def render_memories_interface():
    """Interface for managing memories"""
    st.header("📝 Memory Management")
    st.markdown("View and manage what your AI has learned")
    
    # Memory filters
    col1, col2, col3 = st.columns(3)
    with col1:
        category_filter = st.selectbox(
            "Filter by category",
            ["all", "general", "coding_life", "productivity", "motivation", "college_life", 
             "learning", "mental_health", "personal_growth", "researched_knowledge"]
        )
    with col2:
        limit = st.slider("Show memories", 5, 50, 10)
    with col3:
        if st.button("🔄 Refresh Memories", use_container_width=True):
            st.rerun()
    
    # Load memories
    with st.spinner("Loading memories..."):
        memories = get_memories(limit=limit)
    
    if not memories:
        st.info("No memories found. Start teaching your AI or use the research feature!")
        return
    
    st.write(f"**Showing {len(memories)} memories:**")
    
    for i, memory in enumerate(memories):
        with st.expander(f"#{memory['id']} - {memory['category']} - {memory['input_text'][:50]}...", expanded=i < 3):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.write(f"**Question:** {memory['input_text']}")
                st.write(f"**Answer:** {memory['output_text']}")
                if memory.get('context'):
                    st.write(f"**Context:** {memory['context']}")
                st.write(f"**Created:** {memory['created_at']}")
                st.write(f"**Confidence:** {memory['confidence']:.0%}")
            
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{memory['id']}", use_container_width=True):
                    if delete_memory(memory['id']):
                        st.success("Memory deleted!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to delete memory")

def render_insights_interface():
    """Show system insights and analytics"""
    st.header("📊 System Insights")
    
    try:
        # Get all data
        health = get_health()
        profile = get_user_profile()
        performance = get_performance()
        
        # System Health
        st.subheader("🩺 System Health")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Memories", health["memory_count"])
        with col2:
            st.metric("Rules", health["rule_count"])
        with col3:
            st.metric("Cache Size", health["cache_size"])
        with col4:
            status_color = "🟢" if health["status"] == "healthy" else "🔴"
            st.metric("Status", health["status"].upper())
        
        # User Insights
        st.subheader("👤 User Insights")
        if profile.get('interests'):
            st.write("**Your Top Interests:**")
            interests_cols = st.columns(3)
            for i, interest in enumerate(profile['interests'][:6]):
                col = interests_cols[i % 3]
                with col:
                    st.write(f"• {interest}")
        else:
            st.info("No user interests detected yet. Keep chatting!")
        
        st.write(f"**Total Conversations:** {profile.get('conversation_count', 0)}")
        st.write(f"**Topics Discussed:** {len(profile.get('topics_discussed', []))}")
        
        # Performance Metrics
        st.subheader("⚡ Performance Metrics")
        if performance:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Conversation History", performance.get('conversation_history', 0))
            with col2:
                st.metric("User Interests", performance.get('user_interests', 0))
            with col3:
                st.metric("Successful Responses", performance.get('successful_responses', 0))
            with col4:
                st.metric("Feedback Ratings", performance.get('total_feedback_ratings', 0))
        else:
            st.info("Performance data unavailable")
            
    except Exception as e:
        st.error(f"Error loading insights: {e}")

def main():
    """Main application"""
    # Initialize session state
    init_session_state()
    
    # Main title
    st.title("🤖 Privacy-First AI Assistant")
    st.markdown("**Your data stays with you • No cloud tracking • Fully customizable**")
    
    # Check connection and render sidebar
    is_connected = render_sidebar()
    
    if not is_connected:
        st.error("## 🔌 Backend Server Not Connected")
        st.info("""
        **To start using your AI:**
        
        1. **Start the backend server** (in a terminal):
        ```bash
        python run.py
        ```
        
        2. **Wait for it to fully load** (you should see "Uvicorn running on http://0.0.0.0:8000")
        
        3. **Refresh this page** once the backend is ready
        
        The backend provides the AI brain, while this frontend is just the interface!
        """)
        return
    
    # Tab navigation
    tabs = st.tabs(["💬 Chat", "🔍 Research", "📝 Memories", "📊 Insights"])
    
    with tabs[0]:
        render_chat_interface()
    
    with tabs[1]:
        render_research_interface()
    
    with tabs[2]:
        render_memories_interface()
    
    with tabs[3]:
        render_insights_interface()
    
    # Footer
    st.divider()
    st.caption("""
    **Privacy-First AI Assistant** • Built with Python • 
    [Report Issues](https://github.com/your-repo/issues) • 
    [Documentation](http://localhost:8000/docs)
    """)

if __name__ == "__main__":
    main()