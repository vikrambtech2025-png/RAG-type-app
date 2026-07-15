import os
import tempfile
from pathlib import Path
from typing import List, Literal, Optional

from langchain_community.document_loaders import (
    CSVLoader,
    Docx2txtLoader,
    PyMuPDFLoader,
    TextLoader,
    UnstructuredHTMLLoader,
)
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

LLMBackend = Literal["openai", "ollama", "none"]


class DocumentProcessor:
    SUPPORTED_EXTENSIONS = {
        ".pdf": PyMuPDFLoader,
        ".txt": TextLoader,
        ".md": TextLoader,
        ".docx": Docx2txtLoader,
        ".csv": CSVLoader,
        ".html": UnstructuredHTMLLoader,
        ".htm": UnstructuredHTMLLoader,
    }

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""],
        )

    def load_and_chunk(self, file_path: str) -> List[Document]:
        ext = Path(file_path).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")

        loader_cls = self.SUPPORTED_EXTENSIONS[ext]
        loader = loader_cls(file_path)
        docs = loader.load()

        for doc in docs:
            doc.metadata["source_file"] = Path(file_path).name
            doc.metadata["source_ext"] = ext

        return self.splitter.split_documents(docs)


class RAGEngine:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
    ):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True},
        )
        self.vector_store: Optional[FAISS] = None
        self.all_chunks: List[Document] = []
        self.processor = DocumentProcessor()

    @property
    def is_indexed(self) -> bool:
        return self.vector_store is not None

    def add_file(self, file_path: str) -> int:
        chunks = self.processor.load_and_chunk(file_path)
        if not chunks:
            return 0

        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        else:
            self.vector_store.add_documents(chunks)

        self.all_chunks.extend(chunks)
        return len(chunks)

    def add_text(self, text: str, metadata: Optional[dict] = None) -> int:
        meta = metadata or {}
        doc = Document(page_content=text, metadata=meta)
        split = self.processor.splitter.split_documents([doc])

        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(split, self.embeddings)
        else:
            self.vector_store.add_documents(split)

        self.all_chunks.extend(split)
        return len(split)

    def search(self, query: str, k: int = 4) -> List[Document]:
        if not self.is_indexed:
            return []
        return self.vector_store.similarity_search(query, k=k)

    def clear(self):
        self.vector_store = None
        self.all_chunks = []

    def get_chunk_count(self) -> int:
        return len(self.all_chunks)

    def get_document_sources(self) -> List[str]:
        sources = set()
        for chunk in self.all_chunks:
            src = chunk.metadata.get("source_file", "unknown")
            sources.add(src)
        return sorted(sources)
