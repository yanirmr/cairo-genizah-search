// Cairo Genizah Search - Main JavaScript

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.querySelector('.search-form');

    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const queryInput = document.querySelector('input[name="q"]');

            if (!queryInput.value.trim()) {
                e.preventDefault();
                alert('אנא הזן שאילתת חיפוש');
                queryInput.focus();
                return false;
            }
        });
    }

    // Auto-focus search input
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.focus();
    }

    // Line count validation
    const minLines = document.querySelector('#min_lines');
    const maxLines = document.querySelector('#max_lines');

    if (minLines && maxLines) {
        function validateLineCounts() {
            const min = parseInt(minLines.value) || 0;
            const max = parseInt(maxLines.value) || Infinity;

            if (min > 0 && max > 0 && min > max) {
                maxLines.setCustomValidity('מקסימום שורות חייב להיות גדול ממינימום שורות');
            } else {
                maxLines.setCustomValidity('');
            }
        }

        minLines.addEventListener('change', validateLineCounts);
        maxLines.addEventListener('change', validateLineCounts);
    }
});

// Smooth scroll to top
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Copy document ID to clipboard
function copyDocId(docId) {
    navigator.clipboard.writeText(docId).then(function() {
        alert('מזהה מסמך הועתק ללוח: ' + docId);
    }).catch(function(err) {
        console.error('Failed to copy: ', err);
    });
}
