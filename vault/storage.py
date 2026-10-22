from django.conf import settings
from django.core.files.storage import FileSystemStorage

class PrivateDocumentStorage(FileSystemStorage):
    """Filesystem storage intentionally separate from static/public media roots."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("location", str(settings.PRIVATE_MEDIA_ROOT))
        kwargs.setdefault("base_url", None)
        super().__init__(*args, **kwargs)
