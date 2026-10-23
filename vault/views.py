import hashlib
import hmac
import json
import mimetypes
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .audit import audit
from .forms import DocumentUploadForm, DocumentEditForm, GrantForm
from .models import AuditEvent, Category, Document, DocumentGrant
from .permissions import can_read, can_edit, can_manage_access
from .signup_forms import SignupForm

User = get_user_model()


# Public homepage
def home(request):
    return render(request, "vault/home.html")


# New user registration
@require_http_methods(["GET", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignupForm(request.POST)

        if form.is_valid():
            user = form.save()

            # Automatically sign in the newly registered user.
            login(request, user)

            messages.success(
                request,
                "Your TrustVault account was created successfully.",
            )
            return redirect("dashboard")
    else:
        form = SignupForm()

    return render(
        request,
        "registration/signup.html",
        {"form": form},
    )


def _visible_documents(user):
    if not user.is_authenticated:
        return Document.objects.none()

    return Document.objects.filter(deleted_at__isnull=True).filter(
        Q(owner=user) | Q(grants__user=user)
    ).distinct()


# Private dashboard
@login_required
def dashboard(request):
    docs = _visible_documents(request.user).select_related(
        "owner", "category"
    )

    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    owner = request.GET.get("owner", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if q:
        docs = docs.filter(
            Q(title__icontains=q)
            | Q(original_filename__icontains=q)
            | Q(description__icontains=q)
            | Q(owner__username__icontains=q)
        )

    if category:
        docs = docs.filter(category_id=category)

    if owner:
        docs = docs.filter(owner__username__icontains=owner)

    if date_from:
        docs = docs.filter(created_at__date__gte=date_from)

    if date_to:
        docs = docs.filter(created_at__date__lte=date_to)

    return render(request, "vault/dashboard.html", {
        "documents": docs,
        "categories": Category.objects.order_by("name"),
        "filters": {
            "q": q,
            "category": category,
            "owner": owner,
            "date_from": date_from,
            "date_to": date_to,
        },
    })


# Upload document
@login_required
@require_http_methods(["GET", "POST"])
def upload_document(request):
    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)

        if form.is_valid():
            upload = form.cleaned_data["upload"]
            digest = hashlib.sha256()

            for chunk in upload.chunks():
                digest.update(chunk)

            upload.seek(0)

            doc = form.save(commit=False)
            doc.owner = request.user
            doc.original_filename = os.path.basename(upload.name)[:255]
            doc.content_type = (
                mimetypes.guess_type(upload.name)[0]
                or "application/octet-stream"
            )
            doc.size_bytes = upload.size
            doc.sha256 = digest.hexdigest()
            doc.file = upload
            doc.save()

            audit(
                request.user,
                "upload",
                doc,
                "allowed",
                {
                    "sha256": doc.sha256,
                    "size_bytes": doc.size_bytes,
                },
            )

            messages.success(request, "Document uploaded securely.")
            return redirect("document_detail", document_id=doc.pk)
    else:
        form = DocumentUploadForm()

    return render(request, "vault/upload.html", {"form": form})


# View document details
@login_required
def document_detail(request, document_id):
    doc = get_object_or_404(
        Document,
        pk=document_id,
        deleted_at__isnull=True,
    )

    if not can_read(request.user, doc):
        audit(
            request.user,
            "view",
            doc,
            "denied",
            {"reason": "read_permission_missing"},
        )
        return HttpResponseForbidden(
            "You do not have permission to access this document."
        )

    audit(request.user, "view", doc, "allowed")

    grant = DocumentGrant.objects.filter(
        document=doc,
        user=request.user,
    ).first()

    can_manage = can_manage_access(request.user, doc)

    return render(request, "vault/detail.html", {
        "document": doc,
        "can_edit_document": can_edit(request.user, doc),
        "can_manage": can_manage,
        "grant": grant,
        "grants": (
            doc.grants.select_related("user", "granted_by").all()
            if can_manage else []
        ),
        "grant_form": (
            GrantForm(actor=request.user) if can_manage else None
        ),
    })


# Edit document
@login_required
@require_http_methods(["GET", "POST"])
def edit_document(request, document_id):
    doc = get_object_or_404(
        Document,
        pk=document_id,
        deleted_at__isnull=True,
    )

    if not can_edit(request.user, doc):
        audit(
            request.user,
            "edit",
            doc,
            "denied",
            {"reason": "edit_permission_missing"},
        )
        return HttpResponseForbidden(
            "You do not have edit permission."
        )

    if request.method == "POST":
        form = DocumentEditForm(request.POST, instance=doc)

        if form.is_valid():
            form.save()

            audit(
                request.user,
                "edit",
                doc,
                "allowed",
                {"fields": ["title", "description", "category"]},
            )

            messages.success(request, "Document details updated.")
            return redirect("document_detail", document_id=doc.pk)
    else:
        form = DocumentEditForm(instance=doc)

    return render(request, "vault/edit.html", {
        "form": form,
        "document": doc,
    })


# Download document
@login_required
@require_POST
def download_document(request, document_id):
    doc = get_object_or_404(
        Document,
        pk=document_id,
        deleted_at__isnull=True,
    )

    if not can_read(request.user, doc):
        audit(
            request.user,
            "download",
            doc,
            "denied",
            {"reason": "read_permission_missing"},
        )
        return HttpResponseForbidden(
            "You do not have permission to download this document."
        )

    audit(
        request.user,
        "download",
        doc,
        "allowed",
        {"sha256": doc.sha256},
    )

    try:
        file_handle = doc.file.open("rb")
    except (FileNotFoundError, ValueError, OSError):
        raise Http404("The document file is unavailable.")

    response = FileResponse(
        file_handle,
        as_attachment=True,
        filename=doc.original_filename,
    )
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"

    return response


# Delete document
@login_required
@require_POST
def delete_document(request, document_id):
    doc = get_object_or_404(
        Document,
        pk=document_id,
        deleted_at__isnull=True,
    )

    if not can_manage_access(request.user, doc):
        audit(
            request.user,
            "delete",
            doc,
            "denied",
            {"reason": "owner_required"},
        )
        return HttpResponseForbidden(
            "Only the owner or administrator can delete this document."
        )

    doc.deleted_at = timezone.now()
    doc.save(update_fields=["deleted_at", "updated_at"])

    audit(
        request.user,
        "delete",
        doc,
        "allowed",
        {"soft_delete": True},
    )

    messages.success(request, "Document deleted from active view.")
    return redirect("dashboard")


# Grant document access
@login_required
@require_POST
def grant_access(request, document_id):
    doc = get_object_or_404(
        Document,
        pk=document_id,
        deleted_at__isnull=True,
    )

    if not can_manage_access(request.user, doc):
        audit(
            request.user,
            "permission_grant",
            doc,
            "denied",
            {"reason": "owner_required"},
        )
        return HttpResponseForbidden(
            "Only the owner can manage document access."
        )

    form = GrantForm(request.POST, actor=request.user)

    if form.is_valid():
        target = form.cleaned_data["user"]
        permission = form.cleaned_data["permission"]

        grant, created = DocumentGrant.objects.update_or_create(
            document=doc,
            user=target,
            defaults={
                "permission": permission,
                "granted_by": request.user,
            },
        )

        audit(
            request.user,
            "permission_grant",
            doc,
            "allowed",
            {
                "permission": permission,
                "created": created,
            },
            target_user_label=target.get_username(),
        )

        messages.success(
            request,
            f"Access updated for {target.get_username()}.",
        )
    else:
        messages.error(
            request,
            "Please select a valid user and permission.",
        )

    return redirect("document_detail", document_id=doc.pk)


# Revoke document access
@login_required
@require_POST
def revoke_access(request, document_id, user_id):
    doc = get_object_or_404(
        Document,
        pk=document_id,
        deleted_at__isnull=True,
    )

    if not can_manage_access(request.user, doc):
        audit(
            request.user,
            "permission_revoke",
            doc,
            "denied",
            {"reason": "owner_required"},
        )
        return HttpResponseForbidden(
            "Only the owner can revoke access."
        )

    grant = get_object_or_404(
        DocumentGrant,
        document=doc,
        user_id=user_id,
    )

    target_name = grant.user.get_username()
    grant.delete()

    audit(
        request.user,
        "permission_revoke",
        doc,
        "allowed",
        {"revoked": True},
        target_user_label=target_name,
    )

    messages.success(request, f"Access revoked for {target_name}.")
    return redirect("document_detail", document_id=doc.pk)


# Administrator checks
def is_admin(user):
    return user.is_authenticated and user.is_staff


# View audit activity
@login_required
@user_passes_test(is_admin)
def admin_activity(request):
    events = AuditEvent.objects.select_related("actor").order_by("-id")[:500]

    return render(
        request,
        "vault/activity.html",
        {"events": events},
    )


# Verify audit integrity
@login_required
@user_passes_test(is_admin)
def audit_verify(request):
    rows = list(AuditEvent.objects.order_by("id"))
    previous = "GENESIS"
    failures = []

    for event in rows:
        payload = {
            "actor": str(event.actor_id) if event.actor_id else "anonymous",
            "actor_label": event.actor_label,
            "action": event.action,
            "document_id": event.document_id,
            "document_title": event.document_title,
            "target_user_label": event.target_user_label,
            "outcome": event.outcome,
            "details": event.details,
            "timestamp": event.timestamp.isoformat(),
            "previous_hash": event.previous_hash,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

        expected = hmac.new(
            settings.AUDIT_HMAC_KEY.encode(),
            canonical.encode(),
            hashlib.sha256,
        ).hexdigest()

        if (
            event.previous_hash != previous
            or not hmac.compare_digest(
                expected,
                event.event_hash,
            )
        ):
            failures.append(event.id)

        previous = event.event_hash

    return render(
        request,
        "vault/audit_verify.html",
        {
            "total": len(rows),
            "failures": failures,
        },
    )