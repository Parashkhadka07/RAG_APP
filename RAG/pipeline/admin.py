from django.contrib import admin
from .models import Document,Chunk,Notebook
# Register your models here.

admin.site.register(Document)
admin.site.register(Chunk)
admin.site.register(Notebook)