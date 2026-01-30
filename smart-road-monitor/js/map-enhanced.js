// map-enhanced.js - Enhanced map functionality with better location detection
let map;
let markers = [];
let userMarker;
let userLocationCircle;
let roadIssues = [];
let currentFilters = { high: true, medium: true, low: true };
let autoRefreshInterval;

// Initialize map
function initMap() {
    // Create map with better tile layer
    map = L.map('roadMap').setView([40.7128, -74.0060], 13);
    
    // Use OpenStreetMap with custom styling
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
    }).addTo(map);
    
    // Add additional tile layer for better visual
    L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
        maxZoom: 19,
        opacity: 0.3
    }).addTo(map);
    
    // Load road issues
    loadRoadIssues();
    
    // Set up event listeners
    setupEventListeners();
    
    // Setup auto-refresh
    setupAutoRefresh();
    
    // Add custom controls
    addCustomControls();
}

// Load road issues with more realistic data
function loadRoadIssues() {
    // More comprehensive road issues data
    roadIssues = [
        { id: 1024, lat: 40.7128, lng: -74.0060, type: 'pothole', severity: 'high', 
          description: 'Large pothole (2ft diameter, 6in deep) causing vehicle damage', 
          date: '2023-10-15', address: 'Main Street, Downtown', reporter: 'AI Detection' },
        
        { id: 1023, lat: 40.7215, lng: -74.0092, type: 'crack', severity: 'medium', 
          description: 'Multiple longitudinal cracks across lane', 
          date: '2023-10-14', address: 'Oak Avenue near Park', reporter: 'Citizen Report' },
        
        { id: 1022, lat: 40.7150, lng: -74.0130, type: 'pothole', severity: 'high', 
          description: 'Deep pothole near intersection, filled with water', 
          date: '2023-10-15', address: '5th Avenue & Broadway', reporter: 'IoT Sensor' },
        
        { id: 1021, lat: 40.7080, lng: -74.0050, type: 'speed-hump', severity: 'low', 
          description: 'Unmarked speed hump causing vehicle bottoming', 
          date: '2023-10-13', address: 'River Road Bridge', reporter: 'Citizen Report' },
        
        { id: 1020, lat: 40.7050, lng: -74.0150, type: 'crack', severity: 'medium', 
          description: 'Alligator cracking over 10sqm area', 
          date: '2023-10-14', address: 'Park Avenue South', reporter: 'AI Detection' },
        
        { id: 1019, lat: 40.7200, lng: -74.0020, type: 'pothole', severity: 'high', 
          description: 'Cluster of potholes in right lane', 
          date: '2023-10-15', address: 'Central Park West', reporter: 'IoT Sensor' },
        
        { id: 1018, lat: 40.7100, lng: -74.0080, type: 'flooding', severity: 'medium', 
          description: 'Poor drainage causing regular flooding after rain', 
          date: '2023-10-12', address: 'Wall Street Area', reporter: 'Citizen Report' },
        
        { id: 1017, lat: 40.7180, lng: -74.0100, type: 'pothole', severity: 'high', 
          description: 'Multiple potholes near bus stop', 
          date: '2023-10-15', address: '7th Avenue Bus Stop', reporter: 'AI Detection' },
        
        { id: 1016, lat: 40.7020, lng: -74.0120, type: 'crack', severity: 'low', 
          description: 'Minor edge cracks on shoulder', 
          date: '2023-10-13', address: 'Battery Park Blvd', reporter: 'IoT Sensor' },
        
        { id: 1015, lat: 40.7250, lng: -74.0050, type: 'debris', severity: 'medium', 
          description: 'Construction debris in lane', 
          date: '2023-10-14', address: 'Upper West Side', reporter: 'Citizen Report' }
    ];
    
    updateMarkers();
}

// Update markers based on filters
function updateMarkers() {
    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
    
    // Add filtered markers
    roadIssues.forEach(issue => {
        if (!currentFilters[issue.severity]) return;
        
        const marker = createMarker(issue);
        markers.push(marker);
    });
}

// Create marker with custom icon
function createMarker(issue) {
    let markerColor, icon, size;
    
    switch(issue.severity) {
        case 'high':
            markerColor = '#e63946';
            icon = 'exclamation';
            size = 32;
            break;
        case 'medium':
            markerColor = '#ffc107';
            icon = 'exclamation-triangle';
            size = 28;
            break;
        case 'low':
            markerColor = '#2a9d8f';
            icon = 'info';
            size = 24;
            break;
    }
    
    // Create custom marker icon
    const markerIcon = L.divIcon({
        html: `
            <div style="
                width: ${size}px;
                height: ${size}px;
                background-color: ${markerColor};
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: ${size/2}px;
            ">
                <i class="fas fa-${icon}"></i>
            </div>
        `,
        className: 'custom-marker',
        iconSize: [size, size],
        iconAnchor: [size/2, size/2]
    });
    
    const marker = L.marker([issue.lat, issue.lng], { 
        icon: markerIcon,
        title: `${issue.type} - ${issue.severity} priority`
    }).addTo(map);
    
    // Create popup content
    const popupContent = createPopupContent(issue);
    marker.bindPopup(popupContent);
    
    return marker;
}

