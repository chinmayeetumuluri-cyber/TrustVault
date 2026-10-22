from .models import AuditEvent

def audit(actor, action, document=None, outcome="info", details=None, target_user_label=""):
    return AuditEvent.record(actor=actor, action=action, document=document, outcome=outcome,
                             details=details or {}, target_user_label=target_user_label)
