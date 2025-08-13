import os
import sys
import requests
from dotenv import load_dotenv

def usage() -> None:
    print(
        "Usage:\n"
        "  List assistants:\n"
        "    VAPI_API_KEY=... python main.py --list\n"
        "    VAPI_API_KEY=... VAPI_LIST=1 python main.py\n"
        "  Update assistant with idle messages:\n"
        "    VAPI_API_KEY=... VAPI_ASSISTANT_ID=... python main.py --update-idle\n"
        "  Get specific assistant details:\n"
        "    VAPI_API_KEY=... VAPI_ASSISTANT_ID=... python main.py --get"
    )

def list_assistants(*, api_key: str, api_url: str) -> int:
    url = f"{api_url.rstrip('/')}/assistant"  # Note: /assistant not /assistants
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"Error {resp.status_code}: {resp.text}")
        return 1
    data = resp.json()
    assistants = data if isinstance(data, list) else data.get("assistants") or data.get("data") or []
    print("\n=== Your Assistants ===")
    for assistant in assistants:
        name = assistant.get("name") if isinstance(assistant, dict) else getattr(assistant, "name", None)
        a_id = assistant.get("id") if isinstance(assistant, dict) else getattr(assistant, "id", None)
        print(f"Name: {name}")
        print(f"ID:   {a_id}")
        print("-" * 40)
    return 0

def get_assistant(*, api_key: str, api_url: str, assistant_id: str) -> int:
    """Get details of a specific assistant"""
    url = f"{api_url.rstrip('/')}/assistant/{assistant_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.get(url, headers=headers, timeout=30)
    
    if resp.status_code != 200:
        print(f"Error {resp.status_code}: {resp.text}")
        return 1
    
    assistant = resp.json()
    print(f"\n=== Assistant Details ===")
    print(f"Name: {assistant.get('name')}")
    print(f"ID: {assistant.get('id')}")
    print(f"Silence Timeout: {assistant.get('silenceTimeoutSeconds', 30)} seconds")
    
    # Check if idle messages are configured
    message_plan = assistant.get('messagePlan', {})
    if message_plan.get('idleMessages'):
        print(f"\nIdle Messages Configuration:")
        print(f"  Messages: {message_plan.get('idleMessages')}")
        print(f"  Timeout: {message_plan.get('idleTimeoutSeconds')} seconds")
        print(f"  Max Count: {message_plan.get('idleMessageMaxSpokenCount')}")
    else:
        print("\n⚠️  No idle messages configured")
    
    return 0

def update_assistant_idle_messages(*, api_key: str, api_url: str, assistant_id: str) -> int:
    """Add idle messages to an assistant"""
    url = f"{api_url.rstrip('/')}/assistant/{assistant_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    update_data = {
        "messagePlan": {
            "idleMessages": [
                "Are you still there?"
            ],
            "idleTimeoutSeconds": 10,
            "idleMessageMaxSpokenCount": 2,
            "idleMessageResetCountOnUserSpeechEnabled": True
        },
        "silenceTimeoutSeconds": 30
    }
    
    print(f"\nUpdating assistant {assistant_id} with idle messages...")
    resp = requests.patch(url, headers=headers, json=update_data, timeout=30)
    
    if resp.status_code != 200:
        print(f"Error {resp.status_code}: {resp.text}")
        return 1
    
    updated = resp.json()
    print("✅ Successfully updated assistant!")
    print(f"Timeline: 10s → First prompt, 20s → Second prompt, 30s → End call")
    return 0

def main() -> int:
    load_dotenv()
    
    # Get API key (your private key)
    api_key = os.environ.get("VAPI_API_KEY") or (sys.argv[1] if len(sys.argv) > 1 else None)
    api_url = os.environ.get("VAPI_API_URL", "https://api.vapi.ai")
    assistant_id = os.environ.get("VAPI_ASSISTANT_ID") or (sys.argv[2] if len(sys.argv) > 2 else None)
    
    if not api_key:
        print("❌ API key required")
        usage()
        return 2
    
    # Check for specific operations
    if "--list" in sys.argv or os.environ.get("VAPI_LIST") in {"1", "true", "TRUE"} or not assistant_id:
        return list_assistants(api_key=api_key, api_url=api_url)
    
    if "--get" in sys.argv:
        if not assistant_id:
            print("❌ VAPI_ASSISTANT_ID required")
            return 2
        return get_assistant(api_key=api_key, api_url=api_url, assistant_id=assistant_id)
    
    if "--update-idle" in sys.argv:
        if not assistant_id:
            print("❌ VAPI_ASSISTANT_ID required")
            print("First run with --list to find your assistant ID")
            return 2
        return update_assistant_idle_messages(
            api_key=api_key, 
            api_url=api_url, 
            assistant_id=assistant_id
        )
    
    # Default behavior: if assistant_id is set, get its details
    if assistant_id:
        return get_assistant(api_key=api_key, api_url=api_url, assistant_id=assistant_id)
    
    usage()
    return 2

if __name__ == "__main__":
    raise SystemExit(main())