import random
import string
from datetime import datetime

def generate_account_number():
    """Generate a unique 10-digit account number"""
    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

def generate_referral_code():
    """Generate a unique 8-character referral code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def format_currency(amount):
    """Format amount as Nigerian Naira"""
    return f"₦{amount:,.2f}"

def is_suspicious_activity(user, amount, transaction_type):
    """Simple fraud detection - flag large transactions or frequent transactions"""
    if amount > 100000:  # Large transaction
        return True
    
    # Check for frequent transactions in the last hour
    from models import Transaction
    recent_transactions = Transaction.query.filter(
        (Transaction.from_user_id == user.id) | (Transaction.to_user_id == user.id),
        Transaction.created_at >= datetime.utcnow().replace(hour=datetime.utcnow().hour - 1)
    ).count()
    
    if recent_transactions > 10:  # More than 10 transactions in an hour
        return True
    
    return False

def validate_account_number(account_number):
    """Validate account number format"""
    if not account_number or len(account_number) != 10:
        return False
    return account_number.isdigit()