// Create popup content
function createPopupContent(issue) {
    let severityColor, severityIcon;
    
    switch(issue.severity) {
        case 'high':
            severityColor = '#e63946';
            severityIcon = 'exclamation-circle';
            break;
        case 'medium':
            severityColor = '#ffc107';
            severityIcon = 'exclamation-triangle';
            break;
        case 'low':
            severityColor = '#2a9d8f';
            severityIcon = 'info-circle';
            break;
    }
    
    return `
        <div style="min-width: 250px; padding: 10px;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                <div style="
                    width: 40px;
                    height: 40px;
                    background-color: ${severityColor};
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 1.2rem;
                ">
                    <i class="fas fa-${severityIcon}"></i>
                </div>
                <div>
                    <h3 style="margin: 0; text-transform: capitalize;">${issue.type.replace('-', ' ')}</h3>
                    <p style="margin: 5px 0 0; font-size: 0.9rem; color: #666;">
                        ${issue.address}
                    </p>
                </div>
            </div>
            
            <div style="margin-bottom: 15px;">
                <p style="margin: 0 0 10px;">${issue.description}</p>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;">
                    <div>
                        <strong>Priority:</strong><br>
                        <span style="color: ${severityColor}; font-weight: bold;">${issue.severity.toUpperCase()}</span>
                    </div>
                    <div>
                        <strong>Reported:</strong><br>
                        ${issue.date}
                    </div>
                    <div>
                        <strong>Source:</strong><br>
                        ${issue.reporter}
                    </div>
                    <div>
                        <strong>ID:</strong><br>
                        #${issue.id}
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 15px;">
                <a href="report.html" 
                   style="
                       display: inline-block;
                       padding: 8px 16px;
                       background-color: ${severityColor};
                       color: white;
                       text-decoration: none;
                       border-radius: 5px;
                       font-size: 0.9rem;
                   ">
                    <i class="fas fa-plus"></i> Report Similar Issue
                </a>
            </div>
        </div>
    `;
}

// Find user location
function findUserLocation() {
    const locationBtn = document.getElementById('findMyLocation');
    const loadingIndicator = document.getElementById('locationLoading');
    
    // Show loading
    locationBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    locationBtn.disabled = true;
    loadingIndicator.style.display = 'flex';
    
    if (!navigator.geolocation) {
        showLocationError('Geolocation is not supported by your browser');
        resetLocationButton();
        return;
    }
    
    // Request high accuracy location
    navigator.geolocation.getCurrentPosition(
        // Success callback
        (position) => {
            const { latitude, longitude, accuracy } = position.coords;
            
            // Center map on user location
            map.setView([latitude, longitude], 16);
            
            // Remove existing user marker
            if (userMarker) {
                map.removeLayer(userMarker);
                if (userLocationCircle) {
                    map.removeLayer(userLocationCircle);
                }
            }
            
            // Create accuracy circle
            userLocationCircle = L.circle([latitude, longitude], {
                color: '#1e3d8f',
                fillColor: '#1e3d8f',
                fillOpacity: 0.2,
                radius: accuracy
            }).addTo(map);
            
            // Create user marker
            userMarker = L.marker([latitude, longitude], {
                icon: L.divIcon({
                    html: `
                        <div style="
                            width: 40px;
                            height: 40px;
                            background-color: #1e3d8f;
                            border-radius: 50%;
                            border: 3px solid white;
                            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-size: 1.2rem;
                            animation: pulse 2s infinite;
                        ">
                            <i class="fas fa-user"></i>
                        </div>
                    `,
                    className: 'user-location-marker',
                    iconSize: [40, 40],
                    iconAnchor: [20, 40]
                })
            }).addTo(map);
            
            // Bind popup with location info
            const accuracyMeters = Math.round(accuracy);
            const accuracyText = accuracyMeters < 20 ? 'High' : 
                                accuracyMeters < 50 ? 'Medium' : 'Low';
            
            userMarker.bindPopup(`
                <div style="padding: 10px; min-width: 200px;">
                    <h4 style="margin: 0 0 10px;">
                        <i class="fas fa-map-marker-alt"></i> Your Location
                    </h4>
                    <p style="margin: 0 0 10px;">
                        <strong>Accuracy:</strong> ${accuracyText} (±${accuracyMeters}m)
                    </p>
                    <p style="margin: 0; font-size: 0.9rem; color: #666;">
                        Coordinates: ${latitude.toFixed(6)}, ${longitude.toFixed(6)}
                    </p>
                </div>
            `).openPopup();
            
            // Update location info in UI
            updateLocationInfo(latitude, longitude, accuracy);
            
            // Reset button
            resetLocationButton();
            loadingIndicator.style.display = 'none';
        },
        // Error callback
        (error) => {
            let errorMessage = 'Unable to retrieve your location. ';
            
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    errorMessage += 'Please allow location access in your browser settings.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMessage += 'Location information is unavailable.';
                    break;
                case error.TIMEOUT:
                    errorMessage += 'Location request timed out.';
                    break;
                default:
                    errorMessage += 'An unknown error occurred.';
            }
            
            showLocationError(errorMessage);
            resetLocationButton();
            loadingIndicator.style.display = 'none';
        },
        // Options
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }
    );
}

