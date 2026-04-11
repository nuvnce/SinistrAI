from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Utilisateur

bp = Blueprint('admin', __name__)

@bp.route('/admin/utilisateurs')
@login_required
def utilisateurs():
    users = Utilisateur.query.order_by(Utilisateur.date_creation.desc()).all()
    return render_template('admin/utilisateurs.html', users=users)