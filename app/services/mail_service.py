from flask_mail import Message
from app import mail
from flask import current_app


def envoyer_alerte_anomalie(dossier, resultat, destinataire):
    """
    Envoie un email d'alerte quand un dossier est classé ANOMALIE.
    """
    try:
        regles = resultat.get("regles_violees", [])
        details = resultat.get("details", {})
        score  = resultat.get("score_if", 0)

        # Corps du message
        lignes_regles = ""
        for code, msg in details.items():
            lignes_regles += f"\n  • [{code}] {msg}"

        corps = f"""
Bonjour,

Une anomalie a été détectée sur le dossier suivant :

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Référence  : {dossier.reference}
  Statut     : {dossier.statut}
  Score IF   : {round(score, 2)} / 1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Règles métiers violées ({len(regles)}) :
{lignes_regles if lignes_regles else "  Aucune règle violée explicitement."}

Ce dossier a été automatiquement marqué comme ANOMALIE par le système SinistrAI.
Veuillez vous connecter à la plateforme pour examiner ce dossier.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cet email a été envoyé automatiquement par SinistrAI.
Ne pas répondre à cet email.
        """

        msg = Message(
            subject=f"⚠️ Anomalie détectée — Dossier {dossier.reference}",
            recipients=[destinataire],
            body=corps.strip()
        )
        mail.send(msg)
        return True

    except Exception as e:
        current_app.logger.error(f"Erreur envoi email : {e}")
        return False


def envoyer_email_bienvenue(user):
    """
    Envoie un email de bienvenue lors de la création d'un compte.
    """
    try:
        corps = f"""
Bonjour {user.nom},

Votre compte SinistrAI a été créé avec succès.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Email : {user.email}
  Rôle  : {user.role.capitalize()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Connectez-vous sur la plateforme avec votre email et le mot de passe 
fourni par votre administrateur.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cet email a été envoyé automatiquement par SinistrAI.
        """

        msg = Message(
            subject="🛡️ Bienvenue sur SinistrAI",
            recipients=[user.email],
            body=corps.strip()
        )
        mail.send(msg)
        return True

    except Exception as e:
        current_app.logger.error(f"Erreur envoi email bienvenue : {e}")
        return False