document.getElementById('upload-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file!');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('http://127.0.0.1:5000/upload', { // Update the URL if needed
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('Error response:', errorData);
            alert(`Error: ${errorData.error || 'An unexpected error occurred'}`);
            return;
        }

        const data = await response.json();

        // Display predictions on the page
        const predictionsList = document.getElementById('predictions');
        predictionsList.innerHTML = ''; // Clear previous predictions

        if (data.length === 0) {
            predictionsList.innerHTML = '<li>No predictions available.</li>';
        } else {
            data.forEach(item => {
                const listItem = document.createElement('li');
                listItem.textContent = `Original Data: ${item['Original Data']}, Prediction: ${item['Sales Prediction']}`;
                predictionsList.appendChild(listItem);
            });
        }

    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while processing your request.');
    }
});
