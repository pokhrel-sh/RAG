import os
from pathlib import Path
import numpy as np
import chromadb
import ollama
import PyPDF2
from typing import List, Dict, Any

DISTANCE_METRIC = "cosine"

embedding_models = ["paraphrase-multilingual", "nomic-embed-text", "all-minilm:33m"]
llm_models = ["deepseek-r1:latest", "llama3.2", "mistral"]
chunk_sizes = [100, 250, 500]  
questions = [
    "What are pros and cons of different data structures for storing and searching values?", 
    "What is a right-left rotation for an AVL tree? Give an example of an unbalanced AVL tree that can be balanced using a right-left rotation.", 
    "Generally, explain the process for creating a B+ tree. Given the set of numbers [48, 65, 91, 90, 14, 13, 87, 74, 51, 92, 41, 70, 47, 64, 38, 29, 50, 21], create a B+ tree with node size = 3 by inserting the numbers in the given order.",
    "How are ACID compliance and the CAP theorem related?",
    "Tell me what you know about Redis. How do you connect to Redis?",
    "Give examples of comparison operators in MongoDB and what they do. Given the mflix database, write a query to find the average number of imdb votes per year for movies released between 1970 and 2000 (inclusive)? Make sure the results are ordered by year.",
    "Tell me about Mark Fontenot."   
]

client = None
collections = {}
model_dimensions = {}

# generates a collectio name given model and size
def get_collection_name(model, chunk_size):
    model_safe_name = model.replace('-', '_').replace(':', '_')
    return f"{model_safe_name}_{chunk_size}"

# generates the embedding and dimensions for embedding
def get_embedding_and_dimensions(text, model):
    response = ollama.embeddings(model=model, prompt=text)
    embedding = response["embedding"]
    return embedding, len(embedding)

# initializes the vector store by creating collection for each embedding model and chunk size
def initialize_vector_store(dictionary = "./chroma_db"):
    global client, collections, model_dimensions
    
    client = chromadb.PersistentClient(path=dictionary)
    
    sample_text = "This is a sample text to determine embedding dimensions."
    
    for model in embedding_models:
        embedding, dim = get_embedding_and_dimensions(sample_text, model)
        model_dimensions[model] = dim
        
        for chunk_size in chunk_sizes:
            collection_name = get_collection_name(model, chunk_size)
            
            try:
                client.delete_collection(collection_name)
            except:
                pass
            
            collection = client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": DISTANCE_METRIC},
                embedding_function=None 
            )
            
            collections[(model, chunk_size)] = collection

# add document to the collection based on embedding and chunk size
def add_document(model, chunk_size, text, 
                source, chunk_id, embedding):
    """Add a document chunk to the appropriate collection"""
    global collections
    
    collection = collections.get((model, chunk_size))
    if not collection:
        raise ValueError(f"Collection for {model} and chunk size {chunk_size} not initialized")
    
    collection.add(
        ids=[chunk_id],
        embeddings=[embedding],
        metadatas=[{
            "source": source,
            "chunk_size": chunk_size,
            "chunk_id": chunk_id
        }],
        documents=[text]
    )

# queries the data to store the topk 
def query_vector_store(model, chunk_size, query_embedding, k= 5):
    global collections
    
    collection = collections.get((model, chunk_size))
    if not collection:
        raise ValueError(f"Collection for {model} and chunk size {chunk_size} not initialized")
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    
    formatted_results = []
    for i in range(len(results["ids"][0])):
        formatted_results.append({
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "chunk_id": results["metadatas"][0][i]["chunk_id"],
            "chunk_size": str(results["metadatas"][0][i]["chunk_size"]),
            "vector_distance": results["distances"][0][i]
        })
    
    return formatted_results

# extracts text from pdf using pypdf2
def extract_text_from_pdf(pdf_path: str) -> str:
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = "".join([page.extract_text() + " " for page in pdf_reader.pages])
    return text

# creates a chunks of the texts with overlaps (half of chunks)
def chunk_text(text, chunk_size = 100):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size // 2): 
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

# Remove the check for 'os' within the function, since it's already imported at the top.
def process_pdf_files(folder_path):
    pdf_files = list(Path(folder_path).glob('*.pdf'))
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return
    
    for embedding_model in embedding_models:
        for pdf_file in pdf_files:
            pdf_name = os.path.basename(str(pdf_file))
            text = extract_text_from_pdf(str(pdf_file))
            
            for chunk_size in chunk_sizes:
                chunks = chunk_text(text, chunk_size)                
                for i, chunk in enumerate(chunks):
                    embedding, _ = get_embedding_and_dimensions(chunk, embedding_model)
                    chunk_id = f"{pdf_name}_{i}_{chunk_size}"
                    
                    add_document(
                        model=embedding_model,
                        chunk_size=chunk_size,
                        text=chunk,
                        source=pdf_name,
                        chunk_id=chunk_id,
                        embedding=embedding
                    )
# Ggenerates an answer to the question based on the embedding model, chunk size, and llm models
def answer_question(question: str, embedding_model: str, chunk_size: int, llm_model: str, k: int = 5) -> str:
    question_embedding, _ = get_embedding_and_dimensions(question, embedding_model)
    
    results = query_vector_store(
        model=embedding_model,
        chunk_size=chunk_size,
        query_embedding=question_embedding,
        k=k
    )
    
    context = "\n".join([doc["text"] for doc in results])
    
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

# Iterates over embedding, llm, and chunk size to answer all question for all combination for Redis
def all_combinations_question_answers(log_file: str = "processed_data.txt"):
    with open(log_file, "w", encoding="utf-8") as log:
        for embedding_model in embedding_models:
            
            for llm_model in llm_models:
                
                for chunk_size in chunk_sizes:
                    
                    for question in questions:
                        
                        try:
                            answer = answer_question(
                                question=question,
                                embedding_model=embedding_model,
                                chunk_size=chunk_size,
                                llm_model=llm_model
                            )
                            # writes the result in the file
                            log.write(f"\nLLM\n{llm_model}\n")
                            log.write(f"Embedding\n{embedding_model}\n")
                            log.write(f"Chunk Sizes\n{chunk_size}\n\n")
                            log.write(f"Question\n{question}\n\n")
                            log.write(f"Answer\n{answer}\n")
                            
                        except Exception as e:
                            print(f"Error processing: {e}")
                            log.write(f"\nLLM\n{llm_model}\n")
                            log.write(f"Embedding\n{embedding_model}\n")
                            log.write(f"Chunk Sizes\n{chunk_size}\n\n")
                            log.write(f"Question\n{question}\n\n")
                            log.write(f"Answer\nError: {str(e)}\n")

def main():
    try:
        initialize_vector_store()
        process_pdf_files("./Notes")
        all_combinations_question_answers()
        
    except Exception as e:
        print(f"Main execution failed with error: {str(e)}")

if __name__ == "__main__":
    main()