// report-enhanced.js - Enhanced report functionality with better location detection
let currentStep = 1;
let userLocation = null;
let selectedImage = null;
let formData = {
    location: '',
    locationDetails: {},
    issueType: '',
    severity: '',
    description: '',
    image: null,
    email: ''
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeForm();
    setupEventListeners();
    setupLocationAutocomplete();
});

// Initialize form
function initializeForm() {
    updateStepIndicator();
    updateFormStep();
}

// Setup event listeners
function setupEventListeners() {
    // Step navigation
    document.getElementById('nextStep1')?.addEventListener('click', nextStep);
    document.getElementById('nextStep2')?.addEventListener('click', nextStep);
    document.getElementById('prevStep2')?.addEventListener('click', prevStep);
    document.getElementById('prevStep3')?.addEventListener('click', prevStep);
    
    // Location detection
    document.getElementById('detectLocation')?.addEventListener('click', detectUserLocation);
    document.getElementById('useMap')?.addEventListener('click', openMapSelector);
    document.getElementById('clearLocation')?.addEventListener('click', clearLocation);
    document.getElementById('adjustLocation')?.addEventListener('click', adjustLocation);
    document.getElementById('viewOnMap')?.addEventListener('click', viewOnMap);
    
    // Issue type selection
    document.querySelectorAll('input[name="issueType"]').forEach(radio => {
        radio.addEventListener('change', function() {
            formData.issueType = this.value;
        });
    });
    
    // Severity selection
    document.querySelectorAll('.severity-visual-item').forEach(item => {
        item.addEventListener('click', function() {
            const severity = this.getAttribute('data-severity');
            selectSeverity(severity);
        });
    });
    
    // Image upload
    document.getElementById('imageUpload')?.addEventListener('click', () => {
        document.getElementById('issueImage').click();
    });
    
    document.getElementById('issueImage')?.addEventListener('change', handleImageUpload);
    document.getElementById('removeImage')?.addEventListener('click', removeImage);
    
    // Form submission
    document.getElementById('reportForm')?.addEventListener('submit', handleFormSubmit);
    
    // Success actions
    document.getElementById('reportAnother')?.addEventListener('click', resetForm);
    document.getElementById('printReport')?.addEventListener('click', printReport);
    
    // Real-time location tracking
    setupLocationChangeListener();
}

// Setup location autocomplete
function setupLocationAutocomplete() {
    const locationInput = document.getElementById('issueLocation');
    const suggestionsContainer = document.getElementById('locationSuggestions');
    
    if (!locationInput) return;
    
    let debounceTimer;
    
    locationInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const query = this.value.trim();
            if (query.length > 2) {
                searchLocations(query);
            } else {
                hideSuggestions();
            }
        }, 300);
    });
    
    locationInput.addEventListener('focus', function() {
        const query = this.value.trim();
        if (query.length > 2) {
            searchLocations(query);
        }
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!suggestionsContainer.contains(e.target) && e.target !== locationInput) {
            hideSuggestions();
        }
    });
}

// Search locations (simulated)
function searchLocations(query) {
    const suggestionsContainer = document.getElementById('locationSuggestions');
    const sampleLocations = [
        "Main Street, Downtown, New York",
        "Broadway & 42nd Street, Times Square",
        "Central Park West, New York",
        "5th Avenue, Manhattan",
        "Wall Street, Financial District",
        "Park Avenue, Midtown",
        "Brooklyn Bridge, New York",
        "Times Square, Manhattan",
        "Empire State Building, 34th Street",
        "Statue of Liberty, Liberty Island"
    ];
    
    // Filter sample locations
    const filtered = sampleLocations.filter(loc => 
        loc.toLowerCase().includes(query.toLowerCase())
    );
    
    if (filtered.length > 0) {
        showSuggestions(filtered);
    } else {
        hideSuggestions();
    }
}

