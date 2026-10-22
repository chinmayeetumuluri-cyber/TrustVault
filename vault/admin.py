from django.contrib import admin
from .models import Category, Document, DocumentGrant, AuditEvent

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["name"]

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "category", "created_at", "deleted_at"]
    search_fields = ["title", "original_filename", "owner__username"]
    list_filter = ["category", "created_at", "deleted_at"]
    readonly_fields = ["id", "sha256", "size_bytes", "created_at", "updated_at"]

@admin.register(DocumentGrant)
class DocumentGrantAdmin(admin.ModelAdmin):
    list_display = ["document", "user", "permission", "granted_by", "created_at"]
    list_filter = ["permission"]

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ["id", "timestamp", "actor_label", "action", "outcome", "document_title"]
    readonly_fields = [field.name for field in AuditEvent._meta.fields]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
