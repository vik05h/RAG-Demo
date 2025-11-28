// --- UPLOAD HANDLING (Looks good, but added a check) ---
document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('file-input');
    const status = document.getElementById('upload-status');
    const submitButton = e.target.querySelector('button[type="submit"]');

    if (fileInput.files.length === 0) {
        status.textContent = 'Please select a file first.';
        status.className = 'error';
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        status.textContent = 'Uploading...';
        status.className = 'loading';
        submitButton.disabled = true;

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (response.ok) {
            status.className = 'success';
            status.textContent = 'File uploaded successfully!';
        } else {
            status.className = 'error';
            status.textContent = data.detail || data.error || 'Upload failed';
        }
    } catch (error) {
        status.className = 'error';
        status.textContent = 'Error uploading file';
    } finally {
        submitButton.disabled = false;
    }
});

// --- QUERY HANDLING (Fixed for Versatility & Markdown) ---
document.getElementById('submit-query').addEventListener('click', async () => {
    const queryInput = document.getElementById('query-input');
    const responseContainer = document.getElementById('response-container');
    const submitButton = document.getElementById('submit-query');
    const loadingSpinner = document.getElementById('loading-spinner');

    if (!queryInput.value.trim()) {
        responseContainer.textContent = 'Please enter a query';
        responseContainer.className = 'error';
        return;
    }

    try {
        submitButton.disabled = true;
        // Show loading, hide previous response
        if (loadingSpinner) loadingSpinner.style.display = 'flex';
        responseContainer.style.display = 'none';

        const response = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: queryInput.value
            })
        });
        const data = await response.json();

        if (loadingSpinner) loadingSpinner.style.display = 'none';
        responseContainer.style.display = 'block';

        if (response.ok) {
            responseContainer.innerHTML = marked.parse(data.response);
            responseContainer.className = 'success fade-in';
        } else {
            responseContainer.textContent = data.detail || data.error || 'Query failed';
            responseContainer.className = 'error fade-in';
        }
    } catch (error) {
        if (loadingSpinner) loadingSpinner.style.display = 'none';
        responseContainer.style.display = 'block';
        responseContainer.textContent = 'Error processing query';
        responseContainer.className = 'error fade-in';
        console.error(error);
    } finally {
        submitButton.disabled = false;
    }
});