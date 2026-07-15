# 📚 RAG Chat: Multi-Document AI Assistant

## Project Description
A powerful Retrieval-Augmented Generation (RAG) application that allows you to chat with your documents using local or cloud-based LLMs. RAG Chat enables users to upload various document formats and query them using advanced AI models. It uses a sophisticated indexing pipeline to break down documents into searchable chunks, ensuring accurate and context-aware responses.

## Features
- **Multi-Format Support:** Upload PDF, DOCX, TXT, MD, CSV, and HTML files.
- **Flexible LLM Backends:** Supports **OpenAI (GPT-4o)** and **Ollama** (for local execution).
- **Efficient Retrieval:** Powered by **FAISS** vector store and **HuggingFace** embeddings (`all-MiniLM-L6-v2`).
- **Interactive UI:** A clean, Streamlit-based dashboard with source citations and conversation history.

## Tech Stack
- **Framework:** Streamlit
- **Orchestration:** LangChain
- **Vector Database:** FAISS
- **Embeddings:** HuggingFace Transformers
- **LLM Support:** OpenAI API, Ollama (Local)

## Setup and Installation

### Prerequisites
- Python 3.9+
- (Optional) **Ollama** installed for local LLM support.
- (Optional) **OpenAI API Key** for cloud-based LLM support.

### Clone the Repository
```bash
git clone https://github.com/vikrambtech2025-png/RAG-type-app.git
cd RAG-type-app
```

### Create a Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Running the Application
```bash
streamlit run app.py
```

The application will typically open in your web browser at `http://localhost:8501`.

## How to Use
1. **Configure Backend:** In the sidebar, select your preferred LLM backend (OpenAI or Ollama).
2. **Upload Documents:** Drag and drop your files into the upload area. The system will automatically index them.
3. **Ask Questions:** Use the chat input to ask questions about your documents. The assistant will provide answers with citations to the original sources.

## Project Structure
- `app.py`: The main Streamlit UI and application logic.
- `rag_engine.py`: Core RAG logic, including document processing, embedding, and retrieval.
- `requirements.txt`: List of Python dependencies.
- `render.yaml`: Configuration for deployment on Render.

## Contributing
Contributions are welcome! If you have suggestions for new features or improvements, please open an issue or submit a pull request.

## License
This project is licensed under the MIT License.

---
*Built with ❤️ using LangChain and Streamlit.*
