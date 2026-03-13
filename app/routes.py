from urllib.parse import urlsplit
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required   
import sqlalchemy as sa
from app.forms import LoginForm, RegistrationForm, EditProfileForm, ExclusionForm
from app import app, db
from app.models import User, Exclusion, Policy
from datetime import datetime, timezone, date

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

@app.route('/')

@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    return render_template('user.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.route('/api/exclusions', methods=['POST'])
@login_required
def create_exclusion_api():
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': 'No JSON data received.'}), 400

    excluded_email = data.get('excluded_email', '').strip()
    until_value = data.get('until', '').strip()
    policy_id = data.get('policy_id')

    if not excluded_email:
        return jsonify({'success': False, 'message': 'E-Mail fehlt.'}), 400

    if not until_value:
        return jsonify({'success': False, 'message': 'Datum fehlt.'}), 400

    if not policy_id:
        return jsonify({'success': False, 'message': 'Policy fehlt.'}), 400

    try:
        policy_id = int(policy_id)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Ungültige Policy-ID.'}), 400

    policy = Policy.query.get(policy_id)
    if policy is None:
        return jsonify({'success': False, 'message': 'Policy nicht gefunden.'}), 404

    try:
        until_date = datetime.strptime(until_value, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Ungültiges Datumsformat. Bitte YYYY-MM-DD verwenden.'}), 400

    if until_date < date.today():
        return jsonify({'success': False, 'message': 'Das Datum muss heute oder in der Zukunft liegen.'}), 400

    try:
        exclusion = Exclusion(
            excluded_email=excluded_email,
            policy_id=policy.id,
            until=until_date,
            created_by_id=current_user.id
        )
        db.session.add(exclusion)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Exclusion wurde hinzugefügt.',
            'exclusion': {
                'id': exclusion.id,
                'excluded_email': exclusion.excluded_email,
                'policy_id': exclusion.policy_id,
                'policy_name': exclusion.policy.name,
                'until': exclusion.until.isoformat()
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler beim Speichern: {str(e)}'}), 500

@app.route('/exclusion_manager', methods=['GET', 'POST'])
@login_required
def exclusion_manager():
    form = ExclusionForm()
    exclusions = []

    policies = Policy.query.order_by(Policy.name).all()
    form.policy.choices = [(p.id, p.name) for p in policies]

    if request.method == "POST":
        if form.load_db.data:
            exclusions = Exclusion.query.filter_by(is_deleted=0).all()

    return render_template(
        "exclusion_manager.html",
        title="Exclusion Manager",
        form=form,
        exclusions=exclusions
    )

@app.route('/documentation')
@login_required
def documentation():
    return render_template("documentation.html", title="Documentation")