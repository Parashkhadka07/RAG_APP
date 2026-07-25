"""
llm.py
------
Responsible for ONE thing: taking a vectorstore + a question, and
returning an answer plus the source chunks used to generate it.
"""

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY"),
)

ANSWER_PROMPT = PromptTemplate(
    template="""You are a helpful assistant answering questions using only the
context provided below, taken from the user's uploaded documents.

Format your answer in clean Markdown:
- Use short paragraphs or bullet points, not one dense block of text.
- Use **bold** for key terms.
- Use numbered lists for steps/sequences and bullet lists for unordered items.
- Use headings (##) only if the answer has multiple distinct sections.
- If the context does not contain the answer, say so plainly instead of guessing.

Context:
{context}

Question: {question}

Answer:""",
    input_variables=["context", "question"],
)


def build_qa_chain(vectorstore, k: int = 5):
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": ANSWER_PROMPT},
    )


def ask(qa_chain, question: str):
    result = qa_chain.invoke({"query": question})
    return result["result"], result["source_documents"]