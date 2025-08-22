from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app import db, bcrypt
from models import Admin, User, Transaction, Referral
from utils import format_currency
from datetime import datetime, timedelta
import logging

admin_bp = Blueprint('admin', __name__)

def require_admin(f):
    """Decorator to require admin login"""
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Admin access required', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and password and bcrypt.check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            admin.last_login = datetime.utcnow()
            db.session.commit()
            
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('admin_id', None)
    flash('Admin logged out successfully', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@require_admin
def dashboard():
    # Get key metrics
    total_users = User.query.count()
    total_transactions = Transaction.query.count()
    total_volume = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.status == 'completed'
    ).scalar() or 0
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()
    
    # Suspicious activity
    suspicious_transactions = Transaction.query.filter(
        Transaction.status == 'pending',
        Transaction.amount > 50000
    ).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_transactions=total_transactions,
                         total_volume=total_volume,
                         recent_users=recent_users,
                         recent_transactions=recent_transactions,
                         suspicious_transactions=suspicious_transactions,
                         format_currency=format_currency)

@admin_bp.route('/users')
@require_admin
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.account_number.contains(search))
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search, format_currency=format_currency)

@admin_bp.route('/users/<int:user_id>/toggle_suspension', methods=['POST'])
@require_admin
def toggle_user_suspension(user_id):
    user = User.query.get_or_404(user_id)
    user.is_suspended = not user.is_suspended
    db.session.commit()
    
    status = "suspended" if user.is_suspended else "reactivated"
    flash(f'User {user.username} has been {status}', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/add_balance', methods=['POST'])
@require_admin
def add_user_balance(user_id):
    user = User.query.get_or_404(user_id)
    amount = float(request.form.get('amount', 0))
    
    if amount <= 0:
        flash('Amount must be greater than 0', 'error')
        return redirect(url_for('admin.users'))
    
    user.balance += amount
    
    # Create transaction record
    transaction = Transaction()
    transaction.to_user_id = user.id
    transaction.amount = amount
    transaction.transaction_type = 'deposit'
    transaction.status = 'completed'
    transaction.description = 'Admin balance adjustment'
    db.session.add(transaction)
    db.session.commit()
    
    flash(f'Added {format_currency(amount)} to {user.username} balance', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/transactions')
@require_admin
def transactions():
    page = request.args.get('page', 1, type=int)
    transaction_type = request.args.get('type', '')
    status = request.args.get('status', '')
    
    query = Transaction.query
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if status:
        query = query.filter(Transaction.status == status)
    
    transactions = query.order_by(Transaction.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/transactions.html', 
                         transactions=transactions,
                         transaction_type=transaction_type,
                         status=status,
                         format_currency=format_currency)

@admin_bp.route('/transactions/<int:transaction_id>/approve', methods=['POST'])
@require_admin
def approve_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    if transaction.status != 'pending':
        flash('Transaction is not pending', 'error')
        return redirect(url_for('admin.transactions'))
    
    # Process the transaction
    if transaction.transaction_type == 'transfer':
        sender = User.query.get(transaction.from_user_id)
        recipient = User.query.get(transaction.to_user_id)
        
        if sender.balance >= transaction.amount:
            sender.balance -= transaction.amount
            recipient.balance += transaction.amount
            transaction.status = 'completed'
        else:
            transaction.status = 'failed'
            transaction.description += ' (Insufficient funds)'
    
    db.session.commit()
    flash(f'Transaction {transaction_id} has been processed', 'success')
    return redirect(url_for('admin.transactions'))

@admin_bp.route('/analytics')
@require_admin
def analytics():
    # Get data for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Daily transaction volumes
    daily_volumes = db.session.query(
        db.func.date(Transaction.created_at).label('date'),
        db.func.sum(Transaction.amount).label('volume')
    ).filter(
        Transaction.created_at >= thirty_days_ago,
        Transaction.status == 'completed'
    ).group_by(db.func.date(Transaction.created_at)).all()
    
    # User growth
    daily_signups = db.session.query(
        db.func.date(User.created_at).label('date'),
        db.func.count(User.id).label('signups')
    ).filter(
        User.created_at >= thirty_days_ago
    ).group_by(db.func.date(User.created_at)).all()
    
    # Top users by balance
    top_users = User.query.order_by(User.balance.desc()).limit(10).all()
    
    # Transaction types breakdown
    transaction_types = db.session.query(
        Transaction.transaction_type,
        db.func.count(Transaction.id).label('count'),
        db.func.sum(Transaction.amount).label('volume')
    ).filter(Transaction.status == 'completed').group_by(Transaction.transaction_type).all()
    
    return render_template('admin/analytics.html',
                         daily_volumes=daily_volumes,
                         daily_signups=daily_signups,
                         top_users=top_users,
                         transaction_types=transaction_types,
                         format_currency=format_currency)
