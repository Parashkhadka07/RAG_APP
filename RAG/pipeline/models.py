from django.contrib.auth.models import User
from django.db import models
import os

class Notebook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


def document_upload_path(instance, filename):
    """
    Routes uploaded files into subfolders by type:
    documents/pdf/, documents/text/, documents/word/
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        subfolder = "pdf"
    elif ext == ".txt":
        subfolder = "text"
    elif ext == ".docx":
        subfolder = "word"
    else:
        subfolder = "other"

    return f"documents/{subfolder}/{filename}"


class Document(models.Model):
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE)
    file = models.FileField(upload_to=document_upload_path)
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        # FIX: Changed self.title -> self.filename
        return self.filename  


class Chunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    text = models.TextField()
    chunk_index = models.IntegerField()

    def __str__(self):
        # FIX: Changed self.title -> Chunk index + brief snippet
        snippet = self.text[:30] + "..." if len(self.text) > 30 else self.text
        return f"Chunk {self.chunk_index}: {snippet}"