/**
 * Freelance Manager - JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm || 'Êtes-vous sûr ?')) {
                e.preventDefault();
            }
        });
    });

    // Format currency inputs
    const currencyInputs = document.querySelectorAll('input[data-currency]');
    currencyInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                this.value = value.toFixed(2);
            }
        });
    });

    // Auto-calculate totals
    function setupAutoCalculate() {
        const tjmInput = document.getElementById('tjm');
        const joursInput = document.getElementById('jours') || document.getElementById('jours_effectifs');
        const totalDisplay = document.getElementById('total-display');

        if (tjmInput && joursInput && totalDisplay) {
            function updateTotal() {
                const tjm = parseFloat(tjmInput.value) || 0;
                const jours = parseFloat(joursInput.value) || 0;
                const total = tjm * jours;
                totalDisplay.textContent = total.toLocaleString('fr-FR') + ' €';
            }

            tjmInput.addEventListener('input', updateTotal);
            joursInput.addEventListener('input', updateTotal);
            updateTotal();
        }
    }
    setupAutoCalculate();

    // Tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(function(tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Date inputs - set default to today
    const dateInputs = document.querySelectorAll('input[type="date"]:not([value])');
    const today = new Date().toISOString().split('T')[0];
    // Don't set default for optional date fields

    // Form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+S to submit form
        if (e.ctrlKey && e.key === 's') {
            const form = document.querySelector('form');
            if (form) {
                e.preventDefault();
                form.submit();
            }
        }

        // Escape to go back
        if (e.key === 'Escape') {
            const backButton = document.querySelector('a[href*="list"], .btn-outline-secondary');
            if (backButton && backButton.href) {
                // Don't navigate automatically, just focus the button
                backButton.focus();
            }
        }
    });

    // Loading state for forms
    const submitButtons = document.querySelectorAll('form button[type="submit"]');
    submitButtons.forEach(function(button) {
        button.closest('form').addEventListener('submit', function() {
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Chargement...';
        });
    });

    // Number formatting for display
    function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    }

    // Search/filter functionality for tables
    const searchInput = document.getElementById('search-table');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');

            rows.forEach(function(row) {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        });
    }

    console.log('Freelance Manager loaded');
});

// Utility functions
const FreelanceManager = {
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR'
        }).format(amount);
    },

    formatDate: function(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('fr-FR');
    },

    showNotification: function(message, type = 'info') {
        const container = document.querySelector('.container-fluid');
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        container.insertBefore(alert, container.firstChild);

        setTimeout(function() {
            alert.remove();
        }, 5000);
    }
};
