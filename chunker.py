import nltk
from nltk.tokenize import sent_tokenize
import os

# Download NLTK data if needed
nltk.download('punkt', quiet=True)

def chunk_text(text, chunk_size=800, chunk_overlap=150):
    """
    Split text into overlapping chunks for better retrieval
    """
    if not text or len(text.strip()) < 50:
        return []
    
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_len = len(sentence)
        if current_length + sentence_len > chunk_size and current_chunk:
            # Join current chunk and add to list
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)
            
            # Start new chunk with overlap
            overlap_sentences = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk
            current_chunk = overlap_sentences[:]
            current_length = sum(len(s) for s in current_chunk)
        
        current_chunk.append(sentence)
        current_length += sentence_len
    
    # Add the last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

def process_all_documents(docs_dir="griet_docs", output_dir="chunks"):
    os.makedirs(output_dir, exist_ok=True)
    all_chunks = []
    
    for filename in os.listdir(docs_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(docs_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            
            chunks = chunk_text(text)
            all_chunks.extend(chunks)
            
            # Save chunks per document
            chunk_file = os.path.join(output_dir, filename.replace('.txt', '_chunks.txt'))
            with open(chunk_file, 'w', encoding='utf-8') as f:
                for i, chunk in enumerate(chunks):
                    f.write(f"--- Chunk {i+1} ---\n{chunk}\n\n")
    
    print(f"✅ Created {len(all_chunks)} text chunks from documents.")
    return all_chunks

if __name__ == "__main__":
    process_all_documents()