"""
routes/admin.py
───────────────
Blueprint untuk halaman admin.
Hanya bisa diakses oleh admin hardcoded (username=admin, password=admin123).
URL prefix: /admin
"""
import os, re
from functools import wraps
from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify)
from flask_login import login_required, current_user

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ── Guard decorator ───────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Halaman ini hanya untuk admin.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── Helper: akses df global dari ml_engine ───────────────────────────────────

def _get_df():
    import ml_engine
    return ml_engine.df

def _save_df(df):
    """Simpan df ke CSV dan reload ml_engine global."""
    import ml_engine
    csv_path = os.path.join(
        os.path.dirname(ml_engine.__file__),
        'data', 'dataset-gabungan-clean.csv'
    )
    df.to_csv(csv_path, index=False)
    # Reload supaya perubahan langsung berlaku
    _reload_ml()

def _reload_ml():
    """Reload dataset dan TF-IDF tanpa restart server."""
    import importlib, ml_engine
    importlib.reload(ml_engine)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    df       = _get_df()
    total    = len(df)
    cats     = df['Category'].value_counts().to_dict()
    # Ambil 10 resep terbaru (index terbesar)
    recent   = df.tail(10)[['id','Title','Category','Loves']].iloc[::-1]
    recent_list = [
        {'id': int(r['id']), 'title': r['Title'],
         'category': r['Category'], 'loves': int(r['Loves'])}
        for _, r in recent.iterrows()
    ]
    return render_template('admin/dashboard.html',
        total=total, cats=cats, recent=recent_list)


# ── Daftar resep (paginasi) ───────────────────────────────────────────────────

