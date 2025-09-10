run:
    uv run marimo edit --watch src/marimo_ui.py

run-streamlit:
    uv run streamlit run ./src/UI.py

# Load documents into vector database
doc-load:
    uv run python src/load_docs.py 

# Reset and reload documents
doc-reset:
    uv run python src/load_docs.py --reset

