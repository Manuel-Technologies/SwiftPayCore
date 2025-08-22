# SwiftPay - Digital Payment Platform

## Overview

SwiftPay is a Flask-based digital payment platform that enables users to send money, manage wallet balances, and earn referral bonuses. The application features both user and admin interfaces, with comprehensive transaction management, user authentication, and fraud detection capabilities. The platform supports transfers between users, fund deposits, withdrawals to bank accounts, and a referral program that rewards users for bringing new customers.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask** - Primary web framework with Blueprint-based modular architecture
- **SQLAlchemy** - ORM for database operations with declarative base model
- **JWT Extended** - Token-based authentication for API security
- **Bcrypt** - Password hashing and verification

### Authentication System
- **Dual Authentication** - Separate login systems for users and administrators
- **Session Management** - Flask sessions for user state management
- **JWT Tokens** - JSON Web Tokens for API authentication (configured to not expire)
- **Role-based Access** - Decorator-based access control for admin and user routes

### Database Design
- **User Model** - Stores user credentials, account numbers, balances, referral codes, and suspension status
- **Transaction Model** - Tracks all financial operations (transfers, deposits, withdrawals, referral bonuses)
- **Referral Model** - Manages referral relationships and bonus tracking
- **Admin Model** - Separate admin user management

### Frontend Architecture
- **Jinja2 Templates** - Server-side template rendering with inheritance
- **Bootstrap 5** - CSS framework for responsive design
- **Font Awesome** - Icon library for UI elements
- **Chart.js** - Data visualization for admin analytics
- **Custom CSS** - Enhanced styling with CSS custom properties

### Security Features
- **Password Security** - Bcrypt hashing for all passwords
- **Fraud Detection** - Utility functions to detect suspicious activity patterns
- **Input Validation** - Account number format validation and amount limits
- **Session Security** - Secure session management with configurable secret keys

### Transaction Processing
- **Multi-type Support** - Handles transfers, deposits, withdrawals, and referral bonuses
- **Status Tracking** - Pending, completed, and failed transaction states
- **Balance Management** - Automatic balance updates with transaction completion
- **Referral System** - Automated bonus distribution for successful referrals

### Admin Dashboard
- **User Management** - View, search, and suspend user accounts
- **Transaction Monitoring** - Comprehensive transaction history and filtering
- **Analytics** - Charts and metrics for platform performance
- **Fraud Detection** - Flagged transactions and suspicious activity monitoring

### Data Utilities
- **Account Generation** - Automatic 10-digit account number creation
- **Referral Codes** - 8-character alphanumeric referral code generation
- **Currency Formatting** - Nigerian Naira formatting utilities
- **Activity Detection** - Large transaction and frequency-based fraud detection

## External Dependencies

### Core Framework Dependencies
- **Flask** - Web application framework
- **Flask-SQLAlchemy** - Database ORM integration
- **Flask-JWT-Extended** - JWT authentication management
- **Flask-Bcrypt** - Password hashing utilities
- **Werkzeug** - WSGI utilities and security helpers

### Frontend Libraries
- **Bootstrap 5** - CSS framework via CDN
- **Font Awesome 6** - Icon library via CDN
- **Chart.js** - Data visualization library via CDN

### Database
- **SQLite** - Default database for development (configurable via DATABASE_URL)
- **ProxyFix** - WSGI middleware for deployment behind reverse proxies

### Environment Configuration
- **SESSION_SECRET** - Flask session encryption key
- **JWT_SECRET_KEY** - JWT token signing key
- **DATABASE_URL** - Database connection string

### Potential External Integrations
- **Payment Gateways** - Ready for integration with Nigerian payment processors
- **SMS/Email Services** - Infrastructure prepared for notification services
- **Bank APIs** - Withdrawal functionality designed for bank integration
- **Monitoring Services** - Logging infrastructure in place for external monitoring