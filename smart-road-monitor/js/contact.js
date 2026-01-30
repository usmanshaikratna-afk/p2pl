// contact.js - Contact page specific functionality

document.addEventListener('DOMContentLoaded', function() {
    const feedbackForm = document.getElementById('feedbackForm');
    const feedbackSuccess = document.getElementById('feedbackSuccess');
    const sendAnotherBtn = document.getElementById('sendAnother');
    const ratingStars = document.querySelectorAll('.rating-star');
    const feedbackRating = document.getElementById('feedbackRating');
    
    // Set up rating stars
    ratingStars.forEach(star => {
        star.addEventListener('click', setRating);
        star.addEventListener('mouseover', hoverRating);
        star.addEventListener('mouseout', resetRating);
    });
    
    // Handle feedback submission
    if (feedbackForm) {
        feedbackForm.addEventListener('submit', handleFeedbackSubmit);
    }
    
    if (sendAnotherBtn) {
        sendAnotherBtn.addEventListener('click', resetFeedbackForm);
    }
    
    // Set rating
    function setRating(e) {
        const rating = parseInt(e.target.getAttribute('data-rating'));
        feedbackRating.value = rating;
        
        ratingStars.forEach(star => {
            const starRating = parseInt(star.getAttribute('data-rating'));
            if (starRating <= rating) {
                star.style.color = '#ffc107';
            } else {
                star.style.color = '#ddd';
            }
        });
    }
    
    // Hover effect for stars
    function hoverRating(e) {
        const rating = parseInt(e.target.getAttribute('data-rating'));
        
        ratingStars.forEach(star => {
            const starRating = parseInt(star.getAttribute('data-rating'));
            if (starRating <= rating) {
                star.style.color = '#ffc107';
            }
        });
    }
    
    // Reset stars to current rating
    function resetRating() {
        const currentRating = parseInt(feedbackRating.value);
        
        ratingStars.forEach(star => {
            const starRating = parseInt(star.getAttribute('data-rating'));
            if (starRating > currentRating) {
                star.style.color = '#ddd';
            }
        });
    }
    
    // Reset rating stars
    function resetRatingStars() {
        feedbackRating.value = 0;
        ratingStars.forEach(star => {
            star.style.color = '#ddd';
        });
    }
    
    // Handle feedback submission
    function handleFeedbackSubmit(e) {
        e.preventDefault();
        
        // Get form data
        const formData = {
            name: document.getElementById('feedbackName').value,
            email: document.getElementById('feedbackEmail').value,
            category: document.getElementById('feedbackCategory').value,
            rating: feedbackRating.value,
            message: document.getElementById('feedbackMessage').value,
            subscribe: document.getElementById('subscribeNews').checked,
            timestamp: new Date().toISOString()
        };
        
        // Validate form
        if (!formData.name || !formData.email || !formData.message) {
            alert('Please fill in all required fields.');
            return;
        }
        
        if (formData.rating === '0') {
            if (!confirm('You haven\'t provided a rating. Submit without rating?')) {
                return;
            }
        }
        
        // Show loading state
        const submitBtn = feedbackForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        submitBtn.disabled = true;
        
        // Simulate API call
        setTimeout(() => {
            // Show success message
            feedbackForm.style.display = 'none';
            feedbackSuccess.style.display = 'block';
            
            // Reset button
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
            
            // Store feedback in localStorage
            storeFeedbackInLocalStorage(formData);
            
            console.log('Feedback submitted:', formData);
        }, 1500);
    }
    
    // Store feedback in localStorage
    function storeFeedbackInLocalStorage(feedback) {
        let feedbacks = JSON.parse(localStorage.getItem('userFeedbacks') || '[]');
        feedbacks.push(feedback);
        localStorage.setItem('userFeedbacks', JSON.stringify(feedbackList));
    }
    
    // Reset feedback form
    function resetFeedbackForm() {
        feedbackForm.reset();
        feedbackForm.style.display = 'block';
        feedbackSuccess.style.display = 'none';
        resetRatingStars();
        document.getElementById('subscribeNews').checked = true;
    }
    
    // Initialize with sample data for testing
    function initializeSampleData() {
        // Only for demonstration purposes
        if (window.location.search.includes('demo=true')) {
            document.getElementById('feedbackName').value = "John Doe";
            document.getElementById('feedbackEmail').value = "john@example.com";
            document.getElementById('feedbackCategory').value = "improvement";
            document.getElementById('feedbackMessage').value = "The system is very useful! I'd love to see more detailed reporting options for specific types of road damage.";
            setRating({ target: document.querySelector('.rating-star[data-rating="5"]') });
        }
    }
    
    // Initialize sample data if needed
    initializeSampleData();
});