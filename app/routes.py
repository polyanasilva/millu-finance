import os
from google import genai
from flask import Blueprint, render_template, url_for, flash, redirect, request
from app import db, bcrypt
from app.models import User, Transaction, FixedExpense
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime, date, timedelta
import calendar

main = Blueprint('main', __name__)

@main.route("/")
@login_required
def dashboard():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    balance = total_income - total_expense
    
    expense_categories = {}
    for t in transactions:
        if t.type == 'expense':
            expense_categories[t.category] = expense_categories.get(t.category, 0) + t.amount
            
    return render_template('dashboard.html', 
                           title='Início',
                           total_income=total_income,
                           total_expense=total_expense,
                           balance=balance,
                           categories=list(expense_categories.keys()),
                           category_amounts=list(expense_categories.values()),
                           transactions=transactions[:5])  # Ultimas 5 transacoes

@main.route("/add_expense", methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        title = request.form.get('title')
        amount = float(request.form.get('amount'))
        category = request.form.get('category')
        payment_method = request.form.get('payment_method')
        installments = True if request.form.get('installments') == 'on' else False
        
        transaction = Transaction(
            type='expense', title=title, amount=amount, category=category,
            payment_method=payment_method, installments=installments,
            author=current_user
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Gasto cadastrado com sucesso!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('add_expense.html', title='Cadastrar Gasto')

@main.route("/add_income", methods=['GET', 'POST'])
@login_required
def add_income():
    if request.method == 'POST':
        title = request.form.get('title')
        amount = float(request.form.get('amount'))
        category = request.form.get('category') # Pode ser "Salário", "Freelance", etc.
        
        transaction = Transaction(
            type='income', title=title, amount=amount, category=category,
            author=current_user
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Receita cadastrada com sucesso!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('add_income.html', title='Cadastrar Receita')

@main.route("/fixed_expenses")
@login_required
def fixed_expenses():
    today = date.today()
    month = int(request.args.get('month', today.month))
    year = int(request.args.get('year', today.year))
    
    # Calculate previous and next months for navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    # Get all fixed expenses for this user
    all_fixed = FixedExpense.query.filter_by(user_id=current_user.id).all()
    
    # Get transactions mapped to fixed expenses ONLY IN THIS MONTH
    # to check what has already been paid
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)
    
    paid_transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.is_fixed == True,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()
    
    paid_expense_ids = {t.fixed_expense_id: t for t in paid_transactions if t.fixed_expense_id}
    
    # Create a mapping of day -> list of expense dicts
    expenses_by_day = {}
    for expense in all_fixed:
        day = expense.due_day
        # Adjust if month has fewer days
        max_days = calendar.monthrange(year, month)[1]
        adjusted_day = min(day, max_days)
        
        is_paid = expense.id in paid_expense_ids
        paid_amount = paid_expense_ids[expense.id].amount if is_paid else 0
        
        if adjusted_day not in expenses_by_day:
            expenses_by_day[adjusted_day] = []
            
        expenses_by_day[adjusted_day].append({
            'obj': expense,
            'is_paid': is_paid,
            'paid_amount': paid_amount
        })
        
    return render_template('fixed_expenses.html', 
                           title='Gastos Fixos',
                           calendar=cal, 
                           month=month, 
                           year=year,
                           month_name=month_name,
                           prev_month=prev_month, prev_year=prev_year,
                           next_month=next_month, next_year=next_year,
                           expenses_by_day=expenses_by_day,
                           today=today)

@main.route("/add_fixed_expense", methods=['GET', 'POST'])
@login_required
def add_fixed_expense():
    if request.method == 'POST':
        title = request.form.get('title')
        default_amount = float(request.form.get('default_amount'))
        due_day = int(request.form.get('due_day'))
        category = request.form.get('category')
        
        fixed_expense = FixedExpense(
            title=title, default_amount=default_amount, due_day=due_day, 
            category=category, user_id=current_user.id
        )
        db.session.add(fixed_expense)
        db.session.commit()
        flash('Gasto Fixo cadastrado com sucesso!', 'success')
        return redirect(url_for('main.fixed_expenses'))
    return render_template('add_fixed_expense.html', title='Novo Gasto Fixo')

@main.route("/pay_fixed_expense/<int:expense_id>", methods=['POST'])
@login_required
def pay_fixed_expense(expense_id):
    expense = FixedExpense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id:
        flash('Sem permissão.', 'danger')
        return redirect(url_for('main.fixed_expenses'))
        
    try:
        actual_amount = float(request.form.get('amount'))
        month = int(request.form.get('month', date.today().month))
        year = int(request.form.get('year', date.today().year))
        
        # Payment Date
        payment_date = datetime(year, month, min(expense.due_day, calendar.monthrange(year, month)[1]))
        
        transaction = Transaction(
            type='expense', title=f"{expense.title} ({month}/{year})", 
            amount=actual_amount, category=expense.category,
            payment_method='debit', # Default or could be asked in modal
            is_fixed=True, fixed_expense_id=expense.id,
            date=payment_date, author=current_user
        )
        db.session.add(transaction)
        db.session.commit()
        flash(f'Conta de {expense.title} marcada como paga!', 'success')
    except Exception as e:
        flash(f'Erro ao registrar pagamento: {str(e)}', 'danger')
        
    return redirect(url_for('main.fixed_expenses', month=month, year=year))

@main.route("/chat", methods=['GET', 'POST'])
@login_required
def chat():
    api_key = os.environ.get('GEMINI_API_KEY')
    chat_response = None
    
    if request.method == 'POST':
        if not api_key or api_key == 'YOUR_API_KEY_HERE':
            chat_response = "A chave da API do Gemini não está configurada no arquivo .env. Por favor, adicione sua GEMINI_API_KEY."
        else:
            client = genai.Client(api_key=api_key)
            
            user_message = request.form.get('message')
            
            # Build context dynamically
            transactions = Transaction.query.filter_by(user_id=current_user.id).all()
            total_income = sum(t.amount for t in transactions if t.type == 'income')
            total_expense = sum(t.amount for t in transactions if t.type == 'expense')
            
            # Fetch fixed expenses status for the current month
            today = date.today()
            all_fixed = FixedExpense.query.filter_by(user_id=current_user.id).all()
            start_date = datetime(today.year, today.month, 1)
            end_date = datetime(today.year, today.month, calendar.monthrange(today.year, today.month)[1], 23, 59, 59)
            
            paid_fixed_transactions = Transaction.query.filter(
                Transaction.user_id == current_user.id,
                Transaction.is_fixed == True,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).all()
            paid_fixed_ids = [t.fixed_expense_id for t in paid_fixed_transactions if t.fixed_expense_id]
            
            context = f"Você é 'Milu', uma assistente financeira engajada e inteligente. O usuário atual é {current_user.name}. Ele tem {current_user.age} anos, média salarial declarada: R$ {current_user.average_salary}.\n"
            context += f"Resumo atual: Total de Receitas: R$ {total_income}. Total de Gastos: R$ {total_expense}. Saldo restante: R$ {total_income - total_expense}.\n\n"
            
            if all_fixed:
                context += "O usuário possui as seguintes Contas Fixas cadastradas este mês:\n"
                for fx in all_fixed:
                    status = "✅ PAGA" if fx.id in paid_fixed_ids else "❌ PENDENTE"
                    context += f"- Conta: {fx.title} | Valor Base: R$ {fx.default_amount} | Vence no dia: {fx.due_day} | Status este mês: {status}\n"
                context += "\n"
                
            if transactions:
                context += "Aqui está o histórico geral de transações do usuário (das mais antigas para as mais recentes):\n"
                for t in transactions[-20:]:  # Limiting to last 20 to avoid huge context
                    context += f"- [{t.date.strftime('%d/%m/%Y')}] {t.type.capitalize()} | {t.category} | {t.payment_method} | R$ {t.amount} | Descrição: {t.title}\n"
            else:
                context += "O usuário não possui nenhuma transação cadastrada ainda.\n"
                
            context += f"\nResponda diretamente e de modo prestativo em português à pergunta do usuário: \"{user_message}\". Pode usar markdown na sua resposta, seja amigável. Não precisa dizer que você é uma IA, aja como a assistente financeira do app."
            
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=context
                )
                chat_response = response.text
            except Exception as e:
                chat_response = f"Erro na IA: {str(e)}"
                
    return render_template('chat.html', title='Chat IA', response=chat_response)

@main.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.age = int(request.form.get('age'))
        current_user.average_salary = float(request.form.get('average_salary'))
        current_user.categories = request.form.get('categories')
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('main.settings'))
        
    return render_template('settings.html', title='Configurações de Perfil')

