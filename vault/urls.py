
from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("documents/upload/", views.upload_document, name="upload_document"),
    path(
        "documents/<uuid:document_id>/",
        views.document_detail,
        name="document_detail",
    ),
    path(
        "documents/<uuid:document_id>/edit/",
        views.edit_document,
        name="edit_document",
    ),
    path(
        "documents/<uuid:document_id>/download/",
        views.download_document,
        name="download_document",
    ),
    path(
        "documents/<uuid:document_id>/delete/",
        views.delete_document,
        name="delete_document",
    ),
    path(
        "documents/<uuid:document_id>/grants/",
        views.grant_access,
        name="grant_access",
    ),
    path(
        "documents/<uuid:document_id>/grants/<int:user_id>/revoke/",
        views.revoke_access,
        name="revoke_access",
    ),
    path("admin/activity/", views.admin_activity, name="admin_activity"),
    path("admin/activity/verify/", views.audit_verify, name="audit_verify"),
]
