from flask import Blueprint, render_template, request, redirect, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import Income, Expense
from app.extensions import db

finance_bp = Blueprint('finance', __name__)

@finance_bp.route('/income', methods=['GET', 'POST'])
@login_required
def income():
    if request.method == 'POST':
        source = request.form['source']
        amount = float(request.form['amount'])

        if amount <= 0:
            flash('Amount must be greater than zero!', 'danger')
            return redirect('/income')

        new_income = Income(source=source, amount=amount, user_id=current_user.id)
        db.session.add(new_income)
        db.session.commit()
        flash('Income Added Successfully!', 'success')
        return redirect('/income')

    incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).all()
    return render_template('income.html', incomes=incomes)

@finance_bp.route('/delete-income/<int:id>')
@login_required
def delete_income(id):
    income = Income.query.get_or_404(id)
    if income.user_id != current_user.id:
        flash('Unauthorized Action!', 'danger')
        return redirect('/income')
    db.session.delete(income)
    db.session.commit()
    flash('Income Deleted Successfully!', 'success')
    return redirect('/income')

@finance_bp.route('/expense', methods=['GET', 'POST'])
@login_required
def expense():
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])

        if amount <= 0:
            flash('Amount must be greater than zero!', 'danger')
            return redirect('/expense')

        new_expense = Expense(category=category, amount=amount, user_id=current_user.id)
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense Added Successfully!', 'success')
        return redirect('/expense')

    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    return render_template('expense.html', expenses=expenses)

@finance_bp.route('/delete-expense/<int:id>')
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        flash('Unauthorized Action!', 'danger')
        return redirect('/expense')
    db.session.delete(expense)
    db.session.commit()
    flash('Expense Deleted Successfully!', 'success')
    return redirect('/expense')

@finance_bp.route('/budget')
@login_required
def budget():
    return render_template('budget.html')

@finance_bp.route('/goal')
@login_required
def goal():
    return render_template('goal.html')

@finance_bp.route('/report')
@login_required
def report():
    # Pass necessary data for report generation
    income_total = db.session.query(func.sum(Income.amount)).filter_by(user_id=current_user.id).scalar() or 0
    expense_total = db.session.query(func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar() or 0
    savings = income_total - expense_total
    health_score = int((savings / income_total) * 100) if income_total > 0 else 0
    health_score = max(0, min(100, health_score))
    
    return render_template('report.html', 
                           user=current_user, 
                           income=income_total, 
                           expense=expense_total, 
                           savings=savings,
                           health_score=health_score)
