from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.notebook_list, name="notebook_list"),
    path("signup/", views.signup, name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="pipeline/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    path("notebook/<int:notebook_id>/", views.notebook_detail, name="notebook_detail"),
    path("notebook/<int:notebook_id>/delete/", views.delete_notebook, name="delete_notebook"),
    path("notebook/<int:notebook_id>/upload/", views.upload_document, name="upload_document"),
    path("notebook/<int:notebook_id>/ask/", views.ask_question, name="ask_question"),
    path(
        "notebook/<int:notebook_id>/document/<int:document_id>/delete/",
        views.delete_document,
        name="delete_document",
    ),
]