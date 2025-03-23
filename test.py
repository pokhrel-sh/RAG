import os
from pathlib import Path
import re
import numpy as np
import redis
from redis.commands.search.query import Query
import ollama
import PyPDF2

# Initialize Redis connection
redis_client = redis.Redis(host="localhost", port=6380, db=0)
VECTOR_DIM = 768
INDEX_NAME = "pdf_embedding_index"
DOC_PREFIX = "doc:"
DISTANCE_METRIC = "COSINE"

# Create an index in Redis
def create_hnsw_index():
    try:
        redis_client.execute_command(f"FT.DROPINDEX {INDEX_NAME} DD")
    except redis.exceptions.ResponseError:
        pass
    redis_client.execute_command(
        f"""
        FT.CREATE {INDEX_NAME} ON HASH PREFIX 1 {DOC_PREFIX}
        SCHEMA 
            text TEXT 
            source TEXT
            chunk_id TEXT
            embedding VECTOR HNSW 6 DIM {VECTOR_DIM} TYPE FLOAT32 DISTANCE_METRIC {DISTANCE_METRIC}
        """
    )
    print("Index created successfully.")

# Generate an embedding using nomic-embed-text
def get_embedding(text: str, model: str = "paraphrase-multilingual") -> list:
    response = ollama.embeddings(model=model, prompt=text)
    return response["embedding"]

# Store the calculated embedding in Redis
def store_embedding(doc_id: str, text: str, source: str, 
    chunk_id: str, embedding: list):
    key = f"{DOC_PREFIX}{doc_id}"
    redis_client.hset(
        key,
        mapping={
            "text": text,
            "source": source,
            "chunk_id": chunk_id,
            "embedding": np.array(embedding, dtype=np.float32).tobytes(),  # Store as byte array
        },
    )

# Extract text from PDF file
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + " "
    return text

# Chunk text into segments of approximately 100 tokens
def chunk_text(text, chunk_size=100):
    # This is a simple chunking method. For more precise token counting, consider using a tokenizer.
    # Approximate a token as 4-5 characters
    words = text.split()
    chunks = []
    current_chunk = []
    current_token_count = 0
    
    for word in words:
        # Estimate token count for this word
        word_token_count = len(word) // 4 + 1
        
        if current_token_count + word_token_count > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_token_count = word_token_count
        else:
            current_chunk.append(word)
            current_token_count += word_token_count
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

# Process all PDFs in a folder
def process_pdf_folder(folder_path):
    pdf_files = list(Path(folder_path).glob('*.pdf'))
    
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return
    
    doc_id_counter = 0
    for pdf_file in pdf_files:
        pdf_path = str(pdf_file)
        pdf_name = os.path.basename(pdf_path)
        print(f"Processing {pdf_name}...")
        
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)
        
        # Chunk the text
        chunks = chunk_text(text)
        
        print(f"Generated {len(chunks)} chunks from {pdf_name}")
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            chunk_id = f"{pdf_name}_{i}"
            
            # Get embedding for the chunk
            embedding = get_embedding(chunk)
            
            # Store the chunk and its embedding
            store_embedding(
                doc_id=str(doc_id_counter),
                text=chunk,
                source=pdf_name,
                chunk_id=chunk_id,
                embedding=embedding
            )
            
            doc_id_counter += 1
            
            if i % 10 == 0:
                print(f"Processed {i}/{len(chunks)} chunks for {pdf_name}")

# Answer a question based on the embedded documents
def answer_question(question, k=5):
    # Get the embedding for the question
    question_embedding = get_embedding(question)
    
    # Perform KNN search to find similar chunks
    query = (
        Query(f"*=>[KNN {k} @embedding $vec AS vector_distance]")
        .sort_by("vector_distance")
        .return_fields("text", "source", "chunk_id", "vector_distance")
        .dialect(2)
    )
    
    results = redis_client.ft(INDEX_NAME).search(
        query, 
        query_params={"vec": np.array(question_embedding, dtype=np.float32).tobytes()}
    )
    
    # Format results for context
    context = ""
    for i, doc in enumerate(results.docs):
        context += f"Document {i+1} (from {doc.source}, chunk {doc.chunk_id}):\n{doc.text}\n\n"
    
    # Generate an answer using the retrieved context
    prompt = f"""
    Context information:
    {context}
    
    Question: {question}
    
    Answer the question based on the context provided above. If the answer is not in the context, give the answer and then state that the information is not available.
    """
    
    # Using Ollama to generate the answer
    response = ollama.chat(
        model="llama3.2",  # Or any other model you prefer
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    return response["message"]["content"]

if __name__ == "__main__":
    # Create the index
    create_hnsw_index()
    
    # Process PDFs in the specified folder
    pdf_folder = "./Notes"  # Replace with your folder path
    process_pdf_folder(pdf_folder)
    
    # Example usage of the question answering system
    while True:
        question = input("\nEnter your question (or 'exit' to quit): ")
        if question.lower() == 'exit':
            break
        
        answer = answer_question(question)
        print("\nAnswer:")
        print(answer)