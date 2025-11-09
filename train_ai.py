# train_ai.py
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def teach_ai(input_text, output_text, category="general"):
    response = requests.post(f"{BASE_URL}/teach", json={
        "input_text": input_text,
        "output_text": output_text,
        "category": category
    })
    print(f"✅ Taught: '{input_text}' -> '{output_text}'")
    return response.json()

def add_rule(pattern, action):
    response = requests.post(f"{BASE_URL}/rules", json={
        "pattern": pattern,
        "action": action,
        "priority": 1
    })
    print(f"✅ Added rule: '{pattern}' -> '{action}'")
    return response.json()

def ask_ai(query):
    response = requests.post(f"{BASE_URL}/ask", json={
        "query": query,
        "threshold": 0.6
    })
    result = response.json()
    print(f"❓ Q: {query}")
    print(f"🤖 A: {result['response']} (confidence: {result['confidence']:.2f}, source: {result['source']})")
    print("---")
    return result

def get_health():
    response = requests.get(f"{BASE_URL}/health")
    return response.json()

# Training session
if __name__ == "__main__":
    print("🤖 Starting AI Training Session...\n")
    
    # Check health first
    health = get_health()
    print(f"System Health: {health}\n")
    
    # Add rules first
    add_rule("hello", "Hi there! Welcome to your personal AI assistant!")
    add_rule("thank you", "You're welcome! I'm glad I could help.")
    add_rule("bye", "Goodbye! Feel free to come back anytime.")
    
    # Teach personal information
    teach_ai("What is your name?", "I'm your personal AI assistant! You can call me whatever you like.", "introduction")
    teach_ai("Who are you?", "I'm your AI companion, created to help you with tasks and conversations.", "introduction")
    
    # Teach preferences
    teach_ai("What do you like?", "I enjoy learning new things from you and helping with your questions!", "preferences")
    teach_ai("What is your favorite color?", "I think blue is quite nice, but I'm happy with whatever you prefer!", "preferences")
    
    # Teach factual information
    teach_ai("What can you do?", "I can answer questions based on what you teach me, help organize information, and have conversations with you!", "capabilities")
    teach_ai("How do you work?", "I learn from our conversations and use semantic search to find the most relevant responses from what you've taught me.", "capabilities")
    
    # Test the AI
    print("\n🧪 Testing the AI...\n")
    
    test_questions = [
        "Hello!",
        "What is your name?",
        "Who are you?",
        "What do you like?",
        "Tell me your favorite color",
        "What can you do?",
        "How does this work?",
        "Thank you for your help!",
        "What's the weather like?",
        "Goodbye!"
    ]
    
    for question in test_questions:
        ask_ai(question)
        time.sleep(0.5)  # Small delay between questions
    
    print("🎉 Training session complete!")
    
    # Final health check
    final_health = get_health()
    print(f"\nFinal System Health: {final_health}")