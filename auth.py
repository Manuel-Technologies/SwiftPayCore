from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db, bcrypt
from models import User, Admin, Transaction
from utils import generate_account_number, generate_referral_code
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please provide both email and password', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            if user.is_suspended:
                flash('Your account has been suspended. Please contact support.', 'error')
                return render_template('auth/login.html')
            
            access_token = create_access_token(identity=user.id)
            session['access_token'] = access_token
            session['user_id'] = user.id
            
            # Update last login
            user.last_login = db.func.now()
            db.session.commit()
            
            flash('Login successful!', 'success')
            return redirect(url_for('user.dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        referral_code = request.form.get('referral_code')
        
        # Validation
        if not username or not email or not password:
            flash('Please fill in all required fields', 'error')
            return render_template('auth/signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('auth/signup.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/signup.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return render_template('auth/signup.html')
        
        # Generate unique account number and referral code
        account_number = generate_account_number()
        while User.query.filter_by(account_number=account_number).first():
            account_number = generate_account_number()
        
        user_referral_code = generate_referral_code()
        while User.query.filter_by(referral_code=user_referral_code).first():
            user_referral_code = generate_referral_code()
        
        # Create user
        user = User()
        user.username = username
        user.email = email
        user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user.account_number = account_number
        user.referral_code = user_referral_code
        user.referred_by = referral_code if referral_code else None
        
        db.session.add(user)
        db.session.commit()
        
        # Process referral bonus
        if referral_code:
            referrer = User.query.filter_by(referral_code=referral_code).first()
            if referrer:
                # Add referral bonus to referrer
                referrer.balance += 1000
                
                # Create referral record
                from models import Referral
                referral = Referral()
                referral.referrer_id = referrer.id
                referral.referred_user_id = user.id
                referral.bonus_amount = 1000
                referral.is_paid = True
                db.session.add(referral)
                
                # Create transaction record
                transaction = Transaction()
                transaction.to_user_id = referrer.id
                transaction.amount = 1000
                transaction.transaction_type = 'referral_bonus'
                transaction.status = 'completed'
                transaction.description = f'Referral bonus for inviting {username}'
                db.session.add(transaction)
                db.session.commit()
                
                logging.info(f"Referral bonus of ₦1000 credited to {referrer.username}")
        
        flash('Account created successfully! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/signup.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('auth.login'))
