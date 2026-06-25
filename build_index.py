from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
import os

# Load embedding model
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def build_faiss_index(chunks_dir="chunks", index_path="faiss_index.bin", metadata_path="metadata.pkl"):
    print("🔨 Building FAISS vector index...")
    
    all_chunks = []
    metadata = []
    
    for filename in os.listdir(chunks_dir):
        if filename.endswith('_chunks.txt'):
            filepath = os.path.join(chunks_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract chunks
            chunks = [c.strip() for c in content.split('--- Chunk') if c.strip()]
            for chunk in chunks:
                # Remove chunk number header
                if '\n' in chunk:
                    chunk_text = '\n'.join(chunk.split('\n')[1:]).strip()
                    all_chunks.append(chunk_text)
                    metadata.append({
                        "source": filename.replace('_chunks.txt', '.txt'),
                        "chunk": chunk_text[:200] + "..."
                    })
    
    if not all_chunks:
        print("❌ No chunks found!")
        return
    
    # Generate embeddings
    print(f"Embedding {len(all_chunks)} chunks...")
    embeddings = embedder.encode(all_chunks, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # Save index and metadata
    faiss.write_index(index, index_path)
    with open(metadata_path, 'wb') as f:
        pickle.dump((all_chunks, metadata), f)
    
    print(f"✅ FAISS index built successfully with {len(all_chunks)} vectors!")
    print(f"   Index saved to: {index_path}")
    print(f"   Metadata saved to: {metadata_path}")

if __name__ == "__main__":
    build_faiss_index()