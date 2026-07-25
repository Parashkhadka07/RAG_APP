from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

def load_documents(file_path):
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding="utf-8")
    return loader.load()  # returns list of LangChain Document objects (text + metadata)

