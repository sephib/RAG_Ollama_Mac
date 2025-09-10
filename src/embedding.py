from langchain_ollama import OllamaEmbeddings


def get_embedding_function():
    """embeddings = BedrockEmbeddings(
        credentials_profile_name="default", region_name="us-east-1"
    )
    """
    embeddings = OllamaEmbeddings(model="toshk0/nomic-embed-text-v2-moe:Q6_K")
    # embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    return embeddings
