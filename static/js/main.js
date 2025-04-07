document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('file-input');
    const status = document.getElementById('upload-status');
    const submitButton = e.target.querySelector('button[type="submit"]');
    
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
            status.textContent = data.error || 'Upload failed';
        }
    } catch (error) {
        status.className = 'error';
        status.textContent = 'Error uploading file';
    } finally {
        submitButton.disabled = false;
    }
});

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
        loadingSpinner.style.display = 'flex';
        responseContainer.style.display = 'none';

        const response = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                query: `Analyze the software license in: ${queryInput.value}`
            })
        });
        const data = await response.json();
        
        loadingSpinner.style.display = 'none';
        responseContainer.style.display = 'block';
        
        if (response.ok) {
            const formattedResponse = data.response.replace(/\\n/g, '\n');
            responseContainer.innerHTML = `<pre>${formattedResponse}</pre>`;
            responseContainer.className = 'success fade-in';
        } else {
            responseContainer.textContent = data.error || 'Query failed';
            responseContainer.className = 'error fade-in';
        }
    } catch (error) {
        loadingSpinner.style.display = 'none';
        responseContainer.style.display = 'block';
        responseContainer.textContent = 'Error processing query';
        responseContainer.className = 'error fade-in';
    } finally {
        submitButton.disabled = false;
    }
});