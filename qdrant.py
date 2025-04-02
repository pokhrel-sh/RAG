import os
from pathlib import Path
import numpy as np
import ollama
import PyPDF2
import time
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, CollectionStatus, PointStruct

client = QdrantClient(host="localhost", port=6333)

DOC_PREFIX = "doc:"
DISTANCE_METRIC = Distance.COSINE

# Embedding models, LLMs, and chunk sizes
embedding_models = ["paraphrase-multilingual", "nomic-embed-text", "all-minilm:33m"]
llm_models = ["deepseek-r1:latest", "llama3.2", "mistral"]
chunk_sizes = [100, 250, 500]
questions = ["What are pros and cons of different data structures for storing and searching values?", 
             "What is a right-left rotation for an AVL tree? Give an example of an unbalanced AVL tree that can be balanced using a right-left rotation.", 
             "Generally, explain the process for creating a B+ tree. Given the set of numbers [48, 65, 91, 90, 14, 13, 87, 74, 51, 92, 41, 70, 47, 64, 38, 29, 50, 21], create a B+ tree with node size = 3 by inserting the numbers in the given order.",
             "How are ACID compliance and the CAP theorem related?",
             "Tell me what you know about Redis. How do you connect to Redis?",
             "Give examples of comparison operators in MongoDB and what they do. Given the mflix database, write a query to find the average number of imdb votes per year for movies released between 1970 and 2000 (inclusive)? Make sure the results are ordered by year.",
             "Tell me about Mark Fontenot."   
             ]


# generates the embedding and dimensions for the embedding
def get_embedding_and_dimensions(text, model):
    response = ollama.embeddings(model=model, prompt=text)
    embedding = response["embedding"]
    return embedding, len(embedding)

# creates the index in qdrant
def create_indices():
    sample_text = "This is a sample text to determine embedding dimensions."
    model_dimensions = {}

    for model in embedding_models:
        _, dim = get_embedding_and_dimensions(sample_text, model)
        model_dimensions[model] = dim

        collection_name = model.replace('-', '_').replace(':', '_')
        
        existing_collections = client.get_collections().collections
        if any(c.name == collection_name for c in existing_collections):
            client.delete_collection(collection_name)
        
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dim, distance=DISTANCE_METRIC)
        )

# store the calculated embedding in qdrant
def store_embedding(model, doc_id, text, source, chunk_id, chunk_size, embedding):
    collection_name = model.replace('-', '_').replace(':', '_')
    client.upsert(
        collection_name=collection_name,
        points=[
            PointStruct(
                id=doc_id,
                vector=embedding,
                payload={
                    "text": text,
                    "source": source,
                    "chunk_id": chunk_id,
                    "chunk_size": chunk_size
                }
            )
        ]
    )

#extracts text from pdf using pypdf2
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = "".join([page.extract_text() + " " for page in pdf_reader.pages])
    return text

# creates a chunks of the texts with overlaps (half of chunks)
def chunk_text(text, chunk_size=100):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size // 2):
        chunk_end = min(i + chunk_size, len(words))
        chunks.append(" ".join(words[i:chunk_end]))
    return chunks

# Ggenerates an answer to the question based on the embedding model, chunk size, and llm models
def answer_question(question, embedding_model, chunk_size, llm_model, k=5):
    question_embedding, _ = get_embedding_and_dimensions(question, embedding_model)
    collection_name = embedding_model.replace('-', '_').replace(':', '_')
    
    search_results = client.query_points(
        collection_name=collection_name,
        query=question_embedding,
        limit=k,
        with_payload=True
    ).points
    
    context = "\n".join([hit.payload["text"] for hit in search_results if hit.payload["chunk_size"] == chunk_size])
    
    prompt = f"""
    Context information:
    {context}
    
    Question: {question}
    
    Answer based on the context. If the answer is unavailable, state it clearly.
    """
    
    response = ollama.chat(
        model=llm_model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response["message"]["content"]

# Processes all pdf files, chunks them, generates embedding and stores the embedding
def process_pdf_files(folder_path):
    pdf_files = list(Path(folder_path).glob('*.pdf'))
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return
    
    doc_id_counter = 0
    for embedding_model in embedding_models:
        for pdf_file in pdf_files:
            pdf_name = os.path.basename(str(pdf_file))
            text = extract_text_from_pdf(str(pdf_file))
            
            for chunk_size in chunk_sizes:
                chunks = chunk_text(text, chunk_size)
                print(f"Model: {embedding_model}, Chunk size {chunk_size}: {len(chunks)} chunks from {pdf_name}")
                
                for i, chunk in enumerate(chunks):
                    embedding, _ = get_embedding_and_dimensions(chunk, embedding_model)
                    chunk_id = f"{pdf_name}_{i}_{chunk_size}"
                    store_embedding(
                        model=embedding_model,
                        doc_id=doc_id_counter,
                        text=chunk,
                        source=pdf_name,
                        chunk_id=chunk_id,
                        chunk_size=chunk_size,
                        embedding=embedding
                    )
                    doc_id_counter += 1

# Iterates over embedding, llm, and chunk size to answer all question for all combination for qdrant
def all_combinations_question_answers(log_file="processed_data.txt"):
    with open(log_file, "w", encoding="utf-8") as log:
        for embedding_model in embedding_models:
            print(f"Using embedding model: {embedding_model}")
            for llm_model in llm_models:
                print(f"Using LLM model: {llm_model}")
                for chunk_size in chunk_sizes:
                    print(f"Using chunk size: {chunk_size}")
                    for question in questions:
                        print(f"Answering question: {question[:50]}...")
                        try:
                            answer = answer_question(
                                question=question,
                                embedding_model=embedding_model,
                                chunk_size=chunk_size,
                                llm_model=llm_model
                            )
                            log.write(f"\nEmbedding: {embedding_model}\nLLM: {llm_model}\nChunk size: {chunk_size}\n")
                            log.write(f"Question: {question}\nAnswer: {answer}\n")
                            print(f"✓ Answered question: {question[:50]}...")
                        except Exception as e:
                            print(f"Error processing: {e}")
                            log.write(f"Error for question: {question}\n")
                            log.write(f"Error: {str(e)}\n")


# main method
def main():
    try:
        create_indices()
        process_pdf_files("./Notes")
        all_combinations_question_answers()
    except Exception as e:
        print(f"Main execution failed with error: {str(e)}")

if __name__ == "__main__":
    main()