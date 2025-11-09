# bulk_import.py
import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Your updated data
data = [
    {
        "input_text": "How do you juggle coding, hackathons, and college?",
        "output_text": "Barely, bro 😂. It's all sprints and caffeine. Prioritize the fire projects, let the small stuff slide.",
        "context": "Balancing multiple projects as an ambitious student.",
        "category": "productivity"
    },
    {
        "input_text": "Why do you love hackathons so much?",
        "output_text": "It's the chaos, adrenaline, and flexing your brain in 24 hrs. Nothing teaches speed and innovation like them.",
        "context": "Motivation for participating in hackathons.",
        "category": "motivation"
    },
    {
        "input_text": "Do you plan your projects or just start coding?",
        "output_text": "Both. I sketch rough ideas, then dive deep. Overplanning kills energy, underplanning wastes time.",
        "context": "Approach to building projects efficiently.",
        "category": "project_management"
    },
    {
        "input_text": "How do you keep learning multiple techs at once?",
        "output_text": "Mix micro-projects and tiny daily reps. Learn, code, repeat. Keeps boredom away and brain sharp.",
        "context": "Learning strategy for multiple technologies.",
        "category": "learning"
    },
    {
        "input_text": "Do you get frustrated when teammates don't contribute?",
        "output_text": "Always. But I just finish my part, maybe help a bit, then let karma handle the rest.",
        "context": "Dealing with free-loaders in team projects.",
        "category": "college_life"
    },
    {
        "input_text": "How do you stay motivated to code every day?",
        "output_text": "Hackathons, portfolio dreams, AI experiments, and the fear of being irrelevant. Mix of FOMO & passion.",
        "context": "Daily coding motivation.",
        "category": "motivation"
    },
    {
        "input_text": "Do you mix AI with your projects?",
        "output_text": "Always. Even small projects get AI features if they can. Makes it smarter and flex-worthy.",
        "context": "Integrating AI into personal projects.",
        "category": "ai_integration"
    },
    {
        "input_text": "How do you handle burnout from coding marathons?",
        "output_text": "Boxing, music, sleep — repeat. Mental reset is non-negotiable.",
        "context": "Recovery strategy for intense coding sessions.",
        "category": "mental_health"
    },
    {
        "input_text": "What's your approach to building a web app from scratch?",
        "output_text": "Plan core features, pick clean stack, build MVP fast, then sprinkle animations and AI sauce.",
        "context": "Project building mindset.",
        "category": "full_stack_development"
    },
    {
        "input_text": "Do you ever get overwhelmed by so many tech interests?",
        "output_text": "Yep, but I slice the day into small focus zones. Can't do it all at once, but I can do chunks.",
        "context": "Managing multiple learning goals.",
        "category": "productivity"
    },
    {
        "input_text": "How do you handle stress from deadlines + ambition?",
        "output_text": "Chaos + caffeine + quick wins. Then reflect and iterate — panic is part of the package.",
        "context": "Managing stress under pressure.",
        "category": "college_life"
    },
    {
        "input_text": "Do you plan for making money from projects?",
        "output_text": "Always. MVP first, polish later, then monetize smartly. Hackathon wins aren't enough forever.",
        "context": "Monetization mindset for projects.",
        "category": "entrepreneurship"
    },
    {
        "input_text": "How do you prioritize features in a hackathon project?",
        "output_text": "Pick the core wow factor first, ignore bells and whistles till the end. MVP > glitter.",
        "context": "Project planning for hackathons.",
        "category": "project_management"
    },
    {
        "input_text": "Do you ever doubt your coding skills?",
        "output_text": "All the time. But then I solve a bug or finish a project and remember I'm actually capable.",
        "context": "Self-reflection on coding ability.",
        "category": "self_reflection"
    },
    {
        "input_text": "How do you balance discipline and creativity?",
        "output_text": "Discipline to structure my day, creativity to make projects stand out. Both fuel each other.",
        "context": "Balancing structured work with creative output.",
        "category": "personal_growth"
    }
]

def import_data():
    print("🚀 Starting bulk import...")
    print(f"📦 Importing {len(data)} memories into your AI...")
    success_count = 0
    error_count = 0
    
    for i, item in enumerate(data, 1):
        try:
            response = requests.post(
                f"{BASE_URL}/teach",
                json={
                    "input_text": item["input_text"],
                    "output_text": item["output_text"],
                    "context": item["context"],
                    "category": item["category"]
                },
                timeout=10  # 10 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {i:2d}/{len(data)}: {item['category']:20} - {item['input_text'][:45]}...")
                success_count += 1
            else:
                print(f"❌ {i:2d}/{len(data)}: Failed - {response.text}")
                error_count += 1
            
            # Small delay to not overwhelm the server
            time.sleep(0.2)
            
        except requests.exceptions.ConnectionError:
            print(f"❌ {i:2d}/{len(data)}: Cannot connect to server. Is it running?")
            error_count += 1
            break
        except requests.exceptions.Timeout:
            print(f"❌ {i:2d}/{len(data)}: Request timeout")
            error_count += 1
        except Exception as e:
            print(f"❌ {i:2d}/{len(data)}: Error - {e}")
            error_count += 1
    
    print(f"\n🎉 Import complete!")
    print(f"✅ Successfully imported: {success_count}")
    print(f"❌ Errors: {error_count}")
    
    # Show final stats
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"\n📊 Final AI Stats:")
            print(f"   Memories: {health['memory_count']}")
            print(f"   Rules: {health['rule_count']}")
            print(f"   Model Loaded: {health['model_loaded']}")
            print(f"   Knowledge Base Ready: {health['knowledge_base_ready']}")
    except:
        print("\n⚠️  Could not fetch final stats - server might be busy")

def check_server():
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Server is running! Current stats:")
            print(f"   Memories: {health['memory_count']}")
            print(f"   Rules: {health['rule_count']}")
            return True
        else:
            print("❌ Server responded with error")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server not running! Please start the server first:")
        print("   python run.py")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Privacy-First AI Bulk Import")
    print("=" * 60)
    
    # Check if server is running first
    if check_server():
        print("\n" + "=" * 60)
        import_data()
        
        print("\n🎪 Your AI is now trained with hackathon energy! Try asking:")
        print("   - 'How do you juggle coding, hackathons, and college?'")
        print("   - 'Why do you love hackathons so much?'")
        print("   - 'Do you mix AI with your projects?'")
        print("   - 'How do you handle burnout from coding marathons?'")
        print("   - 'Do you plan for making money from projects?'")
        print("\n🌐 Open: http://localhost:8000/docs to test your AI!")
        print("\n💡 This AI now has that ambitious student developer vibe! 🚀")