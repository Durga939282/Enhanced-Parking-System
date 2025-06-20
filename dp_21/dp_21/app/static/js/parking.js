document.addEventListener('DOMContentLoaded', function() {
    // Update parking data every 3 seconds
    setInterval(updateParkingData, 3000);
});

function updateParkingData() {
    fetch('/api/parking/status')
        .then(response => response.json())
        .then(data => {
            // Update each parking spot
            for (let spotNum in data) {
                updateSpotUI(spotNum, data[spotNum]);
            }
        })
        .catch(error => console.error('Error fetching parking data:', error));
}

function updateSpotUI(spotNum, spotData) {
    const spotElement = document.getElementById(`spot-${spotNum}`);
    if (!spotElement) return;
    
    // Update status class
    spotElement.className = `spot ${spotData.status}`;
    
    // Update plate info
    const plateElement = spotElement.querySelector('.plate-info');
    if (plateElement) {
        if (spotData.status === 'occupied' && spotData.plate) {
            plateElement.textContent = `Plate: ${spotData.plate}`;
        } else if (spotData.status === 'occupied') {
            plateElement.textContent = 'No plate detected';
        } else {
            plateElement.textContent = 'Available';
        }
    }
} 