import argparse
import re
from pathlib import Path

from dynaconf import Dynaconf
from langchain.prompts import ChatPromptTemplate
from langchain_chroma import Chroma  # Updated import for Chroma
from langchain_ollama import OllamaLLM  # Updated import for Ollama

from embedding import get_embedding_function

# Load settings
settings = Dynaconf(
    settings_files=[Path(__file__).parent / "settings.toml"]
)

CHROMA_PATH = settings.pdf_processing.chroma_path


def main():
    # Create CLI.
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_text = args.query_text
    query_rag(query_text)


def remove_think_tags(response):
    return re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)


def query_rag_with_sources(query: str):
    """Enhanced RAG query that returns both response and detailed source information"""
    # Prepare the DB.
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    search_count = settings.get('rag.search_count', 5)
    results = db.similarity_search_with_score(query, k=search_count)

    context = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template_text = settings.get('rag.prompt_template', """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context in a brief: {question}
""")
    prompt_template = ChatPromptTemplate.from_template(prompt_template_text)
    prompt = prompt_template.format(context=context, question=query)

    # model = OllamaLLM(model="mistral")
    model_name = settings.get('rag.model', 'gemma3n:latest')
    model = OllamaLLM(model=model_name)
    # model = OllamaLLM(model="gemma3n:e4b")
    # model = OllamaLLM(model="llama3")
    response_text = model.invoke(prompt)
    response = remove_think_tags(response_text)

    # Extract detailed source information
    sources = []
    for i, (doc, score) in enumerate(results, 1):
        source_id = doc.metadata.get("id", "Unknown")
        
        # Parse source ID: "data/renamed_pdfs/filename.pdf:page:chunk"
        pdf_file = "Unknown"
        page_num = "Unknown"
        chunk_num = "Unknown"
        
        if source_id and ":" in source_id:
            parts = source_id.split(":")
            if len(parts) >= 3:
                pdf_path = parts[0]
                pdf_file = Path(pdf_path).name if pdf_path != "Unknown" else "Unknown"
                page_num = parts[1]
                chunk_num = parts[2]
        
        # Get excerpt (first 150 characters)
        excerpt = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
        
        sources.append({
            "citation_number": i,
            "pdf_file": pdf_file,
            "page": page_num,
            "chunk": chunk_num,
            "excerpt": excerpt,
            "score": round(float(score), 3),
            "full_id": source_id
        })
    
    return {
        "response": response,
        "sources": sources
    }


def query_rag(query: str):
    """Original RAG query function - maintained for backward compatibility"""
    result = query_rag_with_sources(query)
    
    # Print formatted response for CLI usage
    sources_list = [source["full_id"] for source in result["sources"]]
    formatted_response = f"Response: {result['response']}\nSources: {sources_list}"
    print(formatted_response)
    
    return result["response"]


if __name__ == "__main__":
    main()
