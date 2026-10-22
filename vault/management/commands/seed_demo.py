from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from vault.models import Category, Document, DocumentGrant
from django.core.files.base import ContentFile
import hashlib

class Command(BaseCommand):
    help = "Create local demo users and sample documents. Use only in a disposable demo environment."

    def add_arguments(self, parser):
        parser.add_argument("--password", required=True, help="Password shared by demo accounts; use a strong value.")

    def handle(self, *args, **opts):
        password = opts["password"]
        if len(password) < 12:
            raise CommandError("Use a demo password of at least 12 characters.")
        User = get_user_model()
        accounts = [
            ("admin_demo", True, True),
            ("owner_demo", False, False),
            ("viewer_demo", False, False),
            ("outsider_demo", False, False),
        ]
        users = {}
        for username, staff, superuser in accounts:
            user, _ = User.objects.get_or_create(username=username, defaults={"is_staff": staff, "is_superuser": superuser, "is_active": True})
            user.is_staff, user.is_superuser, user.is_active = staff, superuser, True
            user.set_password(password)
            user.save()
            users[username] = user
        category, _ = Category.objects.get_or_create(name="Contracts")
        doc, created = Document.objects.get_or_create(
            title="Sample: Partner Agreement",
            owner=users["owner_demo"],
            defaults={"description": "Demo-only example document. Do not use real confidential information.",
                      "category": category, "original_filename": "partner-agreement.txt",
                      "content_type": "text/plain", "size_bytes": 62,
                      "sha256": hashlib.sha256(b"DEMO ONLY - fictional agreement for TrustVault showcase.").hexdigest()}
        )
        if created:
            doc.file.save("partner-agreement.txt", ContentFile(b"DEMO ONLY - fictional agreement for TrustVault showcase."), save=True)
        DocumentGrant.objects.get_or_create(document=doc, user=users["viewer_demo"],
            defaults={"permission": "read", "granted_by": users["owner_demo"]})
        self.stdout.write(self.style.SUCCESS("Demo data ready. Accounts: admin_demo, owner_demo, viewer_demo, outsider_demo."))
        self.stdout.write(self.style.WARNING("All demo accounts share the password you supplied. Change/remove them before public production use."))
