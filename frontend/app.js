// API Configuration
const API_CONFIG = {
    apiKey: 'tKljgtuOpJ9JwocIK6iypS5f5vvpTgI1w5fk8Zfj',
    endpoint: 'https://awj7t30s2g.execute-api.us-east-1.amazonaws.com/prod',
    region: 'us-east-1'
};

// Initialize API client
let apiClient = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeAPI();
    setupEventListeners();
});

function initializeAPI() {
    // Check if API Gateway SDK is loaded (optional)
    if (typeof apigClientFactory !== 'undefined') {
        apiClient = apigClientFactory.newClient({
            apiKey: API_CONFIG.apiKey
        });
    }
    // Falls back to direct fetch calls if SDK not loaded
}

function setupEventListeners() {
    const searchForm = document.getElementById('searchForm');
    const uploadForm = document.getElementById('uploadForm');

    searchForm.addEventListener('submit', handleSearch);
    uploadForm.addEventListener('submit', handleUpload);
}

async function handleSearch(event) {
    event.preventDefault();
    
    const query = document.getElementById('searchQuery').value.trim();
    if (!query) {
        showError('Please enter a search query');
        return;
    }

    const resultsContainer = document.getElementById('resultsContainer');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessage = document.getElementById('errorMessage');

    // Clear previous results
    resultsContainer.innerHTML = '';
    errorMessage.style.display = 'none';
    loadingIndicator.style.display = 'block';

    try {
        let results;
        
        if (apiClient) {
            // Use API Gateway SDK
            const response = await apiClient.searchGet({
                q: query
            });
            results = response.data;
        } else {
            // Fallback: Direct API call
            const response = await fetch(`${API_CONFIG.endpoint}/search?q=${encodeURIComponent(query)}`, {
                method: 'GET',
                headers: {
                    'x-api-key': API_CONFIG.apiKey
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            results = await response.json();
        }

        loadingIndicator.style.display = 'none';
        displayResults(results);
        
    } catch (error) {
        console.error('Search error:', error);
        loadingIndicator.style.display = 'none';
        showError('Error searching photos: ' + error.message);
    }
}

async function handleUpload(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('photoFile');
    const customLabelsInput = document.getElementById('customLabels');
    const file = fileInput.files[0];

    if (!file) {
        showError('Please select a photo to upload');
        return;
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
        showError('Please select an image file');
        return;
    }

    const customLabels = customLabelsInput.value.trim();
    const button = event.target.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = 'Uploading...';

    try {
        // Read file as base64 or use FormData
        const formData = new FormData();
        formData.append('file', file);

        let uploadUrl = `${API_CONFIG.endpoint}/photos/${encodeURIComponent(file.name)}`;
        const headers = {
            'x-api-key': API_CONFIG.apiKey,
            'Content-Type': file.type || 'application/octet-stream'
        };

        // Add custom labels header if provided
        if (customLabels) {
            headers['x-amz-meta-customlabels'] = customLabels;
        }

        // Direct API call to upload file
        const response = await fetch(uploadUrl, {
            method: 'PUT',
            headers: headers,
            body: file
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Upload failed: ${response.status} ${response.statusText} - ${errorText}`);
        }

        // Reset form
        fileInput.value = '';
        customLabelsInput.value = '';
        button.disabled = false;
        button.textContent = 'Upload Photo';
        
        showSuccess('Photo uploaded successfully! It will be indexed shortly.');
        
    } catch (error) {
        console.error('Upload error:', error);
        button.disabled = false;
        button.textContent = 'Upload Photo';
        showError('Error uploading photo: ' + error.message);
    }
}

function displayResults(results) {
    const resultsContainer = document.getElementById('resultsContainer');
    
    if (!results || results.length === 0) {
        resultsContainer.innerHTML = '<div class="empty-results">No photos found matching your search.</div>';
        return;
    }

    resultsContainer.innerHTML = '';
    
    results.forEach(photo => {
        const photoCard = createPhotoCard(photo);
        resultsContainer.appendChild(photoCard);
    });
}

function createPhotoCard(photo) {
    const card = document.createElement('div');
    card.className = 'photo-card';
    
    // Create image URL from S3 bucket and key
    const imageUrl = `https://${photo.bucket}.s3.amazonaws.com/${photo.objectKey}`;
    
    card.innerHTML = `
        <img src="${imageUrl}" alt="${photo.objectKey}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'200\' height=\'200\'%3E%3Crect width=\'200\' height=\'200\' fill=\'%23ddd\'/%3E%3Ctext x=\'50%25\' y=\'50%25\' text-anchor=\'middle\' dy=\'.3em\' fill=\'%23999\'%3EImage not available%3C/text%3E%3C/svg%3E'">
        <div class="photo-info">
            <div class="photo-name">${escapeHtml(photo.objectKey)}</div>
            <div class="photo-date">Uploaded: ${formatDate(photo.createdTimestamp)}</div>
            <div class="photo-labels">
                ${photo.labels && photo.labels.length > 0 
                    ? photo.labels.map(label => `<span class="label-tag">${escapeHtml(label)}</span>`).join('')
                    : '<span class="label-tag">No labels</span>'
                }
            </div>
        </div>
    `;
    
    return card;
}

function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    // Create a temporary success message
    const successDiv = document.createElement('div');
    successDiv.className = 'error';
    successDiv.style.background = '#efe';
    successDiv.style.color = '#3c3';
    successDiv.style.borderLeftColor = '#3c3';
    successDiv.textContent = message;
    
    const uploadSection = document.querySelector('.upload-section');
    uploadSection.insertBefore(successDiv, uploadSection.firstChild);
    
    setTimeout(() => {
        successDiv.remove();
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch (e) {
        return timestamp;
    }
}

// Export for configuration
window.updateAPIConfig = function(config) {
    Object.assign(API_CONFIG, config);
    initializeAPI();
};

