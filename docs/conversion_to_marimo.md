# Migration Plan: Streamlit to Marimo

## Current Architecture Analysis

The RAG chatbot application currently uses:
- **`UI.py`**: Streamlit-based chat interface (42 lines)
- **`rag_query.py`**: Core RAG functionality using ChromaDB and Ollama
- **`load_docs.py`**: Document loading and vector database management
- **`embedding.py`**: Embedding function configuration

**Key Advantage**: Marimo is already included in `pyproject.toml` dependencies, making migration straightforward.

## Migration Strategy

The core RAG logic is well-separated from the UI layer, so we only need to replace the Streamlit interface while keeping all backend functionality intact.

## Phase 1: Create Marimo Chat Interface

### 1.1 Main Interface (`marimo_ui.py`)
- Replace Streamlit's `st.chat_message()` and `st.chat_input()` with Marimo's `mo.ui.chat()`
- Implement reactive chat interface using Marimo's component system
- Migrate session state management to Marimo's reactive variables
- Create clean separation between UI and RAG logic

### 1.2 Core Features Migration
- **Chat History**: Use Marimo's reactive state instead of `st.session_state`
- **Message Display**: Implement with Marimo's markdown and UI components
- **User Input**: Replace `st.chat_input()` with Marimo's input widgets
- **Spinner/Loading**: Use Marimo's progress indicators

### 1.3 Enhanced Features (Marimo Advantages)
- **File Upload**: Add document upload directly in the interface
- **Real-time Processing**: Show document processing status
- **Parameter Controls**: Interactive sliders for chunk size, top-k retrieval
- **Model Selection**: Dropdown for switching between Ollama models

## Phase 2: Advanced Marimo Features

### 2.1 Interactive Controls
```python
# Example Marimo controls to add
chunk_size = mo.ui.slider(400, 1200, value=800, label="Chunk Size")
top_k = mo.ui.slider(1, 10, value=5, label="Top K Results")
model_select = mo.ui.dropdown(["gemma3n:latest", "mistral", "llama3"], value="gemma3n:latest")
```

### 2.2 Source Document Display
- Expandable sections showing retrieved document chunks
- Source attribution with document names and page numbers
- Similarity scores for each retrieved chunk

### 2.3 Settings Panel
- Embedding model configuration
- ChromaDB path settings
- Ollama connection settings

## Phase 3: Integration & Cleanup

### 3.1 Dependencies
- Remove Streamlit from `pyproject.toml` dependencies
- Keep Marimo (already present)
- Verify all other dependencies remain compatible

### 3.2 Documentation Updates
- Update `README.md` with Marimo-specific instructions
- Replace `streamlit run ./src/UI.py` with `marimo run ./src/marimo_ui.py`
- Add Marimo installation and usage instructions

### 3.3 Testing
- Create integration tests for the new Marimo interface
- Test reactive behavior with parameter changes
- Verify document upload functionality
- Test deployment as both notebook and web app

## Implementation Details

### Current Streamlit Code Pattern
```python
# Current UI.py structure
import streamlit as st
from rag_query import query_rag

# Session state management
if "messages" not in st.session_state.keys():
    st.session_state.messages = [...]

# Chat interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if input := st.chat_input():
    # Handle user input and generate response
```

### New Marimo Code Pattern
```python
# New marimo_ui.py structure
import marimo as mo
from rag_query import query_rag

# Reactive state management
chat_history = mo.state([])

# Interactive chat interface
chat = mo.ui.chat(
    messages=chat_history.value,
    on_message=handle_chat_message
)

# Parameter controls
controls = mo.ui.form({
    "chunk_size": mo.ui.slider(400, 1200, value=800),
    "top_k": mo.ui.slider(1, 10, value=5),
    "model": mo.ui.dropdown(["gemma3n:latest", "mistral"])
})
```

## Benefits of Migration

### 1. Reactive Interface
- Parameters automatically update the interface
- Real-time feedback on configuration changes
- Better user experience with immediate visual feedback

### 2. Enhanced Functionality
- **File Upload**: Built-in support for document uploads
- **Interactive Widgets**: Sliders, dropdowns, and forms
- **Better State Management**: Reactive variables instead of session state

