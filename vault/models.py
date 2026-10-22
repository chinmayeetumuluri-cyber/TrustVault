import hashlib
import hmac
import json
import os
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from .storage import PrivateDocumentStorage

class Category(models.Model):
    name = models.CharField(max_length=80, unique=True, db_index=True)
    def __str__(self):
        return self.name

def private_upload_path(instance, filename):
    # Never trust the supplied filename for the stored path.
    ext = os.path.splitext(filename)[1].lower()
    return f"documents/{instance.id.hex}/{uuid.uuid4().hex}{ext}"

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=180, db_index=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_documents")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to=private_upload_path, storage=PrivateDocumentStorage(), max_length=500)
    content_type = models.CharField(max_length=100)
    size_bytes = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

class DocumentGrant(models.Model):
    READ = "read"
    EDIT = "edit"
    PERMISSIONS = [(READ, "Read"), (EDIT, "Edit")]
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="grants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="document_grants")
    permission = models.CharField(max_length=10, choices=PERMISSIONS, default=READ)
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="grants_made")
    created_at = models.DateTimeField(default=timezone.now)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["document", "user"], name="unique_document_user_grant")]
        indexes = [models.Index(fields=["user", "document"])]

class AuditEvent(models.Model):
    id = models.BigAutoField(primary_key=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_events")
    actor_label = models.CharField(max_length=150)
    action = models.CharField(max_length=40, db_index=True)
    document_id = models.CharField(max_length=36, blank=True, db_index=True)
    document_title = models.CharField(max_length=180, blank=True)
    target_user_label = models.CharField(max_length=150, blank=True)
    outcome = models.CharField(max_length=12, choices=[("allowed","Allowed"),("denied","Denied"),("info","Info")], default="info")
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    previous_hash = models.CharField(max_length=64, blank=True)
    event_hash = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ["-timestamp", "-id"]

    @classmethod
    def record(cls, *, actor=None, action, document=None, outcome="info", details=None, target_user_label=""):
        # HMAC chain detects edits/reordering without the separately configured key.
        # This is tamper-evident, not immutable against a database+key administrator.
        from django.conf import settings
        last = cls.objects.order_by("-id").first()
        previous = last.event_hash if last else "GENESIS"
        payload = {
            "actor": str(actor.pk) if actor else "anonymous",
            "actor_label": actor.get_username() if actor else "anonymous",
            "action": action,
            "document_id": str(document.pk) if document else "",
            "document_title": document.title if document else "",
            "target_user_label": target_user_label,
            "outcome": outcome,
            "details": details or {},
            "timestamp": timezone.now().isoformat(),
            "previous_hash": previous,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        digest = hmac.new(settings.AUDIT_HMAC_KEY.encode(), canonical.encode(), hashlib.sha256).hexdigest()
        return cls.objects.create(
            actor=actor, actor_label=payload["actor_label"], action=action,
            document_id=payload["document_id"], document_title=payload["document_title"],
            target_user_label=target_user_label, outcome=outcome, details=payload["details"],
            timestamp=timezone.datetime.fromisoformat(payload["timestamp"]),
            previous_hash=previous, event_hash=digest,
        )
