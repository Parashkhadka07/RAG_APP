from django.urls import path

from . import views

urlpatterns = [
    path("", views.notebook_list, name="notebook_list"),
    path("notebook/<int:notebook_id>/", views.notebook_detail, name="notebook_detail"),
    path("notebook/<int:notebook_id>/upload/", views.upload_document, name="upload_document"),
    path("notebook/<int:notebook_id>/ask/", views.ask_question, name="ask_question"),
]