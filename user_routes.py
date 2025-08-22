from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app import db
from models import User, Transaction, OTP
from utils import format_currency, validate_account_number, is_suspicious_activity
from datetime import datetime, timedelta
import logging
import random
import string

user_bp = Blueprint('user', __name__)

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

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
            return render_template('user/transfer.html', user=user, format_currency=format_currency)
        
        if amount <= 0:
            flash('Amount must be greater than 0', 'error')
            return render_template('user/transfer.html', user=user, format_currency=format_currency)
        
        if amount > user.balance:
            flash('Insufficient balance', 'error')
            return render_template('user/transfer.html', user=user, format_currency=format_currency)
        
        # Find recipient
        recipient = User.query.filter_by(account_number=account_number).first()
        if not recipient:
            flash('Recipient account not found', 'error')
            return render_template('user/transfer.html', user=user, format_currency=format_currency)
        
        if recipient.id == user.id:
            flash('Cannot transfer to your own account', 'error')
            return render_template('user/transfer.html', user=user, format_currency=format_currency)
        
        # Check for suspicious activity
        if is_suspicious_activity(user, amount, 'transfer'):
            flash('Transaction flagged for review. Please contact support.', 'warning')
            # Create pending transaction
            transaction = Transaction()
            transaction.from_user_id = user.id
            transaction.to_user_id = recipient.id
            transaction.amount = amount
            transaction.transaction_type = 'transfer'
            transaction.status = 'pending'
            transaction.description = f'Transfer to {recipient.username}: {description}'
            db.session.add(transaction)
            db.session.commit()
            return render_template('user/transfer.html', user=user, format_currency=format_currency)
        
        # Generate and send OTP for transfer verification
        otp_code = generate_otp()
        
        # Delete any existing unused OTPs for this user
        OTP.query.filter_by(user_id=user.id, is_used=False).delete()
        
        # Create new OTP
        otp = OTP()
        otp.user_id = user.id
        otp.otp_code = otp_code
        otp.purpose = 'transfer'
        otp.recipient_account = account_number
        otp.amount = amount
        otp.expires_at = datetime.utcnow() + timedelta(minutes=10)
        db.session.add(otp)
        
        # Create pending transaction
        transaction = Transaction()
        transaction.from_user_id = user.id
        transaction.to_user_id = recipient.id
        transaction.amount = amount
        transaction.transaction_type = 'transfer'
        transaction.status = 'pending'
        transaction.description = f'Transfer to {recipient.username}: {description}'
        db.session.add(transaction)
        db.session.commit()
        
        # Store transaction details in session for OTP verification
        session['pending_transfer'] = {
            'transaction_id': transaction.id,
            'otp_id': otp.id,
            'recipient_name': recipient.username,
            'amount': amount,
            'account_number': account_number,
            'description': description
        }
        
        # In a real app, send OTP via SMS here
        # For demo purposes, we'll log it
        logging.info(f"Transfer OTP for user {user.username}: {otp_code}")
        
        flash(f'OTP sent successfully! Check your phone for the verification code.', 'info')
        return redirect(url_for('user.verify_transfer_otp'))
    
    user = User.query.get(session['user_id'])
    return render_template('user/transfer.html', user=user, format_currency=format_currency)

@user_bp.route('/add_funds')
@require_login
def add_funds():
    user = User.query.get(session['user_id'])
    return render_template('user/add_funds.html', user=user)

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
        transaction = Transaction()
        transaction.from_user_id = user.id
        transaction.amount = amount
        transaction.transaction_type = 'withdrawal'
        transaction.status = 'completed'
        transaction.description = f'Withdrawal to bank account {bank_account}'
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

@user_bp.route('/verify_account', methods=['POST'])
@require_login
def verify_account():
    data = request.get_json()
    account_number = data.get('account_number')
    
    if not account_number or not validate_account_number(account_number):
        return jsonify({'success': False, 'message': 'Invalid account number'})
    
    user = User.query.filter_by(account_number=account_number).first()
    if user:
        return jsonify({'success': True, 'account_holder': user.username})
    else:
        return jsonify({'success': False, 'message': 'Account not found'})