// Show location suggestions
function showSuggestions(locations) {
    const suggestionsContainer = document.getElementById('locationSuggestions');
    suggestionsContainer.innerHTML = '';
    
    locations.forEach(location => {
        const item = document.createElement('div');
        item.className = 'suggest-item';
        item.textContent = location;
        item.addEventListener('click', function() {
            document.getElementById('issueLocation').value = location;
            hideSuggestions();
            // Simulate selecting this location
            simulateLocationSelection(location);
        });
        suggestionsContainer.appendChild(item);
    });
    
    suggestionsContainer.style.display = 'block';
}

// Hide suggestions
function hideSuggestions() {
    document.getElementById('locationSuggestions').style.display = 'none';
}

// Simulate location selection
function simulateLocationSelection(address) {
    formData.location = address;
    formData.locationDetails = {
        address: address,
        coordinates: { lat: 40.7128 + (Math.random() - 0.5) * 0.01, lng: -74.0060 + (Math.random() - 0.5) * 0.01 },
        accuracy: 50 + Math.random() * 100
    };
    
    showLocationPreview();
}

// Detect user location with high accuracy
function detectUserLocation() {
    const detectBtn = document.getElementById('detectLocation');
    const errorDiv = document.getElementById('locationError');
    const successDiv = document.getElementById('locationSuccess');
    
    // Reset messages
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';
    
    // Update button state
    detectBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detecting...';
    detectBtn.disabled = true;
    
    if (!navigator.geolocation) {
        showLocationError('Geolocation is not supported by your browser.');
        resetLocationButton();
        return;
    }
    
    // Request high accuracy location
    const options = {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
    };
    
    navigator.geolocation.getCurrentPosition(
        // Success callback
        (position) => {
            const { latitude, longitude, accuracy } = position.coords;
            
            // Store location data
            userLocation = {
                lat: latitude,
                lng: longitude,
                accuracy: accuracy
            };
            
            // Get address from coordinates (simulated)
            getAddressFromCoordinates(latitude, longitude);
            
            // Show success message
            successDiv.style.display = 'block';
            resetLocationButton();
        },
        // Error callback
        (error) => {
            let errorMessage = 'Unable to detect location. ';
            
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    errorMessage = 'Location access denied. Please enable location services in your browser settings.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMessage = 'Location information is unavailable. Please check your device settings.';
                    break;
                case error.TIMEOUT:
                    errorMessage = 'Location request timed out. Please try again.';
                    break;
                default:
                    errorMessage = 'An unknown error occurred while detecting location.';
            }
            
            showLocationError(errorMessage);
            resetLocationButton();
        },
        options
    );
}

// Get address from coordinates (simulated)
function getAddressFromCoordinates(lat, lng) {
    // In a real app, this would use a geocoding API like Google Maps or OpenStreetMap
    // For demo, we'll use sample addresses based on coordinates
    
    const sampleAddresses = [
        "Main Street, Downtown, New York",
        "Broadway, Manhattan, New York",
        "5th Avenue, New York",
        "Park Avenue, Manhattan",
        "Wall Street, Financial District"
    ];
    
    const randomAddress = sampleAddresses[Math.floor(Math.random() * sampleAddresses.length)];
    const accuracy = userLocation.accuracy;
    
    // Update form data
    formData.location = randomAddress;
    formData.locationDetails = {
        address: randomAddress,
        coordinates: { lat, lng },
        accuracy: accuracy,
        timestamp: new Date().toISOString()
    };
    
    // Update UI
    document.getElementById('issueLocation').value = randomAddress;
    document.getElementById('detectedAddress').textContent = randomAddress;
    
    // Update accuracy display
    const accuracyPercent = Math.max(10, Math.min(100, 100 - (accuracy / 100)));
    document.getElementById('accuracyFill').style.width = `${accuracyPercent}%`;
    document.getElementById('accuracyText').textContent = 
        accuracy < 20 ? 'High' : accuracy < 50 ? 'Medium' : 'Low';
    
    showLocationPreview();
    
    // Show on map preview
    updateMapPreview(lat, lng);
}

// Show location preview
function showLocationPreview() {
    document.getElementById('locationPreview').style.display = 'block';
    document.getElementById('locationMapPreview').style.display = 'flex';
}

