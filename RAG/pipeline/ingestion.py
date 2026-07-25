import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader


def load_document(file_path):
    """Load ONE file, return its list of Document objects (one per page for PDFs)."""
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding="utf-8")
    return loader.load()


def load_documents(file_paths):
    """Load MULTIPLE files, combine all their Document objects into one list."""
    all_documents = []
    for file_path in file_paths:
        all_documents.extend(load_document(file_path))
    return all_documents