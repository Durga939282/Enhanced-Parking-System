let parkingData = {};

function createParkingSlot(spot) {
    const slot = document.createElement('div');
    slot.className = `parking-slot slot-${spot.status}`;
    
    const statusText = spot.status.charAt(0).toUpperCase() + spot.status.slice(1);
    const statusIndicator = document.createElement('span');
    statusIndicator.className = `status-indicator status-${spot.status}`;
    statusIndicator.textContent = statusText;
    
    const carNumber = document.createElement('div');
    carNumber.className = 'car-number';
    carNumber.textContent = spot.car_number || 'Empty';
    
    slot.appendChild(statusIndicator);
    slot.appendChild(carNumber);
    
    return slot;
}

function updateDashboard() {
    fetch('/get_parking_status')
        .then(response => response.json())
        .then(data => {
            // Update stats with animation
            updateStatWithAnimation('total-spots', data.total_spots);
            updateStatWithAnimation('available-spots', data.available);
            updateStatWithAnimation('occupied-spots', data.occupied);

            // Update parking grid
            const parkingGrid = document.getElementById('parking-grid');
            data.spots.forEach(spot => {
                const spotId = `spot-${spot.id}`;
                let spotElement = document.getElementById(spotId);
                
                if (!spotElement) {
                    spotElement = document.createElement('div');
                    spotElement.id = spotId;
                    parkingGrid.appendChild(spotElement);
                }

                // Update spot status with animation
                if (spotElement.getAttribute('data-status') !== spot.status) {
                    spotElement.className = `parking-spot ${spot.status}`;
                    spotElement.setAttribute('data-status', spot.status);
                    spotElement.innerHTML = `
                        <h3>Spot ${spot.id}</h3>
                        <p>${spot.status.toUpperCase()}</p>
                        <p class="plate-info">${spot.plate ? 'Plate: ' + spot.plate : 'No plate detected'}</p>
                        <i class="fas ${spot.status === 'occupied' ? 'fa-car' : 'fa-square-parking'}"></i>
                    `;
                    spotElement.classList.add('updated');
                    setTimeout(() => spotElement.classList.remove('updated'), 300);
                }
            });
        })
        .catch(error => console.error('Error updating dashboard:', error));
}

function updateStatWithAnimation(elementId, newValue) {
    const element = document.getElementById(elementId);
    const currentValue = parseInt(element.textContent);
    
    if (currentValue !== newValue) {
        element.textContent = newValue;
        element.parentElement.parentElement.classList.add('updated');
        setTimeout(() => {
            element.parentElement.parentElement.classList.remove('updated');
        }, 300);
    }
}

// Update every 200ms
setInterval(updateDashboard, 200);

// Initial update
updateDashboard();

// Add hover effects
document.addEventListener('DOMContentLoaded', () => {
    const parkingGrid = document.getElementById('parking-grid');
    parkingGrid.addEventListener('mouseover', (e) => {
        const spot = e.target.closest('.parking-spot');
        if (spot) {
            spot.style.transform = 'scale(1.05)';
        }
    });

    parkingGrid.addEventListener('mouseout', (e) => {
        const spot = e.target.closest('.parking-spot');
        if (spot) {
            spot.style.transform = 'scale(1)';
        }
    });
});

const socket = io.connect('http://localhost:5000');

socket.on('parking_status_update', function(data) {
    const spotId = `spot-${data.spot_number}`;
    const spotElement = document.getElementById(spotId);
    if (spotElement) {
        spotElement.className = `parking-spot ${data.status}`;
        const plateInfo = spotElement.querySelector('.plate-info');
        if (plateInfo) {
            plateInfo.textContent = `Plate: ${data.plate || 'No plate detected'}`;
        }
    }
});