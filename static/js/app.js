/**
 * SwiftPay - Main JavaScript Application
 * Handles client-side interactions and UI enhancements
 */

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Main app initialization
 */
function initializeApp() {
    initializeTooltips();
    initializeAlerts();
    initializeFormValidation();
    initializeCopyFunctionality();
    initializeNumberFormatting();
    initializeConfirmations();
    initializeNavigation();
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Auto-dismiss alerts after 5 seconds
 */
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * Form validation enhancements
 */
function initializeFormValidation() {
    // Account number validation
    const accountNumberInputs = document.querySelectorAll('input[name="account_number"]');
    accountNumberInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            validateAccountNumber(this);
        });
    });

    // Amount validation
    const amountInputs = document.querySelectorAll('input[name="amount"]');
    amountInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            validateAmount(this);
        });
    });

    // Real-time form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

/**
 * Validate account number format
 */
function validateAccountNumber(input) {
    const value = input.value.replace(/\D/g, ''); // Remove non-digits
    input.value = value.slice(0, 10); // Limit to 10 digits
    
    const feedback = input.parentNode.querySelector('.invalid-feedback') || 
                    input.parentNode.parentNode.querySelector('.invalid-feedback');
    
    if (value.length === 10) {
        input.setCustomValidity('');
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        if (feedback) feedback.style.display = 'none';
    } else {
        input.setCustomValidity('Account number must be exactly 10 digits');
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
        if (feedback) {
            feedback.textContent = 'Account number must be exactly 10 digits';
            feedback.style.display = 'block';
        }
    }
}

/**
 * Validate amount input
 */
function validateAmount(input) {
    const value = parseFloat(input.value);
    const min = parseFloat(input.getAttribute('min')) || 0;
    const max = parseFloat(input.getAttribute('max')) || Infinity;
    
    if (isNaN(value) || value < min) {
        input.setCustomValidity(`Amount must be at least ₦${min.toLocaleString()}`);
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
    } else if (value > max) {
        input.setCustomValidity(`Amount cannot exceed ₦${max.toLocaleString()}`);
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
    } else {
        input.setCustomValidity('');
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
    }
}

/**
 * Initialize copy to clipboard functionality
 */
function initializeCopyFunctionality() {
    // Add event listeners for all copy buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-copy]')) {
            const button = e.target.closest('[data-copy]');
            const targetId = button.getAttribute('data-copy');
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                copyToClipboard(targetElement.value || targetElement.textContent, button);
            }
        }
    });
}

/**
 * Copy text to clipboard with visual feedback
 */
function copyToClipboard(text, button) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function() {
            showCopySuccess(button);
        }).catch(function(err) {
            console.error('Failed to copy: ', err);
            fallbackCopyToClipboard(text, button);
        });
    } else {
        fallbackCopyToClipboard(text, button);
    }
}

/**
 * Fallback copy method for older browsers
 */
function fallbackCopyToClipboard(text, button) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showCopySuccess(button);
    } catch (err) {
        console.error('Fallback copy failed: ', err);
        showCopyError(button);
    }
    
    document.body.removeChild(textArea);
}

/**
 * Show copy success feedback
 */
function showCopySuccess(button) {
    const originalContent = button.innerHTML;
    const originalClasses = button.className;
    
    // Update button appearance
    button.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
    button.className = button.className.replace(/btn-\w+/g, 'btn-success');
    button.classList.add('copy-success');
    
    // Reset after 2 seconds
    setTimeout(function() {
        button.innerHTML = originalContent;
        button.className = originalClasses;
        button.classList.remove('copy-success');
    }, 2000);
}

/**
 * Show copy error feedback
 */
function showCopyError(button) {
    const originalContent = button.innerHTML;
    const originalClasses = button.className;
    
    button.innerHTML = '<i class="fas fa-times me-1"></i>Failed';
    button.className = button.className.replace(/btn-\w+/g, 'btn-danger');
    
    setTimeout(function() {
        button.innerHTML = originalContent;
        button.className = originalClasses;
    }, 2000);
}

/**
 * Format numbers with Nigerian Naira currency
 */
function initializeNumberFormatting() {
    const currencyInputs = document.querySelectorAll('.currency-input');
    currencyInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            formatCurrencyInput(this);
        });
    });
}

