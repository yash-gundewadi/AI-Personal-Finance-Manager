from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import Income, Expense
from app.extensions import db

dashboard_bp = Blueprint('dashboard', __name__)

def generate_ai_insights(income_total, expense_total, savings):
    insights = []
    
    # 1. Expense vs Income Ratio
    if income_total > 0:
        expense_ratio = expense_total / income_total
        if expense_ratio > 0.7:
            insights.append({
                'icon': '⚠️',
                'message': 'Your expenses exceed 70% of your income. Consider reducing discretionary spending.',
                'confidence': 95,
                'type': 'warning'
            })
        elif expense_ratio < 0.4:
            insights.append({
                'icon': '🌟',
                'message': 'Excellent! Your expense ratio is under 40%. You are saving efficiently.',
                'confidence': 90,
                'type': 'success'
            })
            
    # 2. Savings check
    if savings > 0 and income_total > 0:
        savings_ratio = savings / income_total
        if savings_ratio > 0.2:
            insights.append({
                'icon': '📈',
                'message': f'Great job! You are saving {int(savings_ratio*100)}% of your income.',
                'confidence': 88,
                'type': 'success'
            })
    elif savings < 0:
        insights.append({
            'icon': '🚨',
            'message': 'You are spending more than you earn. Review your budget immediately.',
            'confidence': 98,
            'type': 'danger'
        })

    # Return default if none triggered
    if not insights:
        insights.append({
            'icon': '💡',
            'message': 'Keep tracking your expenses to receive personalized AI financial insights.',
            'confidence': 70,
            'type': 'info'
        })
        
    return insights

@dashboard_bp.route('/')
@login_required
def home():
    income_total = db.session.query(func.sum(Income.amount)).filter_by(user_id=current_user.id).scalar() or 0
    expense_total = db.session.query(func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar() or 0
    savings = income_total - expense_total
    
    budget_percent = int((expense_total / income_total) * 100) if income_total > 0 else 0
    
    health_score = int((savings / income_total) * 100) if income_total > 0 else 0
    health_score = max(0, min(100, health_score)) # Clamp between 0 and 100

    recent_income = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).limit(5).all()
    recent_expense = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(5).all()

    all_transactions = []
    for inc in recent_income:
        all_transactions.append({
            'type': 'income',
            'desc': inc.source,
            'amount': inc.amount,
            'date': inc.date
        })
    for exp in recent_expense:
        all_transactions.append({
            'type': 'expense',
            'desc': exp.category,
            'amount': exp.amount,
            'date': exp.date
        })
        
    all_transactions.sort(key=lambda x: x['date'], reverse=True)
    recent_transactions = all_transactions[:5]
    
    # Generate Insights
    ai_insights = generate_ai_insights(income_total, expense_total, savings)
    
    # Generate Chart Data (Pie Chart - Expense Categories)
    expense_categories = db.session.query(
        Expense.category, func.sum(Expense.amount)
    ).filter_by(user_id=current_user.id).group_by(Expense.category).all()
    
    pie_labels = [cat[0] for cat in expense_categories]
    pie_data = [cat[1] for cat in expense_categories]

    return render_template(
        'index.html',
        user=current_user,
        income=income_total,
        expense=expense_total,
        savings=savings,
        budget=budget_percent,
        health_score=health_score,
        recent_transactions=recent_transactions,
        ai_insights=ai_insights,
        pie_labels=pie_labels,
        pie_data=pie_data
    )

@dashboard_bp.route('/settings')
@login_required
def settings():
    return render_template('settings.html')
