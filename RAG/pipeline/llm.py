import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_classic.chains import retrieval_qa

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY"),
)

def build_qa_chain(vectorstore):
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    return retrieval_qa.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
    )

def ask(qa_chain, question):
    result = qa_chain.invoke({"query": question})
    return result["result"], result["source_documents"]