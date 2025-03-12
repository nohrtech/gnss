document.addEventListener('DOMContentLoaded', function() {
    // Load base stations
    loadBaseStations();

    // Handle form submission
    const form = document.getElementById('uploadForm');
    const progressBar = document.querySelector('#uploadProgress .progress-bar');
    const progressDiv = document.getElementById('uploadProgress');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        progressDiv.classList.remove('d-none');
        progressBar.style.width = '0%';

        try {
            // Upload file
            const uploadResponse = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!uploadResponse.ok) {
                const errorData = await uploadResponse.json();
                throw new Error(errorData.error || 'Upload failed');
            }

            const uploadResult = await uploadResponse.json();
            progressBar.style.width = '50%';

            // Process the dataset
            const processResponse = await fetch(`/api/process/${uploadResult.dataset_id}`, {
                method: 'POST'
            });

            if (!processResponse.ok) {
                const errorData = await processResponse.json();
                throw new Error(errorData.error || 'Processing failed');
            }

            progressBar.style.width = '100%';
            
            // Show success message and redirect
            showAlert('File uploaded and processed successfully', 'success');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);

        } catch (error) {
            console.error('Error:', error);
            showAlert(error.message || 'Error uploading file', 'danger');
            progressDiv.classList.add('d-none');
        }
    });
});

// Load base stations into select dropdown
async function loadBaseStations() {
    try {
        const response = await fetch('/api/base-stations');
        if (!response.ok) throw new Error('Failed to fetch base stations');
        
        const stations = await response.json();
        const select = document.getElementById('baseStation');
        
        stations.forEach(station => {
            const option = document.createElement('option');
            option.value = station.id;
            option.textContent = `${station.name} (${station.latitude.toFixed(6)}, ${station.longitude.toFixed(6)})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading base stations:', error);
        showAlert('Error loading base stations', 'warning');
    }
}

// Show alert message
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '1050';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}
