import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8080")

def send_chat(question: str, history: str) -> dict:
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "query": question,
                "history": history
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Map API response to simulation fields
        return {
            "answer": data["response"],
            "total_input_tokens": data["input_tokens"],
            "total_output_tokens": data["output_tokens"],
            "tool_messages": data["tool_messages"],
            "price": 17_000 * (data["input_tokens"] * 0.15 + data["output_tokens"] * 0.6) / 1_000_000
        }
    except Exception as e:
        st.error(f"Error calling API: {str(e)}")
        return {
            "answer": "Sorry, I encountered an error connecting to the API.",
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "tool_messages": [],
            "price": 0
        }

st.title("Chatbot HR ")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask me anything about Resumes!"):
    messages_history = st.session_state.get("messages", [])[-20:]
    history = "\n".join([f'{msg["role"]}: {msg["content"]}' for msg in messages_history]) or " "

    # Display user message in chat message container
    with st.chat_message("Human"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display assistant response in chat message container
    with st.chat_message("AI"):
        response = send_chat(prompt, messages_history)
        answer = response["answer"]
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

    with st.expander("**Tool Calls:**"):
        st.code(response["tool_messages"])

    with st.expander("**History Chat:**"):
        st.code(history)

    with st.expander("**Usage Details:**"):
        st.code(f'input token : {response["total_input_tokens"]}\noutput token : {response["total_output_tokens"]}')