// Update location information in UI
function updateLocationInfo(lat, lng, accuracy) {
    // This function can be expanded to show location details in a panel
    console.log(`Location found: ${lat}, ${lng} (accuracy: ${accuracy}m)`);
    
    // You could update a location info panel here
    // document.getElementById('locationInfo').innerHTML = `
    //     <strong>Your Location:</strong><br>
    //     Latitude: ${lat.toFixed(6)}<br>
    //     Longitude: ${lng.toFixed(6)}<br>
    //     Accuracy: ±${Math.round(accuracy)} meters
    // `;
}

// Show location error
function showLocationError(message) {
    alert(message);
}

// Reset location button
function resetLocationButton() {
    const locationBtn = document.getElementById('findMyLocation');
    locationBtn.innerHTML = '<i class="fas fa-location-arrow"></i>';
    locationBtn.disabled = false;
}

// Setup event listeners
function setupEventListeners() {
    // Location button
    const locationBtn = document.getElementById('findMyLocation');
    if (locationBtn) {
        locationBtn.addEventListener('click', findUserLocation);
    }
    
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.getAttribute('data-filter');
            this.classList.toggle('active');
            currentFilters[filter] = !currentFilters[filter];
            updateMarkers();
        });
    });
    
    // Auto-refresh checkbox
    const autoRefreshCheckbox = document.getElementById('autoRefresh');
    if (autoRefreshCheckbox) {
        autoRefreshCheckbox.addEventListener('change', function() {
            if (this.checked) {
                setupAutoRefresh();
            } else {
                clearAutoRefresh();
            }
        });
    }
    
    // Watch for map clicks to add custom markers (for demo)
    map.on('click', function(e) {
        // This is for demo purposes - in real app, this would open a report form
        console.log(`Map clicked at: ${e.latlng.lat}, ${e.latlng.lng}`);
    });
}

// Setup auto-refresh
function setupAutoRefresh() {
    // Clear any existing interval
    clearAutoRefresh();
    
    // Set new interval (30 seconds)
    autoRefreshInterval = setInterval(() => {
        // Simulate new data
        simulateNewData();
        updateMarkers();
        
        // Update live status timestamp
        updateLiveStatus();
    }, 30000);
}

// Clear auto-refresh
function clearAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Simulate new data (for demo)
function simulateNewData() {
    // 20% chance of adding a new issue
    if (Math.random() > 0.8) {
        const newIssue = {
            id: Math.floor(Math.random() * 9000) + 1000,
            lat: 40.7128 + (Math.random() - 0.5) * 0.05,
            lng: -74.0060 + (Math.random() - 0.5) * 0.05,
            type: ['pothole', 'crack', 'speed-hump', 'flooding'][Math.floor(Math.random() * 4)],
            severity: ['high', 'medium', 'low'][Math.floor(Math.random() * 3)],
            description: 'New issue detected by AI system',
            date: new Date().toISOString().split('T')[0],
            address: 'New York City',
            reporter: 'AI Detection'
        };
        
        roadIssues.push(newIssue);
    }
    
    // 10% chance of resolving an issue
    if (Math.random() > 0.9 && roadIssues.length > 0) {
        const randomIndex = Math.floor(Math.random() * roadIssues.length);
        roadIssues.splice(randomIndex, 1);
    }
}

// Update live status
function updateLiveStatus() {
    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Update status text if element exists
    const statusElement = document.querySelector('.live-status span');
    if (statusElement) {
        statusElement.innerHTML = `<strong>Live Data:</strong> Updated ${timeString} • ${roadIssues.length} active issues`;
    }
}

// Add custom controls to map
function addCustomControls() {
    // Add scale control
    L.control.scale({ imperial: true, metric: true }).addTo(map);
    
    // Add attribution control
    L.control.attribution({
        prefix: 'Smart Road Monitor'
    }).addTo(map);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initMap);