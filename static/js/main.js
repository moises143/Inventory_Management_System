// Main JavaScript file for Inventory Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Auto-dismiss alerts
    autoDismissAlerts();
    
    // Form validation
    initializeFormValidation();
    
    // Search functionality
    initializeSearch();
    
    // Loading states
    initializeLoadingStates();
    
    console.log('Inventory Management System initialized');
});

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
function autoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        if (!alert.classList.contains('alert-danger')) {
            setTimeout(function() {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Real-time validation for specific fields
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            if (this.value < 0) {
                this.setCustomValidity('Value must be greater than or equal to 0');
            } else {
                this.setCustomValidity('');
            }
        });
    });
    
    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (this.value && !emailRegex.test(this.value)) {
                this.setCustomValidity('Please enter a valid email address');
            } else {
                this.setCustomValidity('');
            }
        });
    });
}

/**
 * Initialize search functionality with debouncing
 */
function initializeSearch() {
    const searchInputs = document.querySelectorAll('input[name="search"]');
    
    searchInputs.forEach(function(input) {
        let timeout;
        
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            const form = this.closest('form');
            
            timeout = setTimeout(function() {
                if (input.value.length === 0 || input.value.length >= 2) {
                    form.submit();
                }
            }, 500);
        });
        
        // Clear search functionality
        const clearButton = document.createElement('button');
        clearButton.type = 'button';
        clearButton.className = 'btn btn-outline-secondary btn-sm ms-2';
        clearButton.innerHTML = '<i class="fas fa-times"></i>';
        clearButton.title = 'Clear search';
        
        clearButton.addEventListener('click', function() {
            input.value = '';
            input.closest('form').submit();
        });
        
        if (input.value) {
            input.parentNode.appendChild(clearButton);
        }
    });
}

/**
 * Initialize loading states for forms
 */
function initializeLoadingStates() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
                submitButton.disabled = true;
                
                // Re-enable after 5 seconds as fallback
                setTimeout(function() {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }, 5000);
            }
        });
    });
}

/**
 * Utility function to format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

/**
 * Utility function to format dates
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

/**
 * Show confirmation dialog
 */
function showConfirmation(message, callback) {
    if (confirm(message)) {
        callback();
    }
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
 * Calculate reorder suggestion
 */
function calculateReorderSuggestion(currentStock, reorderPoint, averageUsage) {
    if (currentStock <= reorderPoint) {
        const shortage = reorderPoint - currentStock;
        const buffer = Math.ceil(averageUsage * 7); // 7 days buffer
        return shortage + buffer;
    }
    return 0;
}

/**
 * Validate stock levels and show warnings
 */
function validateStockLevels() {
    const quantityInputs = document.querySelectorAll('input[name="quantity"]');
    const reorderInputs = document.querySelectorAll('input[name="reorder_point"]');
    
    quantityInputs.forEach(function(qtyInput, index) {
        const reorderInput = reorderInputs[index];
        
        if (qtyInput && reorderInput) {
            const checkLevels = function() {
                const quantity = parseInt(qtyInput.value) || 0;
                const reorderPoint = parseInt(reorderInput.value) || 0;
                
                if (quantity <= reorderPoint && quantity > 0) {
                    qtyInput.classList.add('border-warning');
                    qtyInput.title = 'Stock level is at or below reorder point';
                } else {
                    qtyInput.classList.remove('border-warning');
                    qtyInput.title = '';
                }
            };
            
            qtyInput.addEventListener('input', checkLevels);
            reorderInput.addEventListener('input', checkLevels);
            
            // Check on page load
            checkLevels();
        }
    });
}

/**
 * Initialize stock level validation
 */
document.addEventListener('DOMContentLoaded', function() {
    validateStockLevels();
});

/**
 * Handle keyboard shortcuts
 */
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + K for search focus
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // ESC to close modals
    if (event.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(function(modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }
});

/**
 * Auto-save functionality for forms (optional)
 */
function initializeAutoSave() {
    const forms = document.querySelectorAll('form[data-autosave]');
    
    forms.forEach(function(form) {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(function(input) {
            input.addEventListener('change', function() {
                const formData = new FormData(form);
                const data = Object.fromEntries(formData);
                
                // Save to localStorage with form ID as key
                localStorage.setItem(`autosave_${form.id}`, JSON.stringify(data));
                
                // Show save indicator
                showToast('Draft saved', 'success');
            });
        });
        
        // Load saved data on page load
        const savedData = localStorage.getItem(`autosave_${form.id}`);
        if (savedData) {
            const data = JSON.parse(savedData);
            Object.keys(data).forEach(function(key) {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    input.value = data[key];
                }
            });
        }
    });
}

/**
 * Export functionality for tables
 */
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const csvContent = [];
    
    rows.forEach(function(row) {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        
        cols.forEach(function(col) {
            // Clean text content and handle commas
            let text = col.textContent.trim().replace(/"/g, '""');
            if (text.includes(',')) {
                text = `"${text}"`;
            }
            rowData.push(text);
        });
        
        csvContent.push(rowData.join(','));
    });
    
    const csvString = csvContent.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'export.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Expose functions globally for use in templates
window.exportTableToCSV = exportTableToCSV;
window.showToast = showToast;
window.showConfirmation = showConfirmation;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
