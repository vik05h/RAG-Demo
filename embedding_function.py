from langchain_ollama import OllamaEmbeddings

def embedding_function():
    embeddings = OllamaEmbeddings(
    model="finellama",)
    return embeddings
