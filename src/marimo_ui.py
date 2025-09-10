import marimo

__generated_with = "0.15.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    from rag_query import query_rag_with_sources
    return mo, query_rag_with_sources


@app.cell
def _(mo):
    mo.md("# 🧠 FactBot: No Hallucinations, Just Facts")
    return


@app.cell
def _(query_rag_with_sources):
    def format_sources(sources):
        """Format source information as markdown"""
        if not sources:
            return "\n\n*No sources found.*"
        
        sources_md = "\n\n---\n\n### 📚 Sources\n\n"
        
        for source in sources:
            citation = source["citation_number"]
            pdf_file = source["pdf_file"]
            page = source["page"]
            excerpt = source["excerpt"]
            score = source["score"]
            
            sources_md += f"**[{citation}]** 📄 **{pdf_file}** (Page {page})  \n"
            sources_md += f"*Relevance: {score}*  \n"
            sources_md += f"> {excerpt}\n\n"
        
        return sources_md
    
    def rag_model(messages, config):
        """
        Enhanced RAG model function with source citations.
        
        Args:
            messages: List of chat messages with .content and .role attributes
            config: Configuration options from the chat interface
            
        Returns:
            str: Response from the RAG system with source citations
        """
        if not messages:
            return "Hello! I'm ready to answer questions about your documents."
        
        # Get the latest user message
        user_message = messages[-1].content.strip()
        
        if not user_message:
            return "Please ask me a question about your documents."
        
        try:
            # Use enhanced RAG system with sources
            result = query_rag_with_sources(user_message)
            response = result["response"]
            sources = result["sources"]
            
            # Format response with source citations
            formatted_response = response
            
            # Add source information
            if sources:
                formatted_response += format_sources(sources)
            
            return formatted_response
            
        except Exception as e:
            return f"I'm sorry, I encountered an error while processing your question: {str(e)}\n\nPlease make sure:\n- Ollama is running\n- Documents are loaded in the vector database\n- The required models are available"
    
    return rag_model,


@app.cell
def _(mo, rag_model):
    # Create the native Marimo chat interface with enhanced prompts
    chat = mo.ui.chat(
        rag_model,
        prompts=[
            "What is this document about?",
            "Summarize the key points from the documents.",
            "What are the main topics covered?",
            "Can you explain the most important concepts?",
            "What specific evidence supports this topic?"
        ],
        show_configuration_controls=True,
        allow_attachments=False
    )
    return chat,


@app.cell
def _(chat):
    # Display the chat interface
    chat
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## About FactBot
        
        This RAG chatbot uses your local documents to provide accurate, context-aware responses.
        
        **Features:**
        - 🔒 **Private**: All processing happens locally
        - 📚 **Document-based**: Answers based on your uploaded PDFs
        - 🧠 **Powered by Ollama**: Using local LLMs for inference
        - 🎯 **Reactive**: Built with Marimo's native chat interface
        
        **How it works:**
        1. Your documents are embedded into a vector database
        2. When you ask a question, relevant chunks are retrieved  
        3. The LLM uses this context to generate accurate responses
        
        **Getting Started:**
        - Click one of the suggested prompts above
        - Or type your own question in the chat input
        - Make sure Ollama is running and documents are loaded
        
        **To add documents:** Configure the input folder in `src/settings.toml` and run:
        ```bash
        # Standard loading
        uv run src/load_docs.py
        
        # Apple Silicon optimized loading
        uv run src/load_docs_mps.py
        ```
        
        **Configuration:** Edit `src/settings.toml` to customize:
        - Input PDF folder path
        - ChromaDB storage location  
        - Performance settings for Apple Silicon
        """
    )
    return


if __name__ == "__main__":
    app.run()