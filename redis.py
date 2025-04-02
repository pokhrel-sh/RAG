import os
from pathlib import Path
import numpy as np
import redis
from redis.commands.search.query import Query
import ollama
import PyPDF2
import time

# Initialize Redis connection
redis_client = redis.Redis(host="localhost", port=6380, db=0)
DOC_PREFIX = "doc:"
DISTANCE_METRIC = "COSINE"

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

embedding_indices = {}

# generates the embedding and dimensions for embedding
def get_embedding_and_dimensions(text, model):
    response = ollama.embeddings(model=model, prompt=text)
    embedding = response["embedding"]
    return embedding, len(embedding)

# creats index for each embedding model in Redis
def create_indices():
    sample_text = "This is a sample text to determine embedding dimensions."
    model_dimensions = {}
    
    for model in embedding_models:
        _, dim = get_embedding_and_dimensions(sample_text, model)
        model_dimensions[model] = dim
        
        model_name = model.replace('-', '_').replace(':', '_')
        index_name = f"embedding_{model_name}"
        embedding_indices[model] = index_name
        
        try:
            redis_client.execute_command(f"FT.DROPINDEX {index_name} DD")
        except redis.exceptions.ResponseError:
            pass
            
        redis_client.execute_command(
            f"""
            FT.CREATE {index_name} ON HASH PREFIX 1 {DOC_PREFIX}{model_safe_name}_
            SCHEMA 
                text TEXT 
                source TEXT
                chunk_id TEXT
                chunk_size TAG
                embedding VECTOR HNSW 6 DIM {dim} TYPE FLOAT32 DISTANCE_METRIC {DISTANCE_METRIC}
            """
        )
        print(f"Index {index_name} created successfully with dimension {dim}")

# Store the calculated embedding in Redis
def store_embedding(model, doc_id, text, source, chunk_id, chunk_size, embedding):
    model_safe_name = model.replace('-', '_').replace(':', '_')
    key = f"{DOC_PREFIX}{model_safe_name}_{doc_id}"
    redis_client.hset(
        key,
        mapping={
            "text": text,
            "source": source,
            "chunk_id": chunk_id,
            "chunk_size": str(chunk_size),
            "embedding": np.array(embedding, dtype=np.float32).tobytes(),
        },
    )

# extracts text from pdf using pypdf2
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
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

# Ggenerates an answer to the question based on the embedding model, chunk size, and llm models
def answer_question(question, embedding_model, chunk_size, llm_model, k=5):
    question_embedding, _ = get_embedding_and_dimensions(question, embedding_model)
    
    index_name = embedding_indices[embedding_model]
    
    query = (
        Query(f"*=>[KNN {k} @embedding $vec AS vector_distance]")
        .sort_by("vector_distance")
        .return_fields("text", "source", "chunk_id", "vector_distance", "chunk_size")
        .dialect(2)
    )
    
    results = redis_client.ft(index_name).search(
        query, query_params={"vec": np.array(question_embedding, dtype=np.float32).tobytes()}
    )
    
    filtered_docs = [doc for doc in results.docs if doc.chunk_size == str(chunk_size)]
    
    context = "\n".join([f"{doc.text}" for doc in filtered_docs[:k]])
    
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

# Remove the check for 'os' within the function, since it's already imported at the top.
def process_pdf_files(folder_path):
    pdf_files = list(Path(folder_path).glob('*.pdf'))
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return
    
    for embedding_model in embedding_models:
        doc_id_counter = 0
    
        for pdf_file in pdf_files:
            pdf_name = os.path.basename(str(pdf_file))
            text = extract_text_from_pdf(str(pdf_file))
            
            for chunk_size in chunk_sizes:
                chunks = chunk_text(text, chunk_size)
                
                for i, chunk in enumerate(chunks):
                    embedding, _ = get_embedding_and_dimensions(chunk, embedding_model)
                    chunk_id = f"{pdf_name}_{i}_{chunk_size}"
                    
                    store_embedding(
                        model=embedding_model,
                        doc_id=str(doc_id_counter),
                        text=chunk,
                        source=pdf_name,
                        chunk_id=chunk_id,
                        chunk_size=chunk_size,
                        embedding=embedding
                    )
                    doc_id_counter += 1


# Iterates over embedding, llm, and chunk size to answer all question for all combination for Redis
def all_combinations_question_answers(log_file="processed_data.txt"):
    with open(log_file, "w", encoding="utf-8") as log:
        for embedding_model in embedding_models:
            for llm_model in llm_models:
                for chunk_size in chunk_sizes:
                    for question in questions:
                        start_time = time.time()
                        
                        try:
                            answer = answer_question(
                                question=question,
                                embedding_model=embedding_model,
                                chunk_size=chunk_size,
                                llm_model=llm_model
                            )
                            
                            #was planning to use this but scrapped after
                            end_time = time.time()
                            
                            total_time = end_time - start_time
                            #writes the result in file                            
                            log.write(f"\nLLM\n{llm_model}\n")
                            log.write(f"Embedding\n{embedding_model}\n")
                            log.write(f"Chunk Sizes\n{chunk_size}\n\n")
                            log.write(f"Question\n{question}\n\n")
                            log.write(f"Answer\n{answer}\n")
                            
                            print(f"✓ Answered question with {embedding_model} + {llm_model} + {chunk_size} in {total_time:.4f} seconds")
                        except Exception as e:
                            end_time = time.time()
                            total_time = end_time - start_time
                            
                            print(f"Error processing: {e}")
                            log.write(f"\nLLM\n{llm_model}\n")
                            log.write(f"Embedding\n{embedding_model}\n")
                            log.write(f"Chunk Sizes\n{chunk_size}\n\n")
                            log.write(f"Question\n{question}\n\n")
                            log.write(f"Answer\nError: {str(e)}\n")


def main():
    try:
        create_indices()
        process_pdf_files("./Notes")
        all_combinations_question_answers()
    except Exception as e:
        print(f"Main execution failed with error: {str(e)}")


if __name__ == "__main__":
    main()