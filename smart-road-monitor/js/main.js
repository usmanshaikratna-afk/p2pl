// main.js - Shared functionality across all pages

// DOM Elements
const themeToggle = document.getElementById('themeToggle');
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const nav = document.querySelector('nav');
const currentPage = document.body.getAttribute('data-page');

// Initialize the application
function initApp() {
    // Set active navigation link
    setActiveNavLink();
    
    // Set up event listeners
    if (themeToggle) themeToggle.addEventListener('click', toggleDarkMode);
    if (mobileMenuBtn) mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    
    // Animate statistics on home page
    if (currentPage === 'home') {
        animateStatistics();
    }
    
    // Check for saved theme preference
    if (localStorage.getItem('darkMode') === 'enabled') {
        enableDarkMode();
    }
}

// Set active navigation link based on current page
function setActiveNavLink() {
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === `${currentPage}.html` || 
            (currentPage === 'home' && href === 'index.html')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Toggle dark mode
function toggleDarkMode() {
    if (document.body.classList.contains('dark-mode')) {
        disableDarkMode();
    } else {
        enableDarkMode();
    }
}

function enableDarkMode() {
    document.body.classList.add('dark-mode');
    if (themeToggle) themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
    localStorage.setItem('darkMode', 'enabled');
}

function disableDarkMode() {
    document.body.classList.remove('dark-mode');
    if (themeToggle) themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
    localStorage.setItem('darkMode', 'disabled');
}

// Toggle mobile menu
function toggleMobileMenu() {
    nav.classList.toggle('active');
    mobileMenuBtn.innerHTML = nav.classList.contains('active') ? 
        '<i class="fas fa-times"></i>' : '<i class="fas fa-bars"></i>';
}

// Animate statistics on home page
function animateStatistics() {
    const potholesCount = document.getElementById('potholesCount');
    const accidentsPrevented = document.getElementById('accidentsPrevented');
    const roadsMonitored = document.getElementById('roadsMonitored');
    const issuesResolved = document.getElementById('issuesResolved');
    
    if (!potholesCount) return;
    
    // Target values
    const targetStats = {
        potholes: 1247,
        accidents: 342,
        roads: 156,
        resolved: 892
    };
    
    // Animate each statistic
    animateValue(potholesCount, 0, targetStats.potholes, 2000);
    animateValue(accidentsPrevented, 0, targetStats.accidents, 2000);
    animateValue(roadsMonitored, 0, targetStats.roads, 2000);
    animateValue(issuesResolved, 0, targetStats.resolved, 2000);
}

// Animate value counter
function animateValue(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        element.textContent = value.toLocaleString();
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', initApp);