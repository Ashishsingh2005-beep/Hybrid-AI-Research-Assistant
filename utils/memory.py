import os
import json
import logging
import streamlit as st
from datetime import datetime

logger = logging.getLogger(__name__)

SESSIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chat_sessions"))
METRICS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "local_models", "savings_metrics.json"))

os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)

class ConversationMemory:
    """
    Manages chatbot conversation history and token/stat logging,
    supporting both Streamlit session state and persistent local files.
    """
    def __init__(self, session_key="chat_history"):
        self.session_key = session_key
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = []
            
        if "stats_history" not in st.session_state:
            st.session_state["stats_history"] = []
            
        if "current_session_file" not in st.session_state:
            st.session_state["current_session_file"] = None

    def add_message(self, role: str, content: str, stats: dict = None):
        """
        Adds a message to the conversation history and updates stats.
        Also automatically saves to the persistent file if a session is active,
        and saves cumulative stats for the savings dashboard.
        """
        st.session_state[self.session_key].append({
            "role": role, 
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        if stats:
            # Ensure timestamp is in stats
            if "timestamp" not in stats:
                stats["timestamp"] = datetime.now().isoformat()
            st.session_state["stats_history"].append(stats)
            self._save_metric_to_persistent_file(stats)
            
        # Auto-save current session if active
        if st.session_state["current_session_file"]:
            self.save_session(st.session_state["current_session_file"])

    def get_messages(self):
        return st.session_state[self.session_key]

    def clear(self):
        st.session_state[self.session_key] = []
        st.session_state["stats_history"] = []
        st.session_state["current_session_file"] = None
        
    def get_formatted_history(self, limit=10) -> str:
        history = st.session_state[self.session_key][-limit:]
        formatted = ""
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted += f"{role}: {msg['content']}\n"
        return formatted

    def get_last_stats(self) -> dict:
        if st.session_state["stats_history"]:
            return st.session_state["stats_history"][-1]
        return {
            "model": "N/A",
            "response_time": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cpu_percent": 0.0,
            "ram_percent": 0.0
        }

    # --- Persistent Chat Sessions (Save / Load / List) ---
    
    def save_session(self, filename: str):
        """
        Saves the current session messages and stats to a JSON file.
        """
        if not filename.endswith(".json"):
            filename = f"{filename}.json"
        
        path = os.path.join(SESSIONS_DIR, filename)
        data = {
            "title": filename.replace(".json", "").replace("_", " ").title(),
            "last_updated": datetime.now().isoformat(),
            "messages": st.session_state[self.session_key],
            "stats": st.session_state["stats_history"]
        }
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            st.session_state["current_session_file"] = filename
            logger.info(f"Session saved successfully to {filename}")
        except Exception as e:
            logger.error(f"Error saving session: {e}")

    def load_session(self, filename: str) -> bool:
        """
        Loads a saved session into session state.
        """
        if not filename.endswith(".json"):
            filename = f"{filename}.json"
            
        path = os.path.join(SESSIONS_DIR, filename)
        if not os.path.exists(path):
            return False
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            st.session_state[self.session_key] = data.get("messages", [])
            st.session_state["stats_history"] = data.get("stats", [])
            st.session_state["current_session_file"] = filename
            logger.info(f"Session loaded successfully from {filename}")
            return True
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return False

    def list_sessions(self) -> list[dict]:
        """
        Lists all available saved sessions.
        """
        sessions = []
        if not os.path.exists(SESSIONS_DIR):
            return []
            
        for name in os.listdir(SESSIONS_DIR):
            if name.endswith(".json"):
                path = os.path.join(SESSIONS_DIR, name)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    sessions.append({
                        "filename": name,
                        "title": data.get("title", name),
                        "last_updated": data.get("last_updated", "")
                    })
                except Exception:
                    pass
        # Sort by last updated descending
        sessions.sort(key=lambda x: x["last_updated"], reverse=True)
        return sessions

    def delete_session(self, filename: str):
        """
        Deletes a saved session file.
        """
        if not filename.endswith(".json"):
            filename = f"{filename}.json"
        path = os.path.join(SESSIONS_DIR, filename)
        if os.path.exists(path):
            try:
                os.remove(path)
                if st.session_state["current_session_file"] == filename:
                    self.clear()
            except Exception as e:
                logger.error(f"Error deleting session: {e}")

    # --- Persistent ROI Dashboard Metrics ---
    
    def _save_metric_to_persistent_file(self, stats: dict):
        """
        Appends the inference stats to local_models/savings_metrics.json.
        """
        existing_metrics = []
        if os.path.exists(METRICS_FILE):
            try:
                with open(METRICS_FILE, "r", encoding="utf-8") as f:
                    existing_metrics = json.load(f)
            except Exception:
                existing_metrics = []
                
        # Clean/sanitize stats before writing
        clean_stats = {
            "model": stats.get("model", "Unknown"),
            "response_time": stats.get("response_time", 0.0),
            "input_tokens": stats.get("input_tokens", 0),
            "output_tokens": stats.get("output_tokens", 0),
            "cost": stats.get("cost", 0.0),
            "cpu_percent": stats.get("cpu_percent", 0.0),
            "ram_percent": stats.get("ram_percent", 0.0),
            "timestamp": stats.get("timestamp", datetime.now().isoformat())
        }
        
        existing_metrics.append(clean_stats)
        
        try:
            with open(METRICS_FILE, "w", encoding="utf-8") as f:
                json.dump(existing_metrics, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving ROI metrics: {e}")

    @staticmethod
    def get_all_persistent_metrics() -> list[dict]:
        """
        Retrieves all persistent metrics for dashboard analytics.
        """
        if not os.path.exists(METRICS_FILE):
            return []
        try:
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
            
    @staticmethod
    def clear_all_persistent_metrics():
        """
        Clears all persistent analytics metrics.
        """
        if os.path.exists(METRICS_FILE):
            try:
                os.remove(METRICS_FILE)
            except Exception:
                pass
