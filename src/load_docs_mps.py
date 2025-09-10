import argparse
import shutil
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List

from dynaconf import Dynaconf
from langchain.schema.document import Document
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

try:
    import torch

    HAS_TORCH = True
    # Check for Apple Silicon MPS availability
    if torch.backends.mps.is_available():
        DEVICE = torch.device("mps")
        print("🚀 Apple Silicon Neural Engine (MPS) detected and enabled")
    else:
        DEVICE = torch.device("cpu")
        print("💻 Using CPU processing")
except ImportError:
    HAS_TORCH = False
    DEVICE = None
    print("💻 Using CPU processing (PyTorch not available)")

from embedding import get_embedding_function

# Load settings
settings = Dynaconf(settings_files=[Path(__file__).parent / "settings.toml"])

# Get paths from configuration
project_root = Path.cwd()
DATA_PATH = project_root / settings.pdf_processing.input_folder
CHROMA_PATH = settings.pdf_processing.chroma_path

# Apple Silicon optimized settings
BATCH_SIZE = getattr(settings.performance, "batch_size", 50)
MAX_WORKERS = getattr(settings.performance, "max_workers", min(mp.cpu_count(), 8))
USE_MPS = (
    getattr(settings.performance, "use_mps", True)
    and HAS_TORCH
    and torch.backends.mps.is_available()
)


def load_single_pdf(pdf_path: Path) -> List[Document]:
    """Load a single PDF file - optimized for multiprocessing"""
    try:
        loader = PyPDFLoader(str(pdf_path))
        documents = loader.load()
        return documents
    except Exception as e:
        print(f"⚠️  Error loading {pdf_path.name}: {e}")
        return []


def load_documents_parallel():
    """Load documents using multiprocessing for Apple Silicon optimization"""
    documents = []

    # Verify data path exists
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Input folder not found: {DATA_PATH}")

    # Get list of PDF files
    pdf_files = [f for f in DATA_PATH.iterdir() if f.suffix.lower() == ".pdf"]

    if not pdf_files:
        print("⚠️  No PDF files found in the input folder")
        return documents

    print(f"📚 Found {len(pdf_files)} PDF files to process")
    print(f"🔧 Using {MAX_WORKERS} processes for parallel loading")

    # Process PDFs in parallel
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all PDF loading tasks
        future_to_pdf = {
            executor.submit(load_single_pdf, pdf_path): pdf_path
            for pdf_path in pdf_files
        }

        # Collect results with progress bar
        with tqdm(total=len(pdf_files), desc="Loading PDF files", unit="file") as pbar:
            for future in as_completed(future_to_pdf):
                pdf_path = future_to_pdf[future]
                try:
                    pdf_documents = future.result()
                    documents.extend(pdf_documents)
                    pbar.set_postfix({"Current": pdf_path.name})
                except Exception as e:
                    print(f"❌ Failed to process {pdf_path.name}: {e}")
                pbar.update(1)

    print(f"✅ Loaded {len(documents)} pages from {len(pdf_files)} PDF files")
    return documents


def split_documents_optimized(documents: List[Document]):
    """Split documents with Apple Silicon memory optimization"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.text_splitter.chunk_size,
        chunk_overlap=settings.text_splitter.chunk_overlap,
        length_function=len,
        is_separator_regex=settings.text_splitter.is_separator_regex,
    )

    print(f"📄 Splitting {len(documents)} pages into chunks...")

    # Process in batches to optimize memory usage on Apple Silicon
    all_chunks = []
    batch_size = BATCH_SIZE

    with tqdm(total=len(documents), desc="Splitting documents", unit="page") as pbar:
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            batch_chunks = text_splitter.split_documents(batch)
            all_chunks.extend(batch_chunks)
            pbar.update(len(batch))

    print(f"✅ Created {len(all_chunks)} text chunks")
    return all_chunks


def calculate_chunk_ids_parallel(chunks):
    """Generate chunk IDs with optimized processing"""
    last_page_id = None
    current_chunk_index = 0

    print("🔗 Generating unique IDs for chunks...")

    # Use tqdm for progress tracking
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


def add_to_db_optimized(chunks: List[Document]):
    """Add documents to database with Apple Silicon optimizations"""
    # Load the existing database.
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function()
    )
    chunks_with_ids = calculate_chunk_ids_parallel(chunks)

    # Add or Update the documents.
    existing_items = db.get(include=[])
    existing_ids = set(existing_items["ids"])
    print(f"📊 Number of existing documents in DB: {len(existing_ids)}")

    # Only add documents that don't exist in the DB.
    new_chunks = []
    for chunk in tqdm(chunks_with_ids, desc="Checking for new chunks", unit="chunk"):
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"👉 Adding {len(new_chunks)} new documents to database")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]

        # Optimized batch processing for Apple Silicon
        optimal_batch_size = min(BATCH_SIZE, 400)  # Limit for memory efficiency

        if len(new_chunks) > optimal_batch_size:
            print(
                f"🔄 Processing in batches of {optimal_batch_size} for optimal performance"
            )
            with tqdm(
                total=len(new_chunks), desc="Adding to database", unit="chunk"
            ) as pbar:
                for i in range(0, len(new_chunks), optimal_batch_size):
                    batch_chunks = new_chunks[i : i + optimal_batch_size]
                    batch_ids = new_chunk_ids[i : i + optimal_batch_size]

                    db.add_documents(batch_chunks, ids=batch_ids)
                    pbar.update(len(batch_chunks))
        else:
            db.add_documents(new_chunks, ids=new_chunk_ids)

        print("✅ Successfully added all new documents to database")
    else:
        print("✅ All documents are already in the database - nothing to add")


def clear_database():
    """Clear the vector database"""
    chroma_path = Path(CHROMA_PATH)
    if chroma_path.exists():
        shutil.rmtree(chroma_path)


def print_system_info():
    """Print Apple Silicon optimization information"""
    print("🍎 Apple Silicon Optimization Status:")
    print(f"   CPU Cores Available: {mp.cpu_count()}")
    print(f"   Max Workers: {MAX_WORKERS}")
    print(f"   Batch Size: {BATCH_SIZE}")

    if HAS_TORCH:
        print(f"   PyTorch Available: ✅")
        if torch.backends.mps.is_available():
            print(
                f"   MPS (Neural Engine): {'✅ Enabled' if USE_MPS else '❌ Disabled'}"
            )
        else:
            print(f"   MPS (Neural Engine): ❌ Not Available")
    else:
        print(f"   PyTorch Available: ❌")


def main():
    # Print system optimization info
    print_system_info()
    print()

    # Check if the database should be cleared (using the --reset flag).
    parser = argparse.ArgumentParser(
        description="Load documents with Apple Silicon optimizations"
    )
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()

    if args.reset:
        print("✨ Clearing Database")
        clear_database()

    # Create (or update) the data store with optimizations.
    print("🚀 Starting optimized document loading...")
    documents = load_documents_parallel()

    if not documents:
        print("⚠️  No documents loaded. Exiting.")
        return

    chunks = split_documents_optimized(documents)
    add_to_db_optimized(chunks)

    print("🎉 Document loading completed successfully!")


if __name__ == "__main__":
    main()
