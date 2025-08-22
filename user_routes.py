from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from models import User, Transaction
from utils import format_currency, validate_account_number, is_suspicious_activity
import logging

user_bp = Blueprint('user', __name__)

def require_login(f):
    """Decorator to require user login"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@user_bp.route('/dashboard')
@require_login
def dashboard():
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Get recent transactions
    recent_transactions = Transaction.query.filter(
        (Transaction.from_user_id == user.id) | (Transaction.to_user_id == user.id)
    ).order_by(Transaction.created_at.desc()).limit(5).all()
    
    # Calculate referral earnings
    referral_earnings = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.to_user_id == user.id,
        Transaction.transaction_type == 'referral_bonus'
    ).scalar() or 0
    
    return render_template('user/dashboard.html', 
                         user=user, 
                         recent_transactions=recent_transactions,
                         referral_earnings=referral_earnings,
                         format_currency=format_currency)

@user_bp.route('/transfer', methods=['GET', 'POST'])
@require_login
def transfer():
    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        account_number = request.form.get('account_number')
        amount = float(request.form.get('amount', 0))
        description = request.form.get('description', '')
        
        # Validation
        if not validate_account_number(account_number):
            flash('Invalid account number format', 'error')
            return render_template('user/transfer.html')
        
        if amount <= 0:
            flash('Amount must be greater than 0', 'error')
            return render_template('user/transfer.html')
        
        if amount > user.balance:
            flash('Insufficient balance', 'error')
            return render_template('user/transfer.html')
        
        # Find recipient
        recipient = User.query.filter_by(account_number=account_number).first()
        if not recipient:
            flash('Recipient account not found', 'error')
            return render_template('user/transfer.html')
        
        if recipient.id == user.id:
            flash('Cannot transfer to your own account', 'error')
            return render_template('user/transfer.html')
        
        # Check for suspicious activity
        if is_suspicious_activity(user, amount, 'transfer'):
            flash('Transaction flagged for review. Please contact support.', 'warning')
            # Create pending transaction
            transaction = Transaction(
                from_user_id=user.id,
                to_user_id=recipient.id,
                amount=amount,
                transaction_type='transfer',
                status='pending',
                description=f'Transfer to {recipient.username}: {description}'
            )
            db.session.add(transaction)
            db.session.commit()
            return render_template('user/transfer.html')
        
        # Process transfer
        user.balance -= amount
        recipient.balance += amount
        
        # Create transaction record
        transaction = Transaction(
            from_user_id=user.id,
            to_user_id=recipient.id,
            amount=amount,
            transaction_type='transfer',
            status='completed',
            description=f'Transfer to {recipient.username}: {description}'
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Successfully transferred {format_currency(amount)} to {recipient.username}', 'success')
        return redirect(url_for('user.dashboard'))
    
    return render_template('user/transfer.html')

@user_bp.route('/add_funds', methods=['GET', 'POST'])
@require_login
def add_funds():
    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        amount = float(request.form.get('amount', 0))
        
        if amount <= 0:
            flash('Amount must be greater than 0', 'error')
            return render_template('user/add_funds.html')
        
        # In a real app, this would integrate with a payment gateway
        # For demo purposes, we'll simulate successful funding
        user.balance += amount
        
        # Create transaction record
        transaction = Transaction(
            to_user_id=user.id,
            amount=amount,
            transaction_type='deposit',
            status='completed',
            description='Account funding'
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Successfully added {format_currency(amount)} to your wallet', 'success')
        return redirect(url_for('user.dashboard'))
    
    return render_template('user/add_funds.html')

@user_bp.route('/withdraw', methods=['GET', 'POST'])
@require_login
def withdraw():
    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        amount = float(request.form.get('amount', 0))
        bank_account = request.form.get('bank_account')
        
        if amount <= 0:
            flash('Amount must be greater than 0', 'error')
            return render_template('user/withdraw.html')
        
        if amount > user.balance:
            flash('Insufficient balance', 'error')
            return render_template('user/withdraw.html')
        
        if not bank_account:
            flash('Bank account number is required', 'error')
            return render_template('user/withdraw.html')
        
        # In a real app, this would integrate with banking APIs
        # For demo purposes, we'll simulate successful withdrawal
        user.balance -= amount
        
        # Create transaction record
        transaction = Transaction(
            from_user_id=user.id,
            amount=amount,
            transaction_type='withdrawal',
            status='completed',
            description=f'Withdrawal to bank account {bank_account}'
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Successfully withdrew {format_currency(amount)} to your bank account', 'success')
        return redirect(url_for('user.dashboard'))
    
    return render_template('user/withdraw.html')

@user_bp.route('/transactions')
@require_login
def transactions():
    user = User.query.get(session['user_id'])
    page = request.args.get('page', 1, type=int)
    
    transactions = Transaction.query.filter(
        (Transaction.from_user_id == user.id) | (Transaction.to_user_id == user.id)
    ).order_by(Transaction.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('user/transactions.html', 
                         transactions=transactions, 
                         format_currency=format_currency,
                         user=user)
