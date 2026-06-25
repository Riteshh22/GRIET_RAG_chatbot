import streamlit as st
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import os

# Page config
st.set_page_config(page_title="GRIET AI Assistant", page_icon="🎓", layout="wide")

# Load model and index
@st.cache_resource
def load_resources():
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    if not os.path.exists("faiss_index.bin"):
        st.error("FAISS index not found. Please run build_index.py first!")
        st.stop()
    
    index = faiss.read_index("faiss_index.bin")
    with open("metadata.pkl", 'rb') as f:
        chunks, metadata = pickle.load(f)
    
    return embedder, index, chunks, metadata

embedder, index, chunks, metadata = load_resources()

# Custom CSS
st.markdown("""
<style>
    .chat-message { padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .user-message { background-color: #e6f3ff; }
    .bot-message { background-color: #f0f2f6; }
</style>
""", unsafe_allow_html=True)

st.title("🎓 GRIET AI Assistant")
st.caption("Ask anything about GRIET - Admissions, Courses, Placements, Campus Life & more")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Type your question here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Embed query
            query_embedding = embedder.encode([prompt])
            query_embedding = np.array(query_embedding).astype('float32')
            
            # Search
            k = 5  # Number of relevant chunks
            distances, indices = index.search(query_embedding, k)
            
            # Retrieve context
            context = ""
            sources = []
            for idx in indices[0]:
                if idx < len(chunks):
                    context += chunks[idx] + "\n\n"
                    if idx < len(metadata):
                        sources.append(metadata[idx]["source"])
            
            # Simple RAG response (can be improved with LLM)
            response = f"""**Relevant Information from GRIET Website:**\n\n{context[:1500]}...\n\n"""
            
            response += """**GRIET AI Assistant Summary:**\n"""
            response += "I found relevant information about GRIET. For the most accurate and up-to-date details, please visit the official website or contact the college administration.\n\n"
            response += "Would you like me to explain anything specific about admissions, courses, placements, or faculty?"
            
            st.markdown(response)
            
            # Show sources
            if sources:
                st.caption("📚 Sources: " + ", ".join(set(sources)))

    st.session_state.messages.append({"role": "assistant", "content": response})