/**
 * Format currency input display
 */
function formatCurrencyInput(input) {
    const value = parseFloat(input.value);
    if (!isNaN(value)) {
        input.value = value.toFixed(2);
    }
}

/**
 * Initialize confirmation dialogs
 */
function initializeConfirmations() {
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Are you sure?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

/**
 * Navigation enhancements
 */
function initializeNavigation() {
    // Add active state to current page
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(function(link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
    
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Show loading state on buttons
 */
function showButtonLoading(button) {
    button.classList.add('loading');
    button.disabled = true;
}

/**
 * Hide loading state on buttons
 */
function hideButtonLoading(button) {
    button.classList.remove('loading');
    button.disabled = false;
}

/**
 * Form submission with loading state
 */
function submitFormWithLoading(form, submitButton) {
    showButtonLoading(submitButton);
    
    // Simulate form processing (remove in production)
    setTimeout(function() {
        form.submit();
    }, 500);
}

/**
 * Format number as Nigerian Naira
 */
function formatNaira(amount) {
    return new Intl.NumberFormat('en-NG', {
        style: 'currency',
        currency: 'NGN',
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * Validate Nigerian phone number format
 */
function validateNigerianPhone(phoneNumber) {
    const phoneRegex = /^(\+234|234|0)(70|71|80|81|90|91|70)[0-9]{8}$/;
    return phoneRegex.test(phoneNumber.replace(/\s+/g, ''));
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

/**
 * Debounce function for search inputs
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Initialize search functionality with debouncing
 */
function initializeSearch() {
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(function(input) {
        const debouncedSearch = debounce(function(value) {
            performSearch(value, input);
        }, 300);
        
        input.addEventListener('input', function() {
            debouncedSearch(this.value);
        });
    });
}

/**
 * Perform search operation
 */
function performSearch(query, input) {
    const form = input.closest('form');
    if (form && query.length >= 2) {
        // Auto-submit search form for queries with 2+ characters
        form.submit();
    }
}

/**
 * Initialize modal enhancements
 */
function initializeModals() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(function(modal) {
        modal.addEventListener('show.bs.modal', function() {
            // Focus first input when modal opens
            const firstInput = this.querySelector('input:not([type="hidden"]):not([disabled])');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 150);
            }
        });
        
        modal.addEventListener('hidden.bs.modal', function() {
            // Reset form when modal closes
            const form = this.querySelector('form');
            if (form) {
                form.reset();
                form.classList.remove('was-validated');
            }
        });
    });
}

/**
 * Utility functions for common operations
 */
const SwiftPayUtils = {
    /**
     * Format account number with spaces for readability
     */
    formatAccountNumber: function(accountNumber) {
        return accountNumber.replace(/(\d{4})(\d{3})(\d{3})/, '$1 $2 $3');
    },
    
    /**
     * Validate email format
     */
    isValidEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    /**
     * Generate random referral code
     */
    generateReferralCode: function(length = 8) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    },
    
    /**
     * Calculate transaction fee
     */
    calculateFee: function(amount, type = 'transfer') {
        if (type === 'transfer' && amount > 50000) {
            return amount * 0.001; // 0.1% fee for large transfers
        } else if (type === 'withdrawal' && amount < 10000) {
            return 50; // Fixed fee for small withdrawals
        }
        return 0;
    }
};

// Initialize additional features when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
    initializeModals();
});

// Global functions for use in templates
window.copyReferralCode = function() {
    const referralCode = document.getElementById('referralCode');
    if (referralCode) {
        copyToClipboard(referralCode.value, referralCode.nextElementSibling);
    }
};

window.copyReferralLink = function() {
    const referralLink = document.getElementById('referralLink');
    if (referralLink) {
        copyToClipboard(referralLink.value, referralLink.nextElementSibling);
    }
};

window.setAmount = function(amount) {
    const amountInput = document.getElementById('amount');
    if (amountInput) {
        amountInput.value = amount;
        amountInput.focus();
        validateAmount(amountInput);
    }
};

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        SwiftPayUtils,
        formatNaira,
        validateNigerianPhone,
        showToast
    };
}
