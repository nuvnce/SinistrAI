from app import create_app, db
from app.models import Utilisateur
import bcrypt

app = create_app()

with app.app_context():
    db.create_all()
    if not Utilisateur.query.filter_by(email='admin@sinistrai.com').first():
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        admin = Utilisateur(
            nom='Administrateur',
            email='admin@sinistrai.com',
            password_hash=password_hash,
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Compte admin créé.")

if __name__ == '__main__':
    app.run(debug=False)