@admin_bp.route('/recipes')
@login_required
@admin_required
def recipes():
    df      = _get_df()
    q       = request.args.get('q', '').strip()
    cat     = request.args.get('cat', '')
    page    = max(1, int(request.args.get('page', 1)))
    per_page = 20

    filtered = df.copy()
    if q:
        filtered = filtered[filtered['Title'].str.contains(q, case=False, na=False)]
    if cat:
        filtered = filtered[filtered['Category'] == cat]

    total   = len(filtered)
    pages   = max(1, (total + per_page - 1) // per_page)
    page    = min(page, pages)
    paged   = filtered.iloc[(page-1)*per_page : page*per_page]

    rows = [
        {'id': int(r['id']), 'title': r['Title'],
         'category': r['Category'], 'loves': int(r['Loves'])}
        for _, r in paged.iterrows()
    ]
    categories = sorted(df['Category'].unique().tolist())
    return render_template('admin/recipes.html',
        rows=rows, total=total, page=page, pages=pages,
        q=q, cat=cat, categories=categories, per_page=per_page)


# ── Tambah resep ──────────────────────────────────────────────────────────────

@admin_bp.route('/recipes/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_recipe():
    df         = _get_df()
    categories = sorted(df['Category'].unique().tolist())

    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        category    = request.form.get('category', '').strip()
        new_cat     = request.form.get('new_category', '').strip()
        ingredients = request.form.get('ingredients', '').strip()
        steps       = request.form.get('steps', '').strip()
        loves       = request.form.get('loves', '0').strip()
        url         = request.form.get('url', '').strip()
        keywords    = request.form.get('keywords', '').strip()

        # Validasi
        errors = []
        if not title:        errors.append('Judul resep wajib diisi.')
        if not ingredients:  errors.append('Bahan-bahan wajib diisi.')
        if not steps:        errors.append('Langkah memasak wajib diisi.')

        final_cat = new_cat if new_cat else category
        if not final_cat:    errors.append('Kategori wajib dipilih atau diisi.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('admin/recipe_form.html',
                mode='add', categories=categories,
                data=request.form)

        import pandas as pd
        new_row = pd.DataFrame([{
            'Title'      : title,
            'Category'   : final_cat.lower(),
            'Ingredients': ingredients,
            'Steps'      : steps,
            'Loves'      : int(loves) if loves.isdigit() else 0,
            'URL'        : url,
            'Keywords'   : keywords,
        }])

        import ml_engine
        updated = pd.concat([ml_engine.df, new_row], ignore_index=True)
        updated['id'] = updated.index
        _save_df(updated.drop(columns=['id','ingredients_clean','tags'], errors='ignore'))
        flash(f'Resep "{title}" berhasil ditambahkan! 🎉', 'success')
        return redirect(url_for('admin.recipes'))

    return render_template('admin/recipe_form.html',
        mode='add', categories=categories, data={})


# ── Edit resep ────────────────────────────────────────────────────────────────

@admin_bp.route('/recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_recipe(recipe_id):
    df         = _get_df()
    categories = sorted(df['Category'].unique().tolist())

    if recipe_id < 0 or recipe_id >= len(df):
        flash('Resep tidak ditemukan.', 'danger')
        return redirect(url_for('admin.recipes'))

    row = df.iloc[recipe_id]

    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        category    = request.form.get('category', '').strip()
        new_cat     = request.form.get('new_category', '').strip()
        ingredients = request.form.get('ingredients', '').strip()
        steps       = request.form.get('steps', '').strip()
        loves       = request.form.get('loves', '0').strip()
        url_val     = request.form.get('url', '').strip()
        keywords    = request.form.get('keywords', '').strip()

        errors = []
        if not title:       errors.append('Judul resep wajib diisi.')
        if not ingredients: errors.append('Bahan-bahan wajib diisi.')
        if not steps:       errors.append('Langkah memasak wajib diisi.')

        final_cat = new_cat if new_cat else category
        if not final_cat:   errors.append('Kategori wajib dipilih atau diisi.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('admin/recipe_form.html',
                mode='edit', recipe_id=recipe_id,
                categories=categories, data=request.form)

        import ml_engine
        ml_engine.df.at[recipe_id, 'Title']       = title
        ml_engine.df.at[recipe_id, 'Category']    = final_cat.lower()
        ml_engine.df.at[recipe_id, 'Ingredients'] = ingredients
        ml_engine.df.at[recipe_id, 'Steps']       = steps
        ml_engine.df.at[recipe_id, 'Loves']       = int(loves) if loves.isdigit() else 0
        ml_engine.df.at[recipe_id, 'URL']         = url_val
        ml_engine.df.at[recipe_id, 'Keywords']    = keywords

        _save_df(ml_engine.df.drop(columns=['id','ingredients_clean','tags'], errors='ignore'))
        flash(f'Resep "{title}" berhasil diperbarui! ✅', 'success')
        return redirect(url_for('admin.recipes'))

    # GET – isi form dengan data yang sudah ada
    # Konversi -- ke newline untuk tampilan di textarea
    ings_display  = '\n'.join(i.strip() for i in str(row['Ingredients']).split('--') if i.strip())
    steps_display = '\n'.join(s.strip() for s in str(row['Steps']).split('--') if s.strip())

    data = {
        'title'      : row['Title'],
        'category'   : row['Category'],
        'ingredients': ings_display,
        'steps'      : steps_display,
        'loves'      : int(row['Loves']),
        'url'        : row.get('URL', ''),
        'keywords'   : row.get('Keywords', ''),
    }
    return render_template('admin/recipe_form.html',
        mode='edit', recipe_id=recipe_id,
        categories=categories, data=data)


# ── Hapus resep ───────────────────────────────────────────────────────────────

@admin_bp.route('/recipes/<int:recipe_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_recipe(recipe_id):
    import ml_engine
    df = _get_df()
    if recipe_id < 0 or recipe_id >= len(df):
        flash('Resep tidak ditemukan.', 'danger')
        return redirect(url_for('admin.recipes'))

    title   = df.iloc[recipe_id]['Title']
    updated = df.drop(index=recipe_id).reset_index(drop=True)
    updated['id'] = updated.index
    _save_df(updated.drop(columns=['id','ingredients_clean','tags'], errors='ignore'))
    flash(f'Resep "{title}" berhasil dihapus.', 'success')
    return redirect(url_for('admin.recipes'))


# ── 403 / error handler ───────────────────────────────────────────────────────

@admin_bp.app_errorhandler(403)
def forbidden(e):
    return render_template('admin/403.html'), 403
