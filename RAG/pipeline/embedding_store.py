from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def build_vectorstore(chunks):
    return FAISS.from_documents(chunks, embeddings)

def save_vectorstore(vectorstore, path):
    vectorstore.save_local(path)

def load_vectorstore(path):
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)