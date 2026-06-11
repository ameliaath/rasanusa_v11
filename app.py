"""
app.py  ← titik masuk utama
────────────────────────────
Hanya berisi:
  1. create_app()  — application factory
  2. Registrasi blueprint
  3. Konfigurasi Flask-Login
  4. Blok __main__ untuk development

Tidak ada route, tidak ada model, tidak ada ML di sini.
"""
from flask import Flask

from extensions      import login_manager
from models.database import init_db
from models.user     import find_by_id

from routes.auth   import auth_bp
from routes.main   import main_bp
from routes.recipe import recipe_bp
from routes.api    import api_bp
from routes.admin  import admin_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = 'rasanusa_2024_ganti_dengan_key_yang_aman'

    # ── Inisialisasi extensions ───────────────────────────────────────────────
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        # id=0 adalah admin hardcoded (tidak ada di database)
        if str(user_id) == '0':
            from routes.auth import ADMIN_USER
            return ADMIN_USER
        return find_by_id(user_id)

    # ── Inisialisasi database ─────────────────────────────────────────────────
    init_db()

    # ── Daftarkan semua blueprint ─────────────────────────────────────────────
    app.register_blueprint(auth_bp)    # /login  /register  /logout
    app.register_blueprint(main_bp)    # /  /category  /favorites  /riwayat  /preferensi
    app.register_blueprint(recipe_bp)  # /search  /recipe/<id>
    app.register_blueprint(api_bp)     # /api/*
    app.register_blueprint(admin_bp)   # /admin/*

    return app

app = create_app()

# ── Entry point untuk development ────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)
