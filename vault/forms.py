import os
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Document, Category, DocumentGrant

User = get_user_model()
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".csv"}
MAX_BYTES = settings.MAX_UPLOAD_MB * 1024 * 1024

def validate_upload(upload):
    ext = os.path.splitext(upload.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise forms.ValidationError("Unsupported file type. Allowed: PDF, PNG, JPG, TXT, CSV.")
    if upload.size > MAX_BYTES:
        raise forms.ValidationError(f"File is too large. Maximum size is {settings.MAX_UPLOAD_MB} MB.")
    head = upload.read(16)
    upload.seek(0)
    signatures = {
        ".pdf": head.startswith(b"%PDF-"),
        ".png": head.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": head.startswith(b"\xff\xd8\xff"),
        ".jpeg": head.startswith(b"\xff\xd8\xff"),
        ".txt": b"\x00" not in head,
        ".csv": b"\x00" not in head,
    }
    if not signatures[ext]:
        raise forms.ValidationError("The file contents do not match the selected file type.")
    return upload

class DocumentUploadForm(forms.ModelForm):
    upload = forms.FileField()
    class Meta:
        model = Document
        fields = ["title", "description", "category"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}
    def clean_upload(self):
        return validate_upload(self.cleaned_data["upload"])

class DocumentEditForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "description", "category"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

class GrantForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.none(), label="Grant to")
    permission = forms.ChoiceField(choices=DocumentGrant.PERMISSIONS)
    def __init__(self, *args, **kwargs):
        actor = kwargs.pop("actor", None)
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.filter(is_active=True).order_by("username")
        if actor:
            self.fields["user"].queryset = self.fields["user"].queryset.exclude(pk=actor.pk)
