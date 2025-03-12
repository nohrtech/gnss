document.addEventListener('DOMContentLoaded', function() {
    loadBaseStations();
    setupUploadForm();
});

function setupUploadForm() {
    const form = document.getElementById('uploadForm');
    const progressBar = document.querySelector('#uploadProgress .progress-bar');
    const progressDiv = document.getElementById('uploadProgress');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        progressDiv.classList.remove('d-none');
        progressBar.style.width = '0%';

        try {
            // Upload file
            const formData = new FormData(form);
            const uploadResponse = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const responseText = await uploadResponse.text();
            let uploadData;
            
            try {
                uploadData = JSON.parse(responseText);
            } catch (error) {
                console.error('Server response:', responseText);
                throw new Error('Server returned invalid response');
            }

            if (!uploadResponse.ok || uploadData.error) {
                throw new Error(uploadData.error || 'Upload failed');
            }

            progressBar.style.width = '50%';

            // Process the dataset
            const processResponse = await fetch(`/api/process/${uploadData.dataset_id}`, {
                method: 'POST'
            });

            const processText = await processResponse.text();
            let processData;
            
            try {
                processData = JSON.parse(processText);
            } catch (error) {
                console.error('Server response:', processText);
                throw new Error('Server returned invalid response during processing');
            }

            if (!processResponse.ok || processData.error) {
                throw new Error(processData.error || 'Processing failed');
            }

            progressBar.style.width = '100%';
            showAlert('File uploaded and processed successfully', 'success');
            
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);

        } catch (error) {
            console.error('Error:', error);
            showAlert(error.message || 'Error uploading file', 'danger');
            progressDiv.classList.add('d-none');
            progressBar.style.width = '0%';
        }
    });
}

async function loadBaseStations() {
    try {
        const response = await fetch('/api/base-stations');
        const responseText = await response.text();
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (error) {
            console.error('Server response:', responseText);
            throw new Error('Server returned invalid response');
        }

        if (!response.ok || data.error) {
            throw new Error(data.error || 'Failed to fetch base stations');
        }

        const select = document.getElementById('baseStation');
        
        if (!Array.isArray(data)) {
            throw new Error('Invalid base stations data');
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
