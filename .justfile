run:
    uv run streamlit run ./src/UI.py

doc-load:
    uv run python ./src/load_docs.py

doc-reset:
    uv run python ./src/load_docs.py --reset

