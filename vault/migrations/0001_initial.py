# Generated as the initial schema for TrustVault.
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models
import vault.models
import vault.storage

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=80, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(db_index=True, max_length=180)),
                ("description", models.TextField(blank=True)),
                ("original_filename", models.CharField(max_length=255)),
                ("file", models.FileField(max_length=500, storage=vault.storage.PrivateDocumentStorage(), upload_to=vault.models.private_upload_path)),
                ("content_type", models.CharField(max_length=100)),
                ("size_bytes", models.PositiveBigIntegerField()),
                ("sha256", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("category", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="vault.category")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="owned_documents", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("actor_label", models.CharField(max_length=150)),
                ("action", models.CharField(db_index=True, max_length=40)),
                ("document_id", models.CharField(blank=True, db_index=True, max_length=36)),
                ("document_title", models.CharField(blank=True, max_length=180)),
                ("target_user_label", models.CharField(blank=True, max_length=150)),
                ("outcome", models.CharField(choices=[("allowed", "Allowed"), ("denied", "Denied"), ("info", "Info")], default="info", max_length=12)),
                ("details", models.JSONField(blank=True, default=dict)),
                ("timestamp", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("previous_hash", models.CharField(blank=True, max_length=64)),
                ("event_hash", models.CharField(max_length=64, unique=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-timestamp", "-id"]},
        ),
        migrations.CreateModel(
            name="DocumentGrant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("permission", models.CharField(choices=[("read", "Read"), ("edit", "Edit")], default="read", max_length=10)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="grants", to="vault.document")),
                ("granted_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="grants_made", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="document_grants", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="documentgrant",
            constraint=models.UniqueConstraint(fields=("document", "user"), name="unique_document_user_grant"),
        ),
        migrations.AddIndex(
            model_name="documentgrant",
            index=models.Index(fields=["user", "document"], name="vault_grant_user_doc_idx"),
        ),
    ]
