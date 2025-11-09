# interactive_import.py
import requests

BASE_URL = "http://localhost:8000"

def add_single_memory():
    print("Add a new memory to your AI:")
    
    input_text = input("Input text: ")
    output_text = input("Output text: ")
    context = input("Context (optional): ")
    category = input("Category: ")
    
    response = requests.post(f"{BASE_URL}/teach", json={
        "input_text": input_text,
        "output_text": output_text,
        "context": context,
        "category": category
    })
    
    if response.status_code == 200:
        print("✅ Memory added successfully!")
    else:
        print("❌ Failed to add memory")

if __name__ == "__main__":
    add_single_memory()