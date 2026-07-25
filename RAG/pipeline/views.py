"""
views.py
--------
Wires the pipeline (ingestion -> chunking -> embedding_store -> llm)
into Django. Three views:

  notebook_list   - shows all notebooks for the logged-in user, create new ones
  notebook_detail - shows one notebook: document list, upload, and chat
  ask_question     - AJAX endpoint the chat UI calls to get an answer
"""

import json
import os
import shutil

from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_http_methods

from .models import Chunk, Document, Notebook
from .ingestion import load_documents
from .chunking import chunk_documents
from .embedding_store import build_vectorstore, save_vectorstore, load_vectorstore
from .llm import build_qa_chain, ask


INDEX_ROOT = os.path.join(settings.BASE_DIR, "indexes")


def _index_path(notebook_id):
    return os.path.join(INDEX_ROOT, f"notebook_{notebook_id}")


def signup(request):
    if request.user.is_authenticated:
        return redirect("notebook_list")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("notebook_list")
    else:
        form = UserCreationForm()

    return render(request, "pipeline/signup.html", {"form": form})


@login_required
def notebook_list(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        if title:
            notebook = Notebook.objects.create(user=request.user, title=title)
            return redirect("notebook_detail", notebook_id=notebook.id)

    notebooks = Notebook.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "pipeline/notebook_app.html", {"notebooks": notebooks})


@login_required
def notebook_detail(request, notebook_id):
    notebook = get_object_or_404(Notebook, id=notebook_id, user=request.user)
    documents = notebook.document_set.all().order_by("-uploaded_at")
    return render(
        request,
        "pipeline/notebook_app.html",
        {"notebook": notebook, "documents": documents},
    )


@login_required
@require_http_methods(["POST", "DELETE"])
def delete_notebook(request, notebook_id):
    notebook = get_object_or_404(Notebook, id=notebook_id, user=request.user)

    index_path = _index_path(notebook.id)
    if os.path.exists(index_path):
        shutil.rmtree(index_path)

    notebook.delete()  # cascades to Document and Chunk rows automatically
    return JsonResponse({"message": "Notebook deleted."})


@login_required
@require_http_methods(["POST", "DELETE"])
def delete_document(request, notebook_id, document_id):
    notebook = get_object_or_404(Notebook, id=notebook_id, user=request.user)
    document = get_object_or_404(Document, id=document_id, notebook=notebook)

    document.file.delete(save=False)  # removes the physical file from disk
    document.delete()  # cascades to Chunk rows automatically

    # Rebuild the index without this document. If no documents remain, just
    # remove the index folder entirely.
    remaining = notebook.document_set.exists()
    index_path = _index_path(notebook.id)

    if not remaining:
        if os.path.exists(index_path):
            shutil.rmtree(index_path)
    else:
        try:
            _rebuild_notebook_index(notebook)
        except Exception as e:
            return JsonResponse(
                {"error": f"Document removed, but failed to rebuild index: {e}"},
                status=500,
            )

    return JsonResponse({"message": "Document removed."})


@login_required
@require_POST
def upload_document(request, notebook_id):
    notebook = get_object_or_404(Notebook, id=notebook_id, user=request.user)
    uploaded_files = request.FILES.getlist("files")

    if not uploaded_files:
        return JsonResponse({"error": "No files provided."}, status=400)

    saved_docs = []
    for f in uploaded_files:
        doc = Document.objects.create(notebook=notebook, file=f, filename=f.name)
        saved_docs.append(doc)

    # Rebuild the notebook's index from ALL its documents (simple v1 approach)
    try:
        _rebuild_notebook_index(notebook)
    except Exception as e:
        return JsonResponse({"error": f"Failed to process documents: {e}"}, status=500)

    for doc in saved_docs:
        doc.processed = True
        doc.save()

    return JsonResponse(
        {
            "message": f"Uploaded and indexed {len(saved_docs)} document(s).",
            "documents": [{"id": d.id, "filename": d.filename} for d in saved_docs],
        }
    )


def _rebuild_notebook_index(notebook):
    """Re-run the full pipeline over every document currently in this notebook."""
    file_paths = [d.file.path for d in notebook.document_set.all()]
    if not file_paths:
        return

    documents = load_documents(file_paths)
    chunks = chunk_documents(documents)

    # keep chunk text in the DB too, so we have a durable record / can show counts
    Chunk.objects.filter(document__notebook=notebook).delete()
    for doc in notebook.document_set.all():
        doc_chunks = [c for c in chunks if c.metadata.get("source") == doc.file.path]
        for i, c in enumerate(doc_chunks):
            Chunk.objects.create(document=doc, text=c.page_content, chunk_index=i)

    vectorstore = build_vectorstore(chunks)
    os.makedirs(INDEX_ROOT, exist_ok=True)
    save_vectorstore(vectorstore, _index_path(notebook.id))


@login_required
@require_POST
def ask_question(request, notebook_id):
    notebook = get_object_or_404(Notebook, id=notebook_id, user=request.user)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request body."}, status=400)

    question = body.get("question", "").strip()
    if not question:
        return JsonResponse({"error": "Question cannot be empty."}, status=400)

    index_path = _index_path(notebook.id)
    if not os.path.exists(index_path):
        return JsonResponse(
            {"error": "This notebook has no processed documents yet."}, status=400
        )

    vectorstore = load_vectorstore(index_path)
    qa_chain = build_qa_chain(vectorstore)
    answer, source_documents = ask(qa_chain, question)

    sources = []
    seen = set()
    for doc in source_documents:
        name = os.path.basename(doc.metadata.get("source", "unknown"))
        page = doc.metadata.get("page")
        label = f"{name} (page {page + 1})" if page is not None else name
        if label not in seen:
            sources.append(label)
            seen.add(label)

    return JsonResponse({"answer": answer, "sources": sources})