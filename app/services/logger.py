from app import db
from app.models import Log
from flask import request


def log_action(action: str, details: str = None, user_id: int = None):
    """Enregistre une action dans la table des logs."""
    try:
        log = Log(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass  # La journalisation ne doit jamais faire planter l'application