"""
extensions.py
Semua Flask extensions di-init di sini (tanpa app),
supaya tidak ada circular import antar module.
"""
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Silakan login terlebih dahulu.'
login_manager.login_message_category = 'warning'