// Update map preview
function updateMapPreview(lat, lng) {
    const mapPreview = document.getElementById('locationMapPreview');
    
    // In a real app, you would embed a small map here
    // For demo, we'll show coordinates
    mapPreview.innerHTML = `
        <div style="text-align: center;">
            <i class="fas fa-map-marker-alt" style="font-size: 2rem; color: var(--secondary-green); margin-bottom: 10px;"></i>
            <h4 style="margin: 0 0 10px;">Location Detected</h4>
            <p style="margin: 0; font-size: 0.9rem;">
                Coordinates: ${lat.toFixed(6)}, ${lng.toFixed(6)}<br>
                Accuracy: ±${Math.round(userLocation.accuracy)} meters
            </p>
        </div>
    `;
}

// Show location error
function showLocationError(message) {
    const errorDiv = document.getElementById('locationError');
    document.getElementById('errorMessage').textContent = message;
    errorDiv.style.display = 'block';
}

// Reset location button
function resetLocationButton() {
    const detectBtn = document.getElementById('detectLocation');
    detectBtn.innerHTML = '<i class="fas fa-location-arrow"></i> Detect My Location';
    detectBtn.disabled = false;
}

// Open map selector (simulated)
function openMapSelector() {
    alert('Map selector would open here. In a real application, this would open an interactive map to select the exact location.');
}

// Clear location
function clearLocation() {
    formData.location = '';
    formData.locationDetails = {};
    document.getElementById('issueLocation').value = '';
    document.getElementById('locationPreview').style.display = 'none';
    document.getElementById('locationMapPreview').style.display = 'none';
    document.getElementById('locationError').style.display = 'none';
    document.getElementById('locationSuccess').style.display = 'none';
}

// Adjust location
function adjustLocation() {
    alert('Location adjustment would open here. You could drag a pin on a map to adjust the exact position.');
}

// View on map
function viewOnMap() {
    if (formData.locationDetails.coordinates) {
        const { lat, lng } = formData.locationDetails.coordinates;
        window.open(`map.html?lat=${lat}&lng=${lng}`, '_blank');
    }
}

// Select severity
function selectSeverity(severity) {
    formData.severity = severity;
    
    // Update visual selection
    document.querySelectorAll('.severity-visual-item').forEach(item => {
        item.style.opacity = item.getAttribute('data-severity') === severity ? '1' : '0.5';
        item.style.transform = item.getAttribute('data-severity') === severity ? 'scale(1.1)' : 'scale(1)';
    });
    
    // Update hidden input
    document.getElementById('severityLevel').value = severity;
}

// Handle image upload
function handleImageUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file
    const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
    if (!validTypes.includes(file.type)) {
        alert('Please upload only JPG, PNG, or GIF images.');
        return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
        alert('File size exceeds 5MB limit. Please choose a smaller image.');
        return;
    }
    
    // Store file
    selectedImage = file;
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewImg = document.getElementById('previewImage');
        previewImg.src = e.target.result;
        document.getElementById('imagePreviewContainer').style.display = 'block';
        document.getElementById('imageUpload').style.display = 'none';
    };
    reader.readAsDataURL(file);
}

// Remove image
function removeImage() {
    selectedImage = null;
    document.getElementById('issueImage').value = '';
    document.getElementById('imagePreviewContainer').style.display = 'none';
    document.getElementById('imageUpload').style.display = 'block';
    document.getElementById('previewImage').src = '';
}

// Next step
function nextStep() {
    // Validate current step
    if (!validateStep(currentStep)) {
        return;
    }
    
    currentStep++;
    updateStepIndicator();
    updateFormStep();
    
    // If moving to step 3, update summary
    if (currentStep === 3) {
        updateReportSummary();
    }
}

// Previous step
function prevStep() {
    currentStep--;
    updateStepIndicator();
    updateFormStep();
}

// Validate step
function validateStep(step) {
    switch(step) {
        case 1:
            if (!formData.location.trim()) {
                alert('Please enter or detect a location for the issue.');
                return false;
            }
            return true;
            
        case 2:
            if (!formData.issueType) {
                alert('Please select the type of issue.');
                return false;
            }
            if (!formData.severity) {
                alert('Please select the severity level.');
                return false;
            }
            return true;
            
        default:
            return true;
    }
}

// Update step indicator
function updateStepIndicator() {
    document.querySelectorAll('.step').forEach(step => {
        const stepNum = parseInt(step.getAttribute('data-step'));
        step.classList.remove('active', 'completed');
        
        if (stepNum === currentStep) {
            step.classList.add('active');
        } else if (stepNum < currentStep) {
            step.classList.add('completed');
        }
    });
}

// Update form step
function updateFormStep() {
    document.querySelectorAll('.form-step').forEach(step => {
        step.classList.remove('active');
    });
    
    document.getElementById(`step${currentStep}`).classList.add('active');
}

// Update report summary
function updateReportSummary() {
    const summaryDiv = document.getElementById('reportSummary');
    
    let severityText = '';
    let severityColor = '';
    
    switch(formData.severity) {
        case 'high':
            severityText = 'High Priority (Immediate danger)';
            severityColor = '#e63946';
            break;
        case 'medium':
            severityText = 'Medium Priority (Needs attention soon)';
            severityColor = '#ffc107';
            break;
        case 'low':
            severityText = 'Low Priority (Minor issue)';
            severityColor = '#2a9d8f';
            break;
    }
    
    summaryDiv.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr; gap: 15px;">
            <div>
                <strong>Location:</strong><br>
                ${formData.location}
                ${formData.locationDetails.coordinates ? 
                    `<div style="font-size: 0.9rem; color: #666; margin-top: 5px;">
                        Coordinates: ${formData.locationDetails.coordinates.lat.toFixed(6)}, ${formData.locationDetails.coordinates.lng.toFixed(6)}
                    </div>` : ''}
            </div>
            
            <div>
                <strong>Issue Type:</strong><br>
                ${formData.issueType ? formData.issueType.charAt(0).toUpperCase() + formData.issueType.slice(1).replace('-', ' ') : ''}
            </div>
            
            <div>
                <strong>Severity:</strong><br>
                <span style="color: ${severityColor}; font-weight: bold;">${severityText}</span>
            </div>
            
            ${formData.description ? `
                <div>
                    <strong>Description:</strong><br>
                    ${formData.description}
                </div>
            ` : ''}
            
            ${selectedImage ? `
                <div>
                    <strong>Image:</strong><br>
                    <span style="color: #2a9d8f;">
                        <i class="fas fa-check-circle"></i> Image attached (${(selectedImage.size / 1024).toFixed(1)} KB)
                    </span>
                </div>
            ` : ''}
        </div>
    `;
}

// Handle form submission
function handleFormSubmit(e) {
    e.preventDefault();
    
    // Validate all steps
    if (!validateStep(1) || !validateStep(2)) {
        currentStep = 1;
        updateStepIndicator();
        updateFormStep();
        return;
    }
    
    // Get email
    formData.email = document.getElementById('userEmail').value;
    
    // Show loading
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
    submitBtn.disabled = true;
    
    // Simulate API call
    setTimeout(() => {
        // Generate reference ID
        const refId = `SRM-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`;
        
        // Show success
        document.getElementById('reportForm').style.display = 'none';
        document.getElementById('successMessage').style.display = 'block';
        document.getElementById('referenceId').textContent = refId;
        document.getElementById('submissionTime').textContent = new Date().toLocaleTimeString([], { 
            hour: '2-digit', minute: '2-digit' 
        });
        
        // Store in localStorage
        storeReportInHistory({
            ...formData,
            referenceId: refId,
            submittedAt: new Date().toISOString(),
            status: 'pending'
        });
        
        // Reset button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }, 2000);
}

// Store report in history
function storeReportInHistory(report) {
    let reports = JSON.parse(localStorage.getItem('userReports') || '[]');
    reports.push(report);
    localStorage.setItem('userReports', JSON.stringify(reports));
}

// Reset form
function resetForm() {
    currentStep = 1;
    formData = {
        location: '',
        locationDetails: {},
        issueType: '',
        severity: '',
        description: '',
        image: null,
        email: ''
    };
    selectedImage = null;
    
    // Reset UI
    document.getElementById('reportForm').reset();
    document.getElementById('reportForm').style.display = 'block';
    document.getElementById('successMessage').style.display = 'none';
    
    // Clear location preview
    clearLocation();
    
    // Clear image preview
    removeImage();
    
    // Reset severity selection
    document.querySelectorAll('.severity-visual-item').forEach(item => {
        item.style.opacity = '1';
        item.style.transform = 'scale(1)';
    });
    
    // Reset form steps
    updateStepIndicator();
    updateFormStep();
}

// Print report
function printReport() {
    const printContent = `
        <html>
            <head>
                <title>Road Issue Report</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .section { margin-bottom: 20px; }
                    .label { font-weight: bold; color: #333; }
                    .value { margin-bottom: 10px; }
                    .footer { margin-top: 40px; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Smart Road Monitor</h1>
                    <h2>Road Issue Report</h2>
                </div>
                
                <div class="section">
                    <div class="label">Reference ID:</div>
                    <div class="value">${document.getElementById('referenceId').textContent}</div>
                </div>
                
                <div class="section">
                    <div class="label">Submitted:</div>
                    <div class="value">${new Date().toLocaleString()}</div>
                </div>
                
                <div class="section">
                    <div class="label">Location:</div>
                    <div class="value">${formData.location}</div>
                </div>
                
                <div class="section">
                    <div class="label">Issue Type:</div>
                    <div class="value">${formData.issueType ? formData.issueType.charAt(0).toUpperCase() + formData.issueType.slice(1).replace('-', ' ') : ''}</div>
                </div>
                
                <div class="section">
                    <div class="label">Severity:</div>
                    <div class="value">${formData.severity ? formData.severity.charAt(0).toUpperCase() + formData.severity.slice(1) : ''}</div>
                </div>
                
                ${formData.description ? `
                    <div class="section">
                        <div class="label">Description:</div>
                        <div class="value">${formData.description}</div>
                    </div>
                ` : ''}
                
                <div class="footer">
                    <p>Thank you for reporting this issue. You can track its status on our website.</p>
                    <p>Smart Road Condition Monitoring System</p>
                    <p>www.smartroadmonitor.gov</p>
                </div>
            </body>
        </html>
    `;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.print();
}

// Setup location change listener (for continuous tracking)
function setupLocationChangeListener() {
    if ('geolocation' in navigator && 'watchPosition' in navigator.geolocation) {
        // Optional: Watch for position changes for better accuracy
        // navigator.geolocation.watchPosition(
        //     (position) => {
        //         // Update location if user moves significantly
        //         if (userLocation) {
        //             const newLat = position.coords.latitude;
        //             const newLng = position.coords.longitude;
        //             
        //             // Calculate distance moved
        //             const distance = calculateDistance(
        //                 userLocation.lat, userLocation.lng,
        //                 newLat, newLng
        //             );
        //             
        //             if (distance > 10) { // If moved more than 10 meters
        //                 userLocation = {
        //                     lat: newLat,
        //                     lng: newLng,
        //                     accuracy: position.coords.accuracy
        //                 };
        //                 
        //                 if (currentStep === 1) {
        //                     getAddressFromCoordinates(newLat, newLng);
        //                 }
        //             }
        //         }
        //     },
        //     (error) => {
        //         console.log('Location tracking error:', error);
        //     },
        //     {
        //         enableHighAccuracy: true,
        //         maximumAge: 10000,
        //         timeout: 5000
        //     }
        // );
    }
}

// Calculate distance between two coordinates (in meters)
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371e3; // Earth's radius in meters
    const φ1 = lat1 * Math.PI/180;
    const φ2 = lat2 * Math.PI/180;
    const Δφ = (lat2-lat1) * Math.PI/180;
    const Δλ = (lon2-lon1) * Math.PI/180;

    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return R * c;
}