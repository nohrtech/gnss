// Dashboard initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize map
    const map = L.map('map').setView([0, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Initialize accuracy chart
    const ctx = document.getElementById('accuracyChart').getContext('2d');
    const accuracyChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Horizontal Error',
                data: [],
                backgroundColor: 'rgba(54, 162, 235, 0.5)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Error (m)'
                    }
                }
            }
        }
    });

    // Load datasets
    loadDatasets();

    // Event listeners
    document.getElementById('uploadBtn').addEventListener('click', () => {
        window.location.href = '/upload';
    });
});

// Load and display datasets
async function loadDatasets() {
    try {
        const response = await fetch('/api/results');
        if (!response.ok) throw new Error('Failed to fetch datasets');
        
        const data = await response.json();
        updateResultsTable(data);
        updateMap(data);
        updateChart(data);
    } catch (error) {
        console.error('Error loading datasets:', error);
        showAlert('Error loading datasets', 'danger');
    }
}

// Update results table
function updateResultsTable(data) {
    const tbody = document.querySelector('#resultsTable tbody');
    tbody.innerHTML = '';

    data.forEach(dataset => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${dataset.name}</td>
            <td>${new Date(dataset.upload_date).toLocaleDateString()}</td>
            <td>${dataset.format_type}</td>
            <td>${dataset.results.horizontal.rmse.toFixed(3)} m</td>
            <td>${dataset.results.vertical.rmse.toFixed(3)} m</td>
            <td>${dataset.results.num_points}</td>
            <td>
                <button class="btn btn-sm btn-info" onclick="showDetails(${dataset.id})">
                    Details
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteDataset(${dataset.id})">
                    Delete
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Update map with dataset points
function updateMap(data) {
    const map = L.map('map');
    map.eachLayer((layer) => {
        if (layer instanceof L.Marker) {
            map.removeLayer(layer);
        }
    });

    data.forEach(dataset => {
        const pos = [
            dataset.results.reference_position.latitude,
            dataset.results.reference_position.longitude
        ];
        
        L.marker(pos)
            .bindPopup(`
                <strong>${dataset.name}</strong><br>
                RMSE (H): ${dataset.results.horizontal.rmse.toFixed(3)} m<br>
                RMSE (V): ${dataset.results.vertical.rmse.toFixed(3)} m
            `)
            .addTo(map);
    });

    if (data.length > 0) {
        const firstPos = [
            data[0].results.reference_position.latitude,
            data[0].results.reference_position.longitude
        ];
        map.setView(firstPos, 13);
    }
}

// Update accuracy chart
function updateChart(data) {
    const chart = Chart.getChart('accuracyChart');
    if (!chart) return;

    const datasets = data.map(dataset => ({
        label: dataset.name,
        data: [{
            x: new Date(dataset.upload_date).getTime(),
            y: dataset.results.horizontal.rmse
        }],
        backgroundColor: getRandomColor()
    }));

    chart.data.datasets = datasets;
    chart.update();
}

// Show detailed analysis
function showDetails(datasetId) {
    fetch(`/api/results/${datasetId}`)
        .then(response => response.json())
        .then(data => {
            // Update modal content
            document.getElementById('horizontalRMSE').textContent = `${data.results.horizontal.rmse.toFixed(3)} m`;
            document.getElementById('horizontalSTD').textContent = `${data.results.horizontal.std.toFixed(3)} m`;
            document.getElementById('horizontalMean').textContent = `${data.results.horizontal.mean.toFixed(3)} m`;
            document.getElementById('horizontalMax').textContent = `${data.results.horizontal.max.toFixed(3)} m`;
            document.getElementById('horizontalMin').textContent = `${data.results.horizontal.min.toFixed(3)} m`;

            document.getElementById('verticalRMSE').textContent = `${data.results.vertical.rmse.toFixed(3)} m`;
            document.getElementById('verticalSTD').textContent = `${data.results.vertical.std.toFixed(3)} m`;
            document.getElementById('verticalMean').textContent = `${data.results.vertical.mean.toFixed(3)} m`;
            document.getElementById('verticalMax').textContent = `${data.results.vertical.max.toFixed(3)} m`;
            document.getElementById('verticalMin').textContent = `${data.results.vertical.min.toFixed(3)} m`;

            document.getElementById('refLat').textContent = data.results.reference_position.latitude.toFixed(7);
            document.getElementById('refLon').textContent = data.results.reference_position.longitude.toFixed(7);
            document.getElementById('refAlt').textContent = `${data.results.reference_position.altitude.toFixed(3)} m`;
            document.getElementById('refMode').textContent = data.results.reference_mode;

            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('analysisModal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error loading dataset details:', error);
            showAlert('Error loading dataset details', 'danger');
        });
}

// Delete dataset
async function deleteDataset(datasetId) {
    if (!confirm('Are you sure you want to delete this dataset?')) return;

    try {
        const response = await fetch(`/api/datasets/${datasetId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete dataset');
        
        showAlert('Dataset deleted successfully', 'success');
        loadDatasets();
    } catch (error) {
        console.error('Error deleting dataset:', error);
        showAlert('Error deleting dataset', 'danger');
    }
}

// Utility functions
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}
