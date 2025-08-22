import os
import logging
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
jwt = JWTManager()
bcrypt = Bcrypt()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure JWT
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY", "jwt-secret-string")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Tokens don't expire for simplicity

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///swiftpay.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
jwt.init_app(app)
bcrypt.init_app(app)

# Register blueprints
from auth import auth_bp
from user_routes import user_bp
from admin_routes import admin_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(admin_bp, url_prefix='/admin')

# Main route
@app.route('/')
def index():
    from flask import redirect, url_for
    return redirect(url_for('auth.login'))

# Template filter for current year
@app.template_filter('current_year')
def current_year_filter(s):
    return datetime.now().year

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
    
    # Create or update admin user
    from models import Admin
    admin = Admin.query.filter_by(email='admin@swiftpay.com').first()
    if admin:
        # Update existing admin with new secure credentials
        admin.username = 'swiftpay_admin'
        admin.password_hash = bcrypt.generate_password_hash('SwiftPay2024!Admin').decode('utf-8')
        db.session.commit()
        logging.info("Admin credentials updated: username=swiftpay_admin")
    else:
        # Create new admin user
        admin = Admin()
        admin.username = 'swiftpay_admin'
        admin.email = 'admin@swiftpay.com'
        admin.password_hash = bcrypt.generate_password_hash('SwiftPay2024!Admin').decode('utf-8')
        db.session.add(admin)
        db.session.commit()
        logging.info("Secure admin user created: username=swiftpay_admin")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
