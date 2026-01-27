import os
import sqlite3
import json
import datetime
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
# Prefer GOOGLE_API_KEY from environment, but fallback to manual config if needed
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../anki_export.db")
CHAT_DB_PATH = os.path.join(BASE_DIR, "chat_history.db")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

def get_db_connection(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_chat_db():
    conn = get_db_connection(CHAT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            has_image BOOLEAN DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blackboard (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Insert default row if not exists
    cursor.execute("INSERT OR IGNORE INTO blackboard (id, content) VALUES (1, '')")
    conn.commit()
    conn.close()

def save_message(role: str, content: str, has_image: bool = False):
    conn = get_db_connection(CHAT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (role, content, has_image) VALUES (?, ?, ?)", (role, content, has_image))
    conn.commit()
    conn.close()

def get_chat_history(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection(CHAT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content, has_image FROM messages ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    # Reverse to get chronological order
    history = [{"role": row["role"], "parts": [row["content"]]} for row in reversed(rows)]
    return history

def get_blackboard() -> str:
    conn = get_db_connection(CHAT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM blackboard WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return row["content"] if row else ""

def log_interaction(request_parts: List[Any], response_obj: Any):
    """
    Log the request and response to a JSON file for debugging.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = os.path.join(LOGS_DIR, f"log_{timestamp}.json")
    
    # Extract token counts if available
    usage_metadata = {}
    if hasattr(response_obj, 'usage_metadata'):
        usage_metadata = {
            "prompt_token_count": response_obj.usage_metadata.prompt_token_count,
            "candidates_token_count": response_obj.usage_metadata.candidates_token_count,
            "total_token_count": response_obj.usage_metadata.total_token_count
        }
    
    # Prepare serializable request
    serializable_request = []
    for part in request_parts:
        if isinstance(part, dict) and "data" in part:
            # Truncate base64 image data for logs
            serializable_request.append({
                "mime_type": part.get("mime_type"),
                "data": "<base64_image_data_truncated>"
            })
        else:
            serializable_request.append(part)

    log_data = {
        "timestamp": timestamp,
        "request": serializable_request,
        "response_text": response_obj.text if hasattr(response_obj, 'text') else str(response_obj),
        "usage": usage_metadata
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

# --- Tool Implementation ---

def lookup_vocabulary_batch(words: List[str]) -> Dict[str, List[str]]:
    """
    Check the difficulty/mastery level of a list of Japanese words/kanji.
    """
    cleaned_words = [w.strip() for w in words if w.strip()]
    if not cleaned_words:
        return {"known": [], "new": [], "unknown_to_db": []}

    conn = get_db_connection(DB_PATH)
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in cleaned_words)
    query = f"SELECT characters, status FROM notes WHERE characters IN ({placeholders})"
    cursor.execute(query, cleaned_words)
    results = cursor.fetchall()
    conn.close()
    
    db_status_map = {row["characters"]: row["status"] for row in results}
    output = {"known": [], "new": [], "unknown_to_db": []}
    
    for word in cleaned_words:
        if word in db_status_map:
            status = db_status_map[word]
            if status in ["Mature"]:
                output["known"].append(word)
            else:
                output["new"].append(word)
        else:
            output["unknown_to_db"].append(word)
            
    return output

def write_to_blackboard(content: str) -> str:
    """
    Writes content to the session blackboard. Overwrites existing content.
    
    Args:
        content: The text to write to the blackboard (e.g., summary of grammar points, vocabulary list).
    """
    conn = get_db_connection(CHAT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE blackboard SET content = ?, timestamp = CURRENT_TIMESTAMP WHERE id = 1", (content,))
    conn.commit()
    conn.close()
    return "Blackboard updated."

# --- Gemini Setup ---

def setup_gemini():
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable is not set. Please set it in a .env file or environment.")
    
    genai.configure(api_key=GOOGLE_API_KEY)
    tools = [lookup_vocabulary_batch, write_to_blackboard]
    
    # Use gemini-1.5-flash which supports multimodal input
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=tools,
        system_instruction=generate_system_prompt() # Set system prompt here
    )
    return model

def generate_system_prompt() -> str:
    today = datetime.date.today().isoformat()
    return f"""
Current Date: {today}

You are a Japanese tutor. Your goal is to help the user learn Japanese. Your task is to keep finding the edge of the user's knowledge to keep them engaged and learning efficiently.

You have access to the following tools:
- lookup_vocabulary_batch: The user learns kanji and vocabulary with an Anki deck. You can check if the user is familiar with the vocabulary you intend to use. This does not mean you can't use the vocabulary if the user is not familiar with it, but you can use this information to guide your tutoring.
- write_to_blackboard: This will be a "rolling session" blackboard so that both you and the user can keep track of what the user is currently working on. Your response will overwrite the entire blackboard, so use this function accordingly.


Current Blackboard:
{get_blackboard()}
"""

# --- Chat Loop ---

def start_chat_session():
    # print("Initializing Chat Session...", flush=True)
    try:
        init_chat_db()
        model = setup_gemini()
        
        # In a real app, we would load history properly.
        # For this loop, we instantiate a new chat object per turn or keep it alive.
        # Keeping it alive is better for context.
        chat = model.start_chat(enable_automatic_function_calling=True)
        
        # print("Chat Session Ready. Send JSON: {\"content\": \"...\", \"image\": \"base64...\"}", flush=True)
        
        while True:
            # Read from stdin
            try:
                line = input()
            except EOFError:
                break
                
            if not line:
                continue
                
            # Try parsing as JSON
            user_text = ""
            user_image_data = None
            
            try:
                data = json.loads(line)
                user_text = data.get("content", "")
                # Expect image as base64 string without data URI prefix if possible, 
                # or strip it if present.
                img_str = data.get("image")
                if img_str:
                    if "base64," in img_str:
                        img_str = img_str.split("base64,")[1]
                    user_image_data = {"mime_type": "image/jpeg", "data": img_str}
            except json.JSONDecodeError:
                # Fallback to plain text
                user_text = line
            
            if user_text.lower() in ['quit', 'exit']:
                break
            
            # Save user message (simplified, ignoring image storage for now)
            save_message("user", user_text, has_image=bool(user_image_data))
            
            # Prepare message parts
            parts = []
            if user_text:
                parts.append(user_text)
            
            if user_image_data:
                parts.append(user_image_data)
            
            # If empty message, skip
            if not parts:
                continue

            # print("Agent: (Thinking...)", flush=True)
            
            try:
                # Send to Gemini
                response = chat.send_message(parts)
                
                # Log interaction
                log_interaction(parts, response)

                agent_text = response.text
                
                # Fetch current blackboard content to send back with response
                blackboard_content = get_blackboard()

                # Output as JSON
                print(json.dumps({
                    "role": "assistant", 
                    "content": agent_text,
                    "blackboard": blackboard_content
                }), flush=True)
                
                # Save response
                save_message("assistant", agent_text)
                
            except Exception as e:
                error_msg = f"Error during generation: {str(e)}"
                print(json.dumps({"role": "system", "error": error_msg}), flush=True)

    except Exception as e:
        print(json.dumps({"role": "system", "error": f"Fatal error: {str(e)}"}))

if __name__ == "__main__":
    start_chat_session()