@user_bp.route('/verify_transfer_otp', methods=['GET', 'POST'])
@require_login
def verify_transfer_otp():
    if 'pending_transfer' not in session:
        flash('No pending transfer found. Please start a new transfer.', 'error')
        return redirect(url_for('user.transfer'))
    
    if request.method == 'POST':
        otp_code = request.form.get('otp_code')
        transfer_data = session['pending_transfer']
        
        if not otp_code or len(otp_code) != 6:
            flash('Please enter a valid 6-digit OTP', 'error')
            return render_template('user/transfer_otp.html', **transfer_data, format_currency=format_currency)
        
        # Find the OTP
        otp = OTP.query.get(transfer_data['otp_id'])
        if not otp or otp.is_used or otp.is_expired():
            flash('Invalid or expired OTP. Please request a new one.', 'error')
            return render_template('user/transfer_otp.html', **transfer_data, format_currency=format_currency)
        
        if otp.otp_code != otp_code:
            flash('Incorrect OTP. Please try again.', 'error')
            return render_template('user/transfer_otp.html', **transfer_data, format_currency=format_currency)
        
        # Mark OTP as used
        otp.is_used = True
        
        # Get transaction and complete it
        transaction = Transaction.query.get(transfer_data['transaction_id'])
        if not transaction:
            flash('Transaction not found. Please contact support.', 'error')
            return redirect(url_for('user.dashboard'))
        
        # Get users
        sender = User.query.get(transaction.from_user_id)
        recipient = User.query.get(transaction.to_user_id)
        
        # Verify sender still has sufficient balance
        if sender.balance < transaction.amount:
            transaction.status = 'failed'
            transaction.description += ' (Insufficient funds at completion)'
            db.session.commit()
            flash('Transfer failed: Insufficient balance. Please try again.', 'error')
            session.pop('pending_transfer', None)
            return redirect(url_for('user.dashboard'))
        
        # Complete the transfer
        sender.balance -= transaction.amount
        recipient.balance += transaction.amount
        transaction.status = 'completed'
        
        db.session.commit()
        
        # Clear pending transfer from session
        session.pop('pending_transfer', None)
        
        flash(f'Transfer completed successfully! {format_currency(transaction.amount)} sent to {recipient.username}', 'success')
        return redirect(url_for('user.dashboard'))
    
    # GET request - show OTP verification form
    transfer_data = session['pending_transfer']
    transfer_data['user'] = User.query.get(session['user_id'])
    transfer_data['transfer_id'] = transfer_data['otp_id']  # For the form
    
    return render_template('user/transfer_otp.html', **transfer_data, format_currency=format_currency)

@user_bp.route('/resend_otp', methods=['POST'])
@require_login
def resend_otp():
    if 'pending_transfer' not in session:
        return jsonify({'success': False, 'message': 'No pending transfer found'})
    
    user = User.query.get(session['user_id'])
    transfer_data = session['pending_transfer']
    
    # Delete old OTP
    old_otp = OTP.query.get(transfer_data['otp_id'])
    if old_otp:
        db.session.delete(old_otp)
    
    # Generate new OTP
    otp_code = generate_otp()
    
    # Create new OTP
    otp = OTP()
    otp.user_id = user.id
    otp.otp_code = otp_code
    otp.purpose = 'transfer'
    otp.recipient_account = transfer_data['account_number']
    otp.amount = transfer_data['amount']
    otp.expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.session.add(otp)
    db.session.commit()
    
    # Update session with new OTP ID
    session['pending_transfer']['otp_id'] = otp.id
    
    # Log the new OTP (in real app, send via SMS)
    logging.info(f"Resent Transfer OTP for user {user.username}: {otp_code}")
    
    return jsonify({'success': True, 'message': 'OTP resent successfully'})
