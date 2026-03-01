from flask_login import UserMixin
from app import db, login_manager
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    average_salary = db.Column(db.Float, nullable=True)
    categories = db.Column(db.String(500), nullable=True)
    transactions = db.relationship('Transaction', backref='author', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    payment_method = db.Column(db.String(50), nullable=True) # e.g. 'debit', 'credit'
    installments = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_fixed = db.Column(db.Boolean, default=False)
    fixed_expense_id = db.Column(db.Integer, db.ForeignKey('fixed_expense.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class FixedExpense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    default_amount = db.Column(db.Float, nullable=False)
    due_day = db.Column(db.Integer, nullable=False)  # 1 to 31
    category = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transactions = db.relationship('Transaction', backref='fixed_expense', lazy=True)
