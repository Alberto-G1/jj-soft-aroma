from flask import Flask, render_template
from config import Config
from models import db, AdminUser
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import bcrypt
import logging
import os

app = Flask(__name__)
app.config.from_object(Config)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}

db.init_app(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin.login'
login_manager.login_message = 'Please log in to access the admin panel.'

# ─── Logging ───
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))

from routes.admin_routes import admin_bp
from routes.customer_routes import customer_bp

app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(customer_bp, url_prefix='/')

with app.app_context():
    db.create_all()

    admin_username = (os.getenv('ADMIN_USERNAME') or '').strip()
    admin_password = (os.getenv('ADMIN_PASSWORD') or '').strip()
    create_default_admin = os.getenv('CREATE_DEFAULT_ADMIN', 'false').lower() == 'true'

    if admin_username and admin_password:
        if not AdminUser.query.filter_by(username=admin_username).first():
            hashed = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
            admin = AdminUser(username=admin_username, password_hash=hashed.decode('utf-8'))
            db.session.add(admin)
            db.session.commit()
            logger.info('Admin user created from environment variables.')
    elif create_default_admin and not app.config.get('IS_PRODUCTION'):
        if not AdminUser.query.filter_by(username='admin').first():
            hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            admin = AdminUser(username='admin', password_hash=hashed.decode('utf-8'))
            db.session.add(admin)
            db.session.commit()
            logger.warning('Development admin created — username: admin | password: admin123. Do not enable this in production.')
    else:
        logger.info('No default admin was created. Set ADMIN_USERNAME and ADMIN_PASSWORD in .env to create one.')


@app.after_request
def add_security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    if app.config.get('IS_PRODUCTION'):
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response

@app.route('/health')
def health_check():
    return {'status': 'ok'}, 200

@app.errorhandler(404)
def page_not_found(e):
    logger.warning(f"404 Not Found: {e}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"500 Internal Server Error: {e}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    debug_mode = app.config.get('DEBUG', False)
    app.run(debug=debug_mode)
