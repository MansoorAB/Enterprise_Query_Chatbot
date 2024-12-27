import streamlit as st
from rag_system import EnterpriseAssistant
import os
import tempfile

def initialize_rag():
    """Initialize RAG system if not already in session state"""
    if 'rag' not in st.session_state:
        st.session_state.rag = EnterpriseAssistant(db_dir="./data/startup_chroma_db")
        
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def main():
    st.set_page_config(
        page_title="Enterprise Policy Assistant",
        page_icon="📚",
        layout="centered"
    )
    
    initialize_rag()
    
    st.title("📚 Enterprise Policy Assistant")
    
    # Main chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for q, a in st.session_state.chat_history:
            st.markdown("🙋‍♂️ **You:** " + q)
            st.markdown("🤖 **Assistant:** " + a)
            st.markdown("---")
    
    # Input area
    st.markdown("### Ask a question")
    # Use form to handle Enter key
    with st.form(key='question_form', clear_on_submit=False):
        question = st.text_input("Type your question here", key="question")
        submit_button = st.form_submit_button("Ask")
    
    if submit_button and question:
        try:
            response = st.session_state.rag.query(question)
            
            # Add to chat history
            st.session_state.chat_history.append((question, response))
            
            # Show latest response
            st.markdown("🙋‍♂️ **You:** " + question)
            st.markdown("🤖 **Assistant:** " + response)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        # Clear both chat history and form input
        for key in list(st.session_state.keys()):
            if key != 'rag':  # Keep the RAG system initialized
                del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main() 