# 🧠 Local RAG Chatbot with Ollama on Mac

> Lightweight, private, and customizable retrieval-augmented chatbot running entirely on your Mac.

Based on the excellent work by [pruthvirajcyn](https://github.com/pruthvirajcyn/RAG_Ollama_Deepseek_Streamlit) and his [Medium article](https://medium.com/@pruthvirajc/implementing-a-local-rag-chat-bot-with-ollama-streamlit-and-deepseek-r1-a-practical-guide-46b1903f011f).

---

## ⚙️ About This Project

This is a modern implementation of a local RAG (Retrieval-Augmented Generation) chatbot using:

- [Ollama](https://ollama.com/) for running open-source LLMs and embedding models locally
- [Marimo](https://marimo.io/) for an interactive, reactive notebook-style UI (primary interface)
- [Streamlit](https://streamlit.io/) for an alternative chat UI
- [ChromaDB](https://www.trychroma.com/) for storing and querying vector embeddings
- [UV](https://github.com/astral-sh/uv) for fast, reliable Python package management

**Default Configuration:**
- 🔍 Embedding model: `toshk0/nomic-embed-text-v2-moe:Q6_K`
- 🧠 LLM: `gemma3n:latest`
- ⚡ Optimized for Apple Silicon with fallback for other systems

---

## 💡 Why Run a RAG Locally?

- **🔒 Privacy**: No data is sent to the cloud. Upload and query your documents entirely offline.
- **💸 Cost-effective**: No API tokens or cloud GPU costs. You only pay electricity.
- **📚 Better than summarizing**: With long PDFs or multiple documents, even summaries may not contain the context you need. A RAG chatbot can drill deeper and provide contextual answers.

> ✅ Recommended: At least **16GB of RAM** on your Mac. Preferably 24GB+ for smoother experience.

---

## 🛠️ 1. Installation

### Prerequisites

- **Python 3.8+** 
- **UV package manager** - Install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **At least 16GB RAM** (24GB+ recommended for best performance)

### 1. Clone the Repository

```bash
git clone https://github.com/sephib/RAG_Ollama_Mac.git
cd RAG_Ollama_Mac
```

### 2. Install Dependencies with UV

UV will automatically handle virtual environment creation and dependency installation:

```bash
uv sync
```

This command will:
- Create a virtual environment automatically
- Install all required dependencies
- Set up the project for immediate use

---

## 🚀 2. Quick Start

### 1. Configure Settings (Important!)

Edit `src/settings.toml` to customize your setup:

```toml
[pdf_processing]
# Update these paths for your documents
input_folder = "data/renamed_pdfs"  # Change to your PDF folder
chroma_path = "data/chroma_renamed_pdfs"

[embedding]
# Choose your embedding model
model = "toshk0/nomic-embed-text-v2-moe:Q6_K"

[rag]
# Configure your LLM and search parameters
model = "gemma3n:latest"
search_count = 5

[performance]
# Optimize for your hardware
batch_size = 400          # Lower for less RAM
max_workers = 8          # Adjust for your CPU cores
use_mps = true           # Enable on Apple Silicon
```

### 2. Start Ollama and Pull Models

```bash
# Start Ollama service
ollama serve

# Pull the default models (or customize in settings.toml first)
ollama pull gemma3n:latest
ollama pull toshk0/nomic-embed-text-v2-moe:Q6_K
```

### 3. Load Your Documents

Place your `.pdf` files in the folder specified in `settings.toml` (default: `data/renamed_pdfs/`), then:

```bash
# Load documents with Apple Silicon optimizations
uv run src/load_docs.py

# Or reset and reload everything
uv run src/load_docs.py --reset
```

### 4. Launch the Interface

**Option A: Marimo (Recommended - Interactive Notebook Style)**
```bash
uv run marimo edit --watch src/marimo_ui.py
```

**Option B: Streamlit (Traditional Chat UI)**
```bash
uv run streamlit run src/UI.py
```

### 5. Start Chatting!

Ask questions and the chatbot will respond using relevant context from your documents with source citations.

---

## 🧩 3. Customization

All configuration is centralized in `src/settings.toml` - no code changes needed!

### **✏️ Modify Prompts**
```toml
[rag]
prompt_template = """
Your custom prompt here with {context} and {question} placeholders.
"""
```

### **🔄 Try Different Models**
```toml
[embedding]
model = "mxbai-embed-large"  # Alternative embedding model

[rag]
model = "llama3.2"           # Alternative LLM
```

### **⚙️ Tune Performance**
```toml
[text_splitter]
chunk_size = 1000     # Larger chunks for more context
chunk_overlap = 100   # More overlap for better continuity

[rag]
search_count = 10     # Retrieve more documents

[performance]
batch_size = 200      # Lower for less RAM usage
max_workers = 4       # Adjust for your CPU
```

### **🚀 Extend Functionality**
- **Marimo**: Interactive reactive notebooks with built-in chat
- **Streamlit**: Traditional web app interface
- **Just Commands**: Use `just doc-load` and `just doc-reset` for convenience

---

## 🛠️ 4. Utility Scripts

The project includes helpful scripts for document management:

### **📄 PDF File Renamer**

**Location:** `scripts/update_pdf_file_names.py`

Automatically renames PDF files based on their extracted titles - perfect for organizing research papers and documents with cryptic filenames.

**Features:**
- 🧠 **Smart Title Extraction**: Uses font analysis, positioning, and OCR
- 🌍 **Multi-language Support**: Detects and translates Hebrew titles to English  
- 📊 **Confidence Scoring**: Rates extraction quality and methods used
- 📝 **Detailed Logging**: CSV logs with processing details for review
- ⚡ **Progress Tracking**: Rich console output with progress bars

**Usage:**
```bash
# Process all PDFs (rename based on content)
uv run scripts/update_pdf_file_names.py data/original_pdfs data/renamed_pdfs --num_files -1

# Process just 5 files for testing
uv run scripts/update_pdf_file_names.py data/original_pdfs data/renamed_pdfs --num_files 5

# The script will:
# 1. Extract titles using multiple methods (font analysis, positioning, OCR)
# 2. Translate non-English titles to English
# 3. Create clean filenames (lowercase_with_underscores.pdf)
# 4. Save processing logs for review
```

**Example Transformation:**
- `התכנית-האסטרטגית-הלאומית-להצללה.pdf` → `national_strategic_plan_for_shading_and_cooling.pdf`
- `AUEJ_Volume 14_Issue 52_Pages 1004-1023.pdf` → `effects_of_downtown_improvement_projects_on_retail_activity.pdf`

**Tips:**
- Run on a small batch first (`--num_files 5`) to test results
- Check the generated CSV log to review extraction quality
- Adjust the title extraction logic in the script if needed for your document types

---

## 🧯 5. Troubleshooting

### **Ollama Issues**
- **Service not running?** → `ollama serve`
- **Missing models?** → `ollama list` to verify, then `ollama pull <model-name>`
- **Model compatibility?** → Check [Ollama model library](https://ollama.com/library)

### **Document Loading Issues**
- **No PDFs found?** → Check `input_folder` path in `settings.toml`
- **Permission errors?** → Ensure read access to PDF directory
- **Memory errors?** → Lower `batch_size` in `settings.toml`

### **Performance Issues**
- **Slow processing?** → Adjust `max_workers` and `batch_size` in settings
- **High memory usage?** → Enable `memory_efficient = true` and lower batch sizes
- **Apple Silicon not detected?** → Ensure PyTorch with MPS support is installed

### **UI Issues**
- **Marimo not starting?** → Try `uv run marimo --version` to verify installation
- **Streamlit errors?** → Check you're using UV: `uv run streamlit run src/UI.py`
- **Port conflicts?** → Marimo auto-selects ports, or specify with `--port`

### **Configuration Issues**
- **Settings not loading?** → Verify `settings.toml` syntax with a TOML validator
- **Path errors?** → Use absolute paths or ensure relative paths are from project root

---

## 🎯 6. Key Features

- **🔒 100% Local**: No data leaves your machine
- **⚡ Fast Setup**: UV handles all dependencies automatically  
- **🧠 Smart Retrieval**: ChromaDB vector search with source citations
- **🍎 Apple Silicon Optimized**: MPS acceleration with graceful fallbacks
- **⚙️ Fully Configurable**: All settings in `settings.toml` - no code changes needed
- **📚 Multiple Interfaces**: Choose between Marimo (interactive) or Streamlit (traditional)
- **🔄 Easy Model Switching**: Just update settings and restart

## 📌 7. What's New

**Recent Updates:**
- ✅ Migrated to UV package management for faster, more reliable installs
- ✅ Added Marimo reactive notebook interface as primary UI
- ✅ Centralized all configuration in `settings.toml`
- ✅ Optimized document loading with parallel processing
- ✅ Enhanced Apple Silicon support with MPS acceleration
- ✅ Added source citations and relevance scoring

**Future Plans:**
- 📄 Support for additional formats (Markdown, .txt, HTML)
- 💾 Chat history persistence
- 🔍 Advanced search and filtering options
- 🎨 UI customization themes

---

## 👋 Final Thoughts

Modern local RAG is incredibly powerful and accessible. With tools like UV, Ollama, and Marimo, you can build a sophisticated, private AI assistant that rivals cloud services — completely offline.

**Performance Tip:** On Apple Silicon Macs with 16GB+ RAM, this setup can process documents and respond to queries faster than many cloud-based solutions!

If you found this useful or have ideas to improve it, feel free to open a PR or drop a star ⭐️
