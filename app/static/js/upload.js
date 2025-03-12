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
            // Log form data for debugging
            const formData = new FormData(form);
            console.log('Form data:', {
                file: formData.get('file')?.name,
                baseStation: formData.get('base_station_id')
            });

            // Upload file
            console.log('Sending upload request...');
            const uploadResponse = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json'
                }
            });

            console.log('Upload response status:', uploadResponse.status);
            console.log('Upload response headers:', Object.fromEntries(uploadResponse.headers.entries()));

            // Get raw response text first
            const responseText = await uploadResponse.text();
            console.log('Raw upload response:', responseText);

            // Try to parse as JSON
            let uploadData;
            try {
                uploadData = JSON.parse(responseText);
                console.log('Parsed upload response:', uploadData);
            } catch (error) {
                console.error('Failed to parse upload response:', error);
                throw new Error('Server returned invalid JSON. Check server logs.');
            }

            // Check for errors
            if (!uploadResponse.ok || !uploadData.success) {
                throw new Error(uploadData.error || 'Upload failed');
            }

            // Update progress
            progressBar.style.width = '50%';
            statusDiv.textContent = 'Processing...';

            // Process the dataset
            console.log('Starting processing...');
            const processResponse = await fetch(`/api/process/${uploadData.dataset_id}`, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json'
                }
            });

            console.log('Process response status:', processResponse.status);
            console.log('Process response headers:', Object.fromEntries(processResponse.headers.entries()));

            // Get raw process response text
            const processText = await processResponse.text();
            console.log('Raw process response:', processText);

            // Try to parse as JSON
            let processData;
            try {
                processData = JSON.parse(processText);
                console.log('Parsed process response:', processData);
            } catch (error) {
                console.error('Failed to parse process response:', error);
                throw new Error('Server returned invalid JSON during processing');
            }

            // Check for processing errors
            if (!processResponse.ok || !processData.success) {
                throw new Error(processData.error || 'Processing failed');
            }

            // Update UI for success
            progressBar.style.width = '100%';
            statusDiv.textContent = 'Success!';
            showAlert('File uploaded and processed successfully', 'success');

            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);

        } catch (error) {
            console.error('Error during upload/process:', error);
            progressDiv.classList.add('d-none');
            showAlert(error.message || 'Error uploading file', 'danger');
        }
    });
});

async function loadBaseStations() {
    try {
        console.log('Fetching base stations...');
        const response = await fetch('/api/base-stations', {
            headers: {
                'Accept': 'application/json'
            }
        });

        console.log('Base stations response status:', response.status);
        console.log('Base stations headers:', Object.fromEntries(response.headers.entries()));

        const responseText = await response.text();
        console.log('Raw base stations response:', responseText);

        let data;
        try {
            data = JSON.parse(responseText);
            console.log('Parsed base stations response:', data);
        } catch (error) {
            console.error('Failed to parse base stations response:', error);
            throw new Error('Server returned invalid JSON');
        }

        if (!response.ok || (data.success === false)) {
            throw new Error(data.error || 'Failed to fetch base stations');
        }

        const select = document.getElementById('baseStation');
        
        if (!Array.isArray(data)) {
            console.error('Invalid base stations data format:', data);
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
        console.log('Base stations loaded successfully');

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
    console.log(`Alert shown: ${type} - ${message}`);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}
