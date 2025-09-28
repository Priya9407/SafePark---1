from flask import Flask
from flask_login import LoginManager
from controllers.login_controller import main as main_blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from models.model import db, User,Parking_lot
from seed_data import seed_data

app = Flask(__name__)
app.config['SECRET_KEY'] = 'its-a-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

app.register_blueprint(main_blueprint)
 
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        admin = User(
            name="Admin User",
            email="admin@example.com",
            address="Admin Address",
            username="admin",
            pin_code=600129,
            password=generate_password_hash('admin123'),
            role="admin"
        )
        user = User(
            name="user User",
            email="user@example.com",
            address="user Address",
            username="user",
            pin_code=600129,
            password=generate_password_hash('user123'),
            role="user"
        )
        db.session.add(admin)
        db.session.add(user)
        db.session.commit() 
        seed_data()
    app.run(debug=True)