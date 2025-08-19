/**
 * Twitter Campaign Manager - Main JavaScript File
 * Handles global functionality, UI interactions, and utilities
 */

// Global application object
const TwitterCampaignManager = {
    // Configuration
    config: {
        apiBaseUrl: '/api',
        chartColors: {
            primary: '#667eea',
            success: '#38ef7d',
            info: '#4facfe',
            warning: '#f093fb',
            danger: '#fc466b'
        },
        dateFormat: 'MMM DD, YYYY',
        timeFormat: 'HH:mm'
    },

    // Initialize the application
    init() {
        this.bindGlobalEvents();
        this.initializeTooltips();
        this.initializeAlerts();
        this.checkNotifications();
        this.initializeDateInputs();
        console.log('Twitter Campaign Manager initialized');
    },

    // Bind global event listeners
    bindGlobalEvents() {
        // Auto-hide alerts after 5 seconds
        setTimeout(() => {
            const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
            alerts.forEach(alert => {
                if (alert && bootstrap.Alert.getOrCreateInstance) {
                    const alertInstance = bootstrap.Alert.getOrCreateInstance(alert);
                    alertInstance.close();
                }
            });
        }, 5000);

        // Global form validation
        document.addEventListener('submit', this.handleFormSubmit.bind(this));

        // Handle dynamic character counting
        document.addEventListener('input', this.handleTextareaInput.bind(this));

        // Handle modal cleanup
        document.addEventListener('hidden.bs.modal', this.handleModalHidden.bind(this));

        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
    },

    // Initialize Bootstrap tooltips
    initializeTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },

    // Initialize alert auto-dismissal
    initializeAlerts() {
        const alerts = document.querySelectorAll('.alert[data-auto-dismiss]');
        alerts.forEach(alert => {
            const timeout = parseInt(alert.dataset.autoDismiss) || 5000;
            setTimeout(() => {
                if (alert.parentElement) {
                    const alertInstance = bootstrap.Alert.getOrCreateInstance(alert);
                    alertInstance.close();
                }
            }, timeout);
        });
    },

    // Check for notifications (placeholder for future implementation)
    checkNotifications() {
        // This would typically fetch from an API
        console.log('Checking for notifications...');
    },

    // Initialize date inputs with minimum dates
    initializeDateInputs() {
        const dateInputs = document.querySelectorAll('input[type="datetime-local"], input[type="date"]');
        const now = new Date();
        const currentDateTime = now.toISOString().slice(0, 16);
        const currentDate = now.toISOString().slice(0, 10);

        dateInputs.forEach(input => {
            if (input.type === 'datetime-local') {
                input.min = currentDateTime;
            } else if (input.type === 'date') {
                input.min = currentDate;
            }
        });
    },

    // Handle form submissions with validation
    handleFormSubmit(event) {
        const form = event.target;
        
        // Check for required fields
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');
                this.showToast('Please fill in all required fields', 'error');
            } else {
                field.classList.remove('is-invalid');
            }
        });

        // Check password confirmation if present
        const password = form.querySelector('input[name="password"]');
        const confirmPassword = form.querySelector('input[name="confirm_password"]');
        
        if (password && confirmPassword && password.value !== confirmPassword.value) {
            isValid = false;
            confirmPassword.classList.add('is-invalid');
            this.showToast('Passwords do not match', 'error');
        }

        if (!isValid) {
            event.preventDefault();
        }
    },

    // Handle textarea input for character counting
    handleTextareaInput(event) {
        const textarea = event.target;
        
        if (textarea.tagName === 'TEXTAREA' && textarea.hasAttribute('maxlength')) {
            const maxLength = parseInt(textarea.getAttribute('maxlength'));
            const currentLength = textarea.value.length;
            
            // Find or create character counter
            let counter = textarea.parentNode.querySelector('.char-counter');
            if (!counter) {
                counter = document.createElement('div');
                counter.className = 'char-counter form-text text-end';
                textarea.parentNode.appendChild(counter);
            }
            
            counter.textContent = `${currentLength}/${maxLength}`;
            
            // Add warning styling if approaching limit
            if (currentLength > maxLength * 0.9) {
                counter.classList.add('text-warning');
            } else {
                counter.classList.remove('text-warning');
            }
            
            // Add error styling if over limit
            if (currentLength > maxLength) {
                counter.classList.add('text-danger');
                textarea.classList.add('is-invalid');
            } else {
                counter.classList.remove('text-danger');
                textarea.classList.remove('is-invalid');
            }
        }
    },

    // Handle modal cleanup
    handleModalHidden(event) {
        const modal = event.target;
        
        // Clear form data in modals
        const forms = modal.querySelectorAll('form');
        forms.forEach(form => form.reset());
        
        // Remove validation classes
        const inputs = modal.querySelectorAll('.is-invalid, .is-valid');
        inputs.forEach(input => {
            input.classList.remove('is-invalid', 'is-valid');
        });
    },

    // Handle keyboard shortcuts
    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + Enter to submit forms
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            const activeElement = document.activeElement;
            const form = activeElement.closest('form');
            
            if (form) {
                const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
                if (submitButton) {
                    submitButton.click();
                }
            }
        }
        
        // Escape to close modals
        if (event.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modalInstance = bootstrap.Modal.getInstance(openModal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
        }
    },

    // Show toast notification
    showToast(message, type = 'info', duration = 3000) {
        // Remove existing toasts
        const existingToasts = document.querySelectorAll('.toast-notification');
        existingToasts.forEach(toast => toast.remove());

        // Create toast container if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-notification align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${this.getIconForType(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toast);

        // Initialize and show toast
        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();

        // Clean up after toast is hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    // Get icon for toast type
    getIconForType(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    },

    // Utility function to format dates
    formatDate(date, format = this.config.dateFormat) {
        if (typeof date === 'string') {
            date = new Date(date);
        }
        
        const options = {
            year: 'numeric',
            month: 'short',
            day: '2-digit'
        };
        
        return date.toLocaleDateString('en-US', options);
    },

    // Utility function to format numbers
    formatNumber(number) {
        if (number >= 1000000) {
            return (number / 1000000).toFixed(1) + 'M';
        } else if (number >= 1000) {
            return (number / 1000).toFixed(1) + 'K';
        }
        return number.toString();
    },

    // Utility function to debounce function calls
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // AJAX utility function
    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(this.config.apiBaseUrl + endpoint, config);
            
            if (!response.ok) {
                throw new Error(`API call failed: ${response.status} ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call error:', error);
            this.showToast('An error occurred while communicating with the server', 'error');
            throw error;
        }
    },

    // Loading spinner utility
    showLoading(element, text = 'Loading...') {
        const loadingHtml = `
            <div class="loading-overlay">
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">${text}</span>
                    </div>
                    <div class="mt-2">${text}</div>
                </div>
            </div>
        `;
        
        element.style.position = 'relative';
        element.insertAdjacentHTML('beforeend', loadingHtml);
    },

    hideLoading(element) {
        const loadingOverlay = element.querySelector('.loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
    },

    // Copy to clipboard utility
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copied to clipboard!', 'success');
        } catch (error) {
            console.error('Failed to copy to clipboard:', error);
            this.showToast('Failed to copy to clipboard', 'error');
        }
    },

    // Confirm dialog utility
    confirm(message, title = 'Confirm Action') {
        return new Promise((resolve) => {
            // Create modal HTML
            const modalHtml = `
                <div class="modal fade" id="confirmModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">${title}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <p>${message}</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                <button type="button" class="btn btn-primary" id="confirmBtn">Confirm</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Remove existing confirm modal
            const existingModal = document.getElementById('confirmModal');
            if (existingModal) {
                existingModal.remove();
            }

            // Add modal to page
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            const modal = document.getElementById('confirmModal');
            const confirmBtn = document.getElementById('confirmBtn');

            // Show modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();

            // Handle confirm button
            confirmBtn.addEventListener('click', () => {
                bsModal.hide();
                resolve(true);
            });

            // Handle modal close
            modal.addEventListener('hidden.bs.modal', () => {
                modal.remove();
                resolve(false);
            });
        });
    }
};

