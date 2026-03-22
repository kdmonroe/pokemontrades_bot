from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if (username == current_app.config['PKMN_USERNAME'] and
                password == current_app.config['PKMN_PASSWORD']):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('inventory.index'))
        else:
            flash('Invalid credentials. Please try again.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
