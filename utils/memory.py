import streamlit as st

class ConversationMemory:
    """
    Manages chatbot conversation history and token/stat logging using Streamlit's session state.
    """
    def __init__(self, session_key="chat_history"):
        self.session_key = session_key
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = []
            
        # Initialize token/stat tracking keys if they don't exist
        if "stats_history" not in st.session_state:
            st.session_state["stats_history"] = []

    def add_message(self, role: str, content: str, stats: dict = None):
        """
        Adds a message to the conversation history.
        stats is an optional dictionary with keys: 'model', 'response_time', 'input_tokens', 'output_tokens', etc.
        """
        st.session_state[self.session_key].append({
            "role": role, 
            "content": content
        })
        if stats:
            st.session_state["stats_history"].append(stats)

    def get_messages(self):
        """
        Returns all messages in the history.
        """
        return st.session_state[self.session_key]

    def clear(self):
        """
        Clears conversation history and stats.
        """
        st.session_state[self.session_key] = []
        st.session_state["stats_history"] = []
        
    def get_formatted_history(self, limit=10) -> str:
        """
        Formats history for LLM/SLM prompt context.
        """
        history = st.session_state[self.session_key][-limit:]
        formatted = ""
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted += f"{role}: {msg['content']}\n"
        return formatted

    def get_last_stats(self) -> dict:
        """
        Returns statistics of the last run.
        """
        if st.session_state["stats_history"]:
            return st.session_state["stats_history"][-1]
        return {
            "model": "N/A",
            "response_time": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "memory_used": "N/A"
        }
