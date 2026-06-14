from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from sqlalchemy import func
from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

from datetime import datetime

# ==================================
# APP CONFIGURATION
# ==================================

app = Flask(__name__)

app.config['SECRET_KEY'] = 'financeai_super_secure_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================================
# FLASK LOGIN SETUP
# ==================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

login_manager.login_message = "Please login first."

login_manager.login_message_category = "warning"

# ==================================
# USER MODEL
# ==================================

class User(UserMixin, db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    incomes = db.relationship(
        'Income',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )

    expenses = db.relationship(
        'Expense',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )

class Income(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    source = db.Column(
        db.String(100),
        nullable=False
    )

    date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

class Expense(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

# ==================================
# TRANSACTION MODEL
# (For Day 4 Dashboard Integration)
# ==================================

class Transaction(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    type = db.Column(
        db.String(20)
    )

    category = db.Column(
        db.String(100)
    )

    amount = db.Column(
        db.Float
    )

# ==================================
# USER LOADER
# ==================================

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))

# ==================================
# DASHBOARD
# ==================================

@app.route('/')
@login_required
def home():

    income_total = db.session.query(
        func.sum(Income.amount)
    ).filter_by(
        user_id=current_user.id
    ).scalar() or 0

    expense_total = db.session.query(
        func.sum(Expense.amount)
    ).filter_by(
        user_id=current_user.id
    ).scalar() or 0

    savings = income_total - expense_total

    budget_percent = int(
        (expense_total / income_total) * 100
    ) if income_total > 0 else 0

    recent_income = Income.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Income.date.desc()
    ).limit(3).all()

    recent_expense = Expense.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Expense.date.desc()
    ).limit(3).all()

    return render_template(
        'index.html',
        user=current_user,
        income=income_total,
        expense=expense_total,
        savings=savings,
        budget=budget_percent,
        recent_income=recent_income,
        recent_expense=recent_expense
    )

# ==================================
# REGISTER
# ==================================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':

        name = request.form['name'].strip()

        email = request.form['email'].strip().lower()

        password = request.form['password']

        confirm_password = request.form['confirm_password']

        if password != confirm_password:

            flash(
                'Passwords do not match!',
                'danger'
            )

            return redirect(url_for('register'))

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                'Email already registered!',
                'warning'
            )

            return redirect(url_for('register'))

        hashed_password = generate_password_hash(
            password
        )

        new_user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)

        db.session.commit()

        flash(
            'Registration Successful! Please Login.',
            'success'
        )

        return redirect(url_for('login'))

    return render_template('register.html')

# ==================================
# LOGIN
# ==================================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':

        email = request.form['email'].strip().lower()

        password = request.form['password']

        remember = request.form.get('remember')

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(
                user,
                remember=remember
            )

            flash(
                f'Welcome back, {user.name} 👋',
                'success'
            )

            return redirect(url_for('home'))

        flash(
            'Invalid Email or Password',
            'danger'
        )

        return redirect(url_for('login'))

    return render_template('login.html')

# ==================================
# LOGOUT
# ==================================

@app.route('/logout')
@login_required
def logout():

    logout_user()

    flash(
        'Logged Out Successfully!',
        'info'
    )

    return redirect(url_for('login'))

# ==================================
# PROFILE
# ==================================

@app.route('/profile')
@login_required
def profile():

    return render_template(
        'profile.html',
        user=current_user
    )

# ==================================
# INCOME PAGE
# ==================================

@app.route('/income', methods=['GET', 'POST'])
@login_required
def income():

    if request.method == 'POST':

        source = request.form['source']

        amount = float(
            request.form['amount']
        )

        if amount <= 0:

            flash(
                'Amount must be greater than zero!',
                'danger'
            )

            return redirect('/income')

        new_income = Income(
            source=source,
            amount=amount,
            user_id=current_user.id
        )

        db.session.add(new_income)

        db.session.commit()

        flash(
            'Income Added Successfully!',
            'success'
        )

        return redirect('/income')

    incomes = Income.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Income.date.desc()
    ).all()

    return render_template(
        'income.html',
        incomes=incomes
    )

# ==================================
# DELETE INCOME
# ==================================

@app.route('/delete-income/<int:id>')
@login_required
def delete_income(id):

    income = Income.query.get_or_404(id)

    if income.user_id != current_user.id:

        flash(
            'Unauthorized Action!',
            'danger'
        )

        return redirect('/income')

    db.session.delete(income)

    db.session.commit()

    flash(
        'Income Deleted Successfully!',
        'success'
    )

    return redirect('/income')

# ==================================
# EXPENSE PAGE
# ==================================

@app.route('/expense', methods=['GET', 'POST'])
@login_required
def expense():

    if request.method == 'POST':

        category = request.form['category']

        amount = float(
            request.form['amount']
        )

        # Validation
        if amount <= 0:

            flash(
                'Amount must be greater than zero!',
                'danger'
            )

            return redirect('/expense')

        new_expense = Expense(
            category=category,
            amount=amount,
            user_id=current_user.id
        )

        db.session.add(new_expense)

        db.session.commit()

        flash(
            'Expense Added Successfully!',
            'success'
        )

        return redirect('/expense')

    expenses = Expense.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Expense.date.desc()
    ).all()

    return render_template(
        'expense.html',
        expenses=expenses
    )

# ==================================
# DELETE EXPENSE
# ==================================

@app.route('/delete-expense/<int:id>')
@login_required
def delete_expense(id):

    expense = Expense.query.get_or_404(id)

    if expense.user_id != current_user.id:

        flash(
            'Unauthorized Action!',
            'danger'
        )

        return redirect('/expense')

    db.session.delete(expense)

    db.session.commit()

    flash(
        'Expense Deleted Successfully!',
        'success'
    )

    return redirect('/expense')

# ==================================
# BUDGET PAGE
# ==================================

@app.route('/budget')
@login_required
def budget():

    return render_template('budget.html')

# ==================================
# GOAL PAGE
# ==================================

@app.route('/goal')
@login_required
def goal():

    return render_template('goal.html')

# ==================================
# REPORT PAGE
# ==================================

@app.route('/report')
@login_required
def report():

    return render_template('report.html')

# ==================================
# SETTINGS PAGE
# ==================================

@app.route('/settings')
@login_required
def settings():

    return render_template('settings.html')

# ==================================
# 404 PAGE
# ==================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        '404.html'
    ), 404

# ==================================
# RUN APP
# ==================================

if __name__ == '__main__':

    with app.app_context():

        db.create_all()

    app.run(
        debug=True
    )