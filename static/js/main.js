// Cairo Genizah Search - Main JavaScript

// Logging utility for frontend
const Logger = {
    log: function(level, message, data = {}) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp: timestamp,
            level: level,
            message: message,
            url: window.location.href,
            userAgent: navigator.userAgent,
            ...data
        };

        // Log to console
        const consoleMethod = level === 'error' ? 'error' : level === 'warn' ? 'warn' : 'log';
        console[consoleMethod](`[${timestamp}] ${level.toUpperCase()}: ${message}`, data);

        // Store logs in session storage for debugging (keep last 100 entries)
        try {
            const logs = JSON.parse(sessionStorage.getItem('genizah_logs') || '[]');
            logs.push(logEntry);
            if (logs.length > 100) logs.shift();
            sessionStorage.setItem('genizah_logs', JSON.stringify(logs));
        } catch (e) {
            console.error('Failed to store log:', e);
        }
    },

    info: function(message, data) {
        this.log('info', message, data);
    },

    warn: function(message, data) {
        this.log('warn', message, data);
    },

    error: function(message, data) {
        this.log('error', message, data);
    },

    debug: function(message, data) {
        this.log('debug', message, data);
    }
};

// Log page load
Logger.info('Page loaded', {
    page: window.location.pathname,
    referrer: document.referrer
});

// Global error handler
window.addEventListener('error', function(e) {
    Logger.error('Uncaught error', {
        message: e.message,
        filename: e.filename,
        lineno: e.lineno,
        colno: e.colno,
        error: e.error ? e.error.toString() : 'Unknown error'
    });
});

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(e) {
    Logger.error('Unhandled promise rejection', {
        reason: e.reason,
        promise: e.promise
    });
});

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    Logger.info('DOM content loaded, initializing application');

    const searchForm = document.querySelector('.search-form');

    if (searchForm) {
        Logger.debug('Search form found, attaching event listeners');

        searchForm.addEventListener('submit', function(e) {
            const queryInput = document.querySelector('input[name="q"]');
            const searchType = document.querySelector('select[name="type"]');
            const limit = document.querySelector('select[name="limit"]');

            Logger.info('Search form submitted', {
                query: queryInput.value,
                type: searchType ? searchType.value : 'unknown',
                limit: limit ? limit.value : 'unknown'
            });

            if (!queryInput.value.trim()) {
                e.preventDefault();
                Logger.warn('Form submission blocked - empty query');
                alert('אנא הזן שאילתת חיפוש');
                queryInput.focus();
                return false;
            }
        });
    } else {
        Logger.debug('Search form not found on this page');
    }

    // Auto-focus search input
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.focus();
        Logger.debug('Search input auto-focused');
    }

    // Line count validation
    const minLines = document.querySelector('#min_lines');
    const maxLines = document.querySelector('#max_lines');

    if (minLines && maxLines) {
        Logger.debug('Line count validation inputs found');

        function validateLineCounts() {
            const min = parseInt(minLines.value) || 0;
            const max = parseInt(maxLines.value) || Infinity;

            if (min > 0 && max > 0 && min > max) {
                Logger.warn('Line count validation failed', {
                    min: min,
                    max: max
                });
                maxLines.setCustomValidity('מקסימום שורות חייב להיות גדול ממינימום שורות');
            } else {
                maxLines.setCustomValidity('');
            }
        }

        minLines.addEventListener('change', function() {
            Logger.debug('Min lines changed', { value: minLines.value });
            validateLineCounts();
        });

        maxLines.addEventListener('change', function() {
            Logger.debug('Max lines changed', { value: maxLines.value });
            validateLineCounts();
        });
    }

    Logger.info('Application initialization completed');
});

// Smooth scroll to top
function scrollToTop() {
    Logger.debug('Scroll to top triggered');
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Copy document ID to clipboard
function copyDocId(docId) {
    Logger.info('Copy document ID to clipboard', { docId: docId });

    navigator.clipboard.writeText(docId).then(function() {
        Logger.info('Document ID copied successfully', { docId: docId });
        alert('מזהה מסמך הועתק ללוח: ' + docId);
    }).catch(function(err) {
        Logger.error('Failed to copy document ID', {
            docId: docId,
            error: err.toString()
        });
        console.error('Failed to copy: ', err);
        alert('שגיאה בהעתקת מזהה המסמך');
    });
}