// Campaign-specific functions
const CampaignManager = {
    // Generate AI content for campaign
    async generateContent(campaignId) {
        try {
            TwitterCampaignManager.showLoading(document.body, 'Generating AI content...');
            
            const response = await TwitterCampaignManager.apiCall(`/campaigns/${campaignId}/generate_content`, {
                method: 'POST'
            });

            if (response.success) {
                TwitterCampaignManager.showToast('Content generated successfully!', 'success');
                return response.content;
            } else {
                throw new Error(response.error || 'Failed to generate content');
            }
        } catch (error) {
            TwitterCampaignManager.showToast('Failed to generate content', 'error');
            throw error;
        } finally {
            TwitterCampaignManager.hideLoading(document.body);
        }
    },

    // Schedule multiple tweets for campaign
    async scheduleCampaignTweets(campaignId, startDate, endDate, tweetsPerDay) {
        try {
            const response = await TwitterCampaignManager.apiCall(`/campaigns/${campaignId}/schedule`, {
                method: 'POST',
                body: JSON.stringify({
                    start_date: startDate,
                    end_date: endDate,
                    tweets_per_day: tweetsPerDay
                })
            });

            if (response.success) {
                TwitterCampaignManager.showToast(`Scheduled ${response.count} tweets successfully!`, 'success');
                return response;
            } else {
                throw new Error(response.error || 'Failed to schedule tweets');
            }
        } catch (error) {
            TwitterCampaignManager.showToast('Failed to schedule tweets', 'error');
            throw error;
        }
    }
};

// Analytics-specific functions
const AnalyticsManager = {
    // Chart instances
    charts: {},

    // Initialize analytics charts
    initCharts() {
        this.initEngagementChart();
        this.initPieChart();
    },

    // Initialize engagement chart
    initEngagementChart() {
        const ctx = document.getElementById('engagementChart');
        if (!ctx) return;

        this.charts.engagement = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    },

    // Initialize pie chart
    initPieChart() {
        const ctx = document.getElementById('engagementPieChart');
        if (!ctx) return;

        this.charts.pie = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Likes', 'Retweets', 'Replies'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        TwitterCampaignManager.config.chartColors.danger,
                        TwitterCampaignManager.config.chartColors.info,
                        TwitterCampaignManager.config.chartColors.success
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    },

    // Update chart data
    updateChart(chartName, data) {
        const chart = this.charts[chartName];
        if (!chart) return;

        chart.data = data;
        chart.update();
    }
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    TwitterCampaignManager.init();
    
    // Initialize analytics if on analytics page
    if (document.getElementById('engagementChart')) {
        AnalyticsManager.initCharts();
    }
});

// Export for global access
window.TwitterCampaignManager = TwitterCampaignManager;
window.CampaignManager = CampaignManager;
window.AnalyticsManager = AnalyticsManager;
