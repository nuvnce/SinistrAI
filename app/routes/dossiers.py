from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('dossiers', __name__)

@bp.route('/dashboard')
@login_required
def index():
    return render_template('dashboard.html')