document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const progressBar = document.querySelector('#uploadProgress .progress-bar');
    const progressDiv = document.getElementById('uploadProgress');
    const statusDiv = document.getElementById('uploadStatus');

    loadBaseStations();

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        progressDiv.classList.remove('d-none');
        progressBar.style.width = '0%';
        statusDiv.textContent = 'Uploading...';

        try {
            const formData = new FormData(form);
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json'
                }
            });

            // First try to get the response text
            const responseText = await response.text();
            console.log('Raw server response:', responseText);

            // Then try to parse it as JSON
            let data;
            try {
                data = JSON.parse(responseText);
            } catch (error) {
                console.error('Failed to parse JSON response:', error);
                throw new Error('Server returned invalid JSON response');
            }

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Upload failed');
            }

            progressBar.style.width = '50%';
            statusDiv.textContent = 'Processing...';

            // Process the dataset
            const processResponse = await fetch(`/api/process/${data.dataset_id}`, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json'
                }
            });

            const processText = await processResponse.text();
            console.log('Raw process response:', processText);

            let processData;
            try {
                processData = JSON.parse(processText);
            } catch (error) {
                console.error('Failed to parse JSON response:', error);
                throw new Error('Server returned invalid JSON response during processing');
            }

            if (!processResponse.ok || !processData.success) {
                throw new Error(processData.error || 'Processing failed');
            }

            progressBar.style.width = '100%';
            statusDiv.textContent = 'Success!';
            showAlert('File uploaded and processed successfully', 'success');

            // Redirect to dashboard after success
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);

        } catch (error) {
            console.error('Error:', error);
            progressDiv.classList.add('d-none');
            showAlert(error.message || 'Error uploading file', 'danger');
        }
    });
});

async function loadBaseStations() {
    try {
        const response = await fetch('/api/base-stations', {
            headers: {
                'Accept': 'application/json'
            }
        });

        const responseText = await response.text();
        console.log('Raw base stations response:', responseText);

        let data;
        try {
            data = JSON.parse(responseText);
        } catch (error) {
            console.error('Failed to parse JSON response:', error);
            throw new Error('Server returned invalid JSON response');
        }

        if (!response.ok || (data.success === false)) {
            throw new Error(data.error || 'Failed to fetch base stations');
        }

        const select = document.getElementById('baseStation');
        
        if (!Array.isArray(data)) {
            throw new Error('Invalid base stations data format');
        }

        data.forEach(station => {
            if (station && station.id && station.name) {
                const option = document.createElement('option');
                option.value = station.id;
                option.textContent = `${station.name} (${station.latitude.toFixed(6)}, ${station.longitude.toFixed(6)})`;
                select.appendChild(option);
            }
        });
    } catch (error) {
        console.error('Error loading base stations:', error);
        showAlert('Error loading base stations: ' + error.message, 'warning');
    }
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '1050';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}
