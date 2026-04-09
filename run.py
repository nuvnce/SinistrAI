from app import create_app, db
from app.models import Utilisateur
import bcrypt

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Base de données initialisée !")

        # Création du compte admin au premier démarrage uniquement
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
            print("✅ Compte admin créé : admin@sinistrai.com / admin123")
        else:
            print("ℹ️ Compte admin déjà existant.")

    app.run(debug=True)