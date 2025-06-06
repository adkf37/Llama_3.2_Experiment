import streamlit as st
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llama_client import LlamaClient
from rag_system import RAGSystem
from config import config

st.set_page_config(
    page_title="Llama 3.2 RAG System",
    page_icon="🦙",
    layout="wide"
)

# Initialize session state
if 'llama_client' not in st.session_state:
    try:
        st.session_state.llama_client = LlamaClient()
        st.session_state.rag_system = RAGSystem()
        st.session_state.initialized = True
    except Exception as e:
        st.session_state.initialized = False
        st.session_state.error = str(e)

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Sidebar configuration
with st.sidebar:
    st.title("🦙 Llama 3.2 RAG")
    
    if not st.session_state.get('initialized', False):
        st.error("⚠️ System not initialized")
        st.error(st.session_state.get('error', 'Unknown error'))
        st.info("Make sure Ollama is installed and running, then restart the app.")
        st.stop()
    
    # Model configuration
    st.header("Model Settings")
    
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=config.get('model.temperature', 0.7),
        step=0.1,
        help="Controls randomness. Lower = more focused, Higher = more creative"
    )
    
    max_tokens = st.slider(
        "Max Tokens",
        min_value=100,
        max_value=4000,
        value=config.get('model.max_tokens', 2048),
        step=100,
        help="Maximum length of the response"
    )
    
    use_rag = st.checkbox(
        "Enable RAG",
        value=True,
        help="Use Retrieval Augmented Generation for enhanced responses"
    )
    
    # Knowledge base info
    st.header("Knowledge Base")
    
    if st.session_state.initialized:
        info = st.session_state.rag_system.get_collection_info()
        st.metric("Documents", info['document_count'])
        st.info(f"Model: {info['embedding_model']}")
    
    # Add fact section
    st.header("Add Knowledge")
    
    with st.form("add_fact_form"):
        new_fact = st.text_area(
            "Add a new fact:",
            placeholder="Enter a fact or piece of information to add to the knowledge base..."
        )
        source = st.text_input("Source", placeholder="Optional source reference")
        
        if st.form_submit_button("Add Fact"):
            if new_fact.strip():
                try:
                    st.session_state.rag_system.add_documents(
                        documents=[new_fact],
                        metadata=[{"source": source or "web_interface", "type": "fact"}]
                    )
                    st.success("✅ Fact added to knowledge base!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error adding fact: {e}")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main chat interface
st.title("🦙 Llama 3.2 RAG Chat System")

# Display current settings
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Temperature", f"{temperature:.1f}")
with col2:
    st.metric("Max Tokens", max_tokens)
with col3:
    st.metric("RAG", "Enabled" if use_rag else "Disabled")

# Chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "context_count" in message:
            st.caption(f"📖 Used {message['context_count']} context documents")

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if use_rag:
                    # Get relevant context
                    context = st.session_state.rag_system.get_relevant_context(prompt)
                    
                    if context:
                        response = st.session_state.llama_client.generate_with_context(
                            prompt=prompt,
                            context=context,
                            temperature=temperature
                        )
                        context_count = len(context)
                    else:
                        response = st.session_state.llama_client.generate(
                            prompt=prompt,
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                        context_count = 0
                else:
                    response = st.session_state.llama_client.generate(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    context_count = None
                
                st.markdown(response)
                
                # Add assistant message
                assistant_message = {"role": "assistant", "content": response}
                if context_count is not None:
                    assistant_message["context_count"] = context_count
                    if context_count > 0:
                        st.caption(f"📖 Used {context_count} context documents")
                
                st.session_state.messages.append(assistant_message)
                
            except Exception as e:
                error_msg = f"❌ Error: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Example questions
if not st.session_state.messages:
    st.markdown("### 💡 Try asking:")
    
    example_questions = [
        "What is Llama 3.2?",
        "How does RAG work?",
        "What are some Python best practices?",
        "How do I use Ollama?",
        "What's the difference between temperature settings?"
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(example_questions):
        with cols[i % 2]:
            if st.button(question, key=f"example_{i}"):
                st.session_state.messages.append({"role": "user", "content": question})
                st.rerun()