@main.route("/history")
@login_required
def history():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    return render_template('history.html', title='Histórico de Transações', transactions=transactions)

@main.route("/delete_transaction/<int:transaction_id>", methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.author != current_user:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.history'))
    db.session.delete(transaction)
    db.session.commit()
    flash('Transação excluída.', 'success')
    return redirect(url_for('main.history'))

@main.route("/edit_transaction/<int:transaction_id>", methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.author != current_user:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.history'))
        
    if request.method == 'POST':
        transaction.title = request.form.get('title')
        transaction.amount = float(request.form.get('amount'))
        transaction.category = request.form.get('category')
        db.session.commit()
        flash('Transação atualizada.', 'success')
        return redirect(url_for('main.history'))
        
    return render_template('edit_transaction.html', title='Editar Transação', transaction=transaction)

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        age = request.form.get('age')
        average_salary = request.form.get('average_salary')
        categories = request.form.get('categories') # E.g., "Alimentação, Transporte, Lazer"
        
        # Check if email exists
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Este e-mail já está em uso. Faça login.', 'danger')
            return redirect(url_for('main.register'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            name=name, email=email, password=hashed_password, 
            age=age, average_salary=average_salary, categories=categories
        )
        db.session.add(user)
        db.session.commit()
        flash('Sua conta foi criada com sucesso! Você já pode fazer login', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Cadastro')

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login não realizado. Por favor, verifique e-mail e senha', 'danger')
    return render_template('login.html', title='Login')

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.login'))
