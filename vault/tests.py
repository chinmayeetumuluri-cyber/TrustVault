import io
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Category, Document, DocumentGrant, AuditEvent
from .permissions import can_read, can_edit

User = get_user_model()

@override_settings(PRIVATE_MEDIA_ROOT="/tmp/trustvault-test-uploads")
class TrustVaultSecurityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="Test-pass-2026!")
        self.viewer = User.objects.create_user(username="viewer", password="Test-pass-2026!")
        self.other = User.objects.create_user(username="other", password="Test-pass-2026!")
        self.admin = User.objects.create_user(username="admin", password="Test-pass-2026!", is_staff=True, is_superuser=True)
        self.category = Category.objects.create(name="Contracts")
        self.doc = Document.objects.create(
            title="Private contract", owner=self.owner, category=self.category,
            original_filename="contract.txt", file=SimpleUploadedFile("contract.txt", b"secret contract"),
            content_type="text/plain", size_bytes=15, sha256="a" * 64
        )

    def test_ungranted_user_cannot_view_detail(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("document_detail", args=[self.doc.pk]))
        self.assertEqual(response.status_code, 403)

    def test_ungranted_user_cannot_download_even_with_guessed_uuid(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse("download_document", args=[self.doc.pk]))
        self.assertEqual(response.status_code, 403)

    def test_ungranted_user_cannot_edit(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("edit_document", args=[self.doc.pk]))
        self.assertEqual(response.status_code, 403)

    def test_ungranted_user_cannot_delete(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse("delete_document", args=[self.doc.pk]))
        self.assertEqual(response.status_code, 403)
        self.doc.refresh_from_db()
        self.assertIsNone(self.doc.deleted_at)

    def test_grant_read_then_revoke_blocks_next_download(self):
        DocumentGrant.objects.create(document=self.doc, user=self.viewer, permission="read", granted_by=self.owner)
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(reverse("document_detail", args=[self.doc.pk])).status_code, 200)
        grant = DocumentGrant.objects.get(document=self.doc, user=self.viewer)
        grant.delete()
        response = self.client.post(reverse("download_document", args=[self.doc.pk]))
        self.assertEqual(response.status_code, 403)

    def test_read_grant_does_not_allow_edit(self):
        DocumentGrant.objects.create(document=self.doc, user=self.viewer, permission="read", granted_by=self.owner)
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(reverse("edit_document", args=[self.doc.pk])).status_code, 403)

    def test_edit_grant_allows_edit_but_not_delete(self):
        DocumentGrant.objects.create(document=self.doc, user=self.viewer, permission="edit", granted_by=self.owner)
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(reverse("edit_document", args=[self.doc.pk])).status_code, 200)
        self.assertEqual(self.client.post(reverse("delete_document", args=[self.doc.pk])).status_code, 403)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("document_detail", args=[self.doc.pk]))
        self.assertEqual(response.status_code, 302)

    def test_admin_does_not_automatically_read_document(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("document_detail", args=[self.doc.pk])).status_code, 403)

    def test_denied_attempt_is_audited(self):
        self.client.force_login(self.other)
        self.client.get(reverse("document_detail", args=[self.doc.pk]))
        event = AuditEvent.objects.filter(action="view", outcome="denied").latest("id")
        self.assertEqual(event.document_id, str(self.doc.pk))

    def test_upload_rejects_unsupported_extension(self):
        self.client.force_login(self.owner)
        file = SimpleUploadedFile("malware.exe", b"not an executable")
        response = self.client.post(reverse("upload_document"), {
            "title": "Bad file", "description": "", "category": self.category.pk, "upload": file
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Document.objects.filter(title="Bad file").exists())

    def test_upload_rejects_pdf_extension_with_wrong_signature(self):
        self.client.force_login(self.owner)
        file = SimpleUploadedFile("fake.pdf", b"not a pdf")
        response = self.client.post(reverse("upload_document"), {
            "title": "Fake PDF", "description": "", "category": self.category.pk, "upload": file
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Document.objects.filter(title="Fake PDF").exists())

    def test_owner_can_grant_and_revoke(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("grant_access", args=[self.doc.pk]), {
            "user": self.viewer.pk, "permission": "read"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(can_read(self.viewer, self.doc))
        response = self.client.post(reverse("revoke_access", args=[self.doc.pk, self.viewer.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(can_read(self.viewer, self.doc))

    def test_audit_chain_links_events(self):
        AuditEvent.record(actor=self.owner, action="test_event", document=self.doc, outcome="info")
        AuditEvent.record(actor=self.owner, action="test_event_2", document=self.doc, outcome="info")
        rows = list(AuditEvent.objects.order_by("id"))
        self.assertEqual(rows[-1].previous_hash, rows[-2].event_hash)
