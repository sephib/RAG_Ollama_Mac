import argparse
import shutil
from pathlib import Path

from dynaconf import Dynaconf
from tqdm import tqdm
from langchain.schema.document import Document
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from embedding import get_embedding_function

# Load settings
settings = Dynaconf(settings_files=[Path(__file__).parent / "settings.toml"])

# Get paths from configuration
project_root = Path.cwd()
DATA_PATH = project_root / settings.pdf_processing.input_folder
CHROMA_PATH = settings.pdf_processing.chroma_path


def load_documents():
    documents = []
    # Verify data path exists
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Input folder not found: {DATA_PATH}")

    # Get list of PDF files
    pdf_files = [f for f in DATA_PATH.iterdir() if f.suffix.lower() == ".pdf"]
    
    # Loop through all PDF files with progress bar
    for file_path in tqdm(pdf_files, desc="Loading PDF files", unit="file"):
        loader = PyPDFLoader(str(file_path))
        documents.extend(loader.load())
    
    print(f"✅ Loaded {len(documents)} pages from {len(pdf_files)} PDF files")
    return documents


def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.text_splitter.chunk_size,
        chunk_overlap=settings.text_splitter.chunk_overlap,
        length_function=len,
        is_separator_regex=settings.text_splitter.is_separator_regex,
    )
    
    print(f"📄 Splitting {len(documents)} pages into chunks...")
    chunks = text_splitter.split_documents(documents)
    print(f"✅ Created {len(chunks)} text chunks")
    return chunks


def add_to_db(chunks: list[Document]):
    # Load the existing database.
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function()
    )
    chunks_with_ids = calculate_chunk_ids(chunks)  # Giving each chunk an ID

    # Add or Update the documents.
    existing_items = db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Only add documents that don't exist in the DB.
    new_chunks = []
    for chunk in tqdm(chunks_with_ids, desc="Checking for new chunks", unit="chunk"):
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"👉 Adding {len(new_chunks)} new documents to database")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        
        # Add documents with progress bar for large batches
        if len(new_chunks) > 100:
            # Process in batches with progress bar
            batch_size = 100
            with tqdm(total=len(new_chunks), desc="Adding to database", unit="chunk") as pbar:
                for i in range(0, len(new_chunks), batch_size):
                    batch_chunks = new_chunks[i:i + batch_size]
                    batch_ids = new_chunk_ids[i:i + batch_size]
                    db.add_documents(batch_chunks, ids=batch_ids)
                    pbar.update(len(batch_chunks))
        else:
            db.add_documents(new_chunks, ids=new_chunk_ids)
        
        print("✅ Successfully added all new documents to database")
    else:
        print("✅ All documents are already in the database - nothing to add")


def calculate_chunk_ids(chunks):
    # This will create IDs like "data/monopoly.pdf:6:2"
    # Page Source : Page Number : Chunk Index

    last_page_id = None
    current_chunk_index = 0

    print("🔗 Generating unique IDs for chunks...")
    for chunk in tqdm(chunks, desc="Generating chunk IDs", unit="chunk"):
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Calculate the chunk ID.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the page meta-data.
        chunk.metadata["id"] = chunk_id

    return chunks


def clear_database():
    chroma_path = Path(CHROMA_PATH)
    if chroma_path.exists():
        shutil.rmtree(chroma_path)


def main():
    # Check if the database should be cleared (using the --clear flag).
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()
    if args.reset:
        print("✨ Clearing Database")
        clear_database()

    # Create (or update) the data store.
    documents = load_documents()
    chunks = split_documents(documents)
    add_to_db(chunks)


if __name__ == "__main__":
    main()