### 3. Development Experience
- **Git-Friendly**: Marimo notebooks are stored as Python files
- **Reproducible**: Deterministic execution order
- **Deployable**: Run as script, web app, or deploy easily

### 4. Modern Features
- **AI Integration**: Built-in AI assistance for notebook development
- **WebAssembly**: Can run entirely in browser
- **Enterprise Ready**: Used by Cloudflare, Shopify, BlackRock

## Migration Timeline

- **Phase 1**: 2-3 hours (core interface migration)
- **Phase 2**: 2-4 hours (enhanced features)
- **Phase 3**: 1-2 hours (cleanup and testing)

**Total Estimated Time**: 5-9 hours

## Risks and Mitigations

### Risk 1: Learning Curve
- **Mitigation**: Marimo has excellent documentation and examples
- **Fallback**: Keep original Streamlit code until migration is complete

### Risk 2: Feature Parity
- **Mitigation**: Marimo has equivalent or better widgets for all Streamlit features used
- **Enhancement**: Can add features not easily possible in Streamlit

### Risk 3: Deployment Changes
- **Mitigation**: Update documentation with new deployment instructions
- **Benefit**: Marimo offers more deployment options than Streamlit

## Success Criteria

1. ✅ Chat interface functions identically to Streamlit version
2. ✅ All RAG functionality preserved
3. ✅ Enhanced with interactive parameter controls
4. ✅ Document upload functionality added
5. ✅ Source attribution displayed clearly
6. ✅ Deployable as both development notebook and production app
7. ✅ Updated documentation and examples

## Next Steps

1. Create `src/marimo_ui.py` with basic chat interface
2. Test core functionality with existing RAG backend
3. Add enhanced features (parameter controls, file upload)
4. Update documentation and deployment instructions
5. Remove Streamlit dependency
6. Create integration tests for new interface


Verified Plan Based on Official Examples

  The official custom.py example shows the exact pattern we need:

  1. Simple Function-Based Model: Instead of a class, we just need a function that takes
  (messages, config) and returns a response
  2. Direct Integration: Pass the function directly to mo.ui.chat()
  3. Clean Implementation: Much simpler than our current manual form approach

  Key Insights from Official Examples

  1. Model Function Signature:
  def rag_model(messages, config):
      # messages is a list with .content and .role attributes
      # Return response string directly
  2. Chat Component Usage:
  chat = mo.ui.chat(
      rag_model,  # Just pass the function directly
      show_configuration_controls=True
  )
  3. Message Handling: The last message is typically messages[-1].content for user input
                                                                                        
⏺ User approved Claude's plan:
  ⎿ Verified Plan: Implement Native Marimo Chat (Based on Official Examples)

    Analysis Confirmed

    After reviewing the official Marimo chat examples (custom.py), the approach is now 
    clear and verified. Our current manual form implementation should be replaced with
    the native mo.ui.chat() component.

    Implementation Pattern (From Official Examples)

    def rag_model(messages, config):
        # Get user's latest message
        user_message = messages[-1].content
        
        # Use existing RAG system
        response = query_rag(user_message)
        return response

    # Create chat interface
    chat = mo.ui.chat(
        rag_model,
        prompts=["What is this document about?", "Summarize the key points"],
        show_configuration_controls=True
    )

    Verified Implementation Steps

    1. Create RAG Model Function

    - Function signature: def rag_model(messages, config)
    - Extract user message from messages[-1].content
    - Call existing query_rag() function
    - Return response string directly
    - Add error handling within the function

    2. Replace Current Implementation

    - Remove all manual form handling cells
    - Remove separate input/button components
    - Remove manual state management
    - Replace with single mo.ui.chat() call

    3. Benefits (Confirmed by Examples)

    - Native Marimo Integration: Uses official patterns
    - Automatic UI: Chat interface, history, and interactions handled automatically
    - Reactive Updates: Works seamlessly with Marimo's reactive model
    - Professional Appearance: Consistent with Marimo's design standards
    - Reliable Functionality: Button/submission issues resolved

    Simple, Clean Solution

    The official examples show this is much simpler than our current approach. Instead 
    of fighting Marimo's reactive model with manual forms, we work with it using the
    purpose-built chat component.

    Expected Outcome

    - Native chat interface that works reliably
    - Automatic message history management
    - Professional chat UI styling
    - Seamless RAG integration
    - No more button click issues
    