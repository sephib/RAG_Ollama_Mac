run:
    uv run marimo edit --watch src/marimo_ui.py

run-streamlit:
    uv run streamlit run ./src/UI.py

# update settings for changing 
doc-load:
    uv run python src/load_docs_mps.py 

# uv run python ./src/load_docs.py

doc-reset:
    uv run python src/load_docs.py --reset

