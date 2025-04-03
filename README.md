# DS4300 RAG 

## Before you start:
* Download Ollama
* Run the following commands in your terminal to download necessary tools
```bash
ollama pull nomic-embed-text
ollama pull all-minilm:33m
ollama run deepseek-r1:7b
ollama run mistral
ollama pull paraphrase-multilingual
ollama pull llama3.2:latest
```

Download docker and docker compose and run the following command
```bash
docker run -d -p 6333:6333 qdrant/qdrant

docker run -d -p 6380:6379 redis/redis-stack

```

By this point, you should have all necessary applications to get started. You might also need to install python libraries.

When running, follow the error messages to install the packages.

## To run:

Redis.py
```
python redis.py

or 

python3 redis.py
```

Chroma.py
```
python chroma.py

or 

python3 chroma.py
```

qdrant.py
```
python chroma.py

or 

python3 chroma.py
```

## Things you might want to change:
1. Notes, you can delete all of the pdf files from Notes folder and add your own
2. Questions, delete the questions and add questions relavant to your topic
3. Embedding, LLM, Chunks, it is using all the possible combinations. This might take couple hours to 20 hours to process. Remove the embeddings, llm, chunk sizes (while keeping one) to make it faster. 

# Recommendation:

Although by our own intuition and a lot of data analysis, we recommend running 
```
python redis.py
``` 
after removing all but
```
nomic for Embedding

mistral for LLM
```

# Disclosure

Please note, this is our opinion on recommendation and does not discredit the experience of others. This is how we felt based on the data given by these LLM, embedding models, and the databases.


For further questions, reach out to 

```
pokhrel.sh@northeastern.edu
ding.jo@northeastern.edu
```
