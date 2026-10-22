from .models import DocumentGrant

def can_read(user, document):
    if not user.is_authenticated or document.deleted_at is not None:
        return False
    if document.owner_id == user.pk:
        return True
    grant = DocumentGrant.objects.filter(document=document, user=user).only("permission").first()
    return bool(grant)

def can_edit(user, document):
    if not user.is_authenticated or document.deleted_at is not None:
        return False
    if document.owner_id == user.pk:
        return True
    return DocumentGrant.objects.filter(document=document, user=user, permission=DocumentGrant.EDIT).exists()

def can_manage_access(user, document):
    return bool(user.is_authenticated and (document.owner_id == user.pk or user.is_superuser))
