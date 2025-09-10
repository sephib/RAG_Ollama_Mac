from pathlib import Path

from dynaconf import Dynaconf
from langchain_ollama import OllamaEmbeddings

# Load settings
settings = Dynaconf(settings_files=[Path(__file__).parent / "settings.toml"])


def get_embedding_function():
    """embeddings = BedrockEmbeddings(
        credentials_profile_name="default", region_name="us-east-1"
    )
    """
    model_name = settings.get('embedding.model', 'toshk0/nomic-embed-text-v2-moe:Q6_K')
    embeddings = OllamaEmbeddings(model=model_name)
    # embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    return embeddings
