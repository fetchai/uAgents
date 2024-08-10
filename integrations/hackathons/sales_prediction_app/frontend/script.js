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
        const response = await fetch('http://127.0.0.1:5000/upload', {
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

        const predictionsTable = document.getElementById('predictions-table');
        predictionsTable.innerHTML = ''; // Clear previous predictions

        data.forEach(item => {
            const row = document.createElement('tr');
            
            const msrpCell = document.createElement('td');
            msrpCell.textContent = item['Original Data'].MSRP;
            row.appendChild(msrpCell);

            const priceEachCell = document.createElement('td');
            priceEachCell.textContent = item['Original Data'].PRICEEACH;
            row.appendChild(priceEachCell);

            const quantityOrderedCell = document.createElement('td');
            quantityOrderedCell.textContent = item['Original Data'].QUANTITYORDERED;
            row.appendChild(quantityOrderedCell);

            const predictedSalesCell = document.createElement('td');
            predictedSalesCell.textContent = item['Sales Prediction'].toFixed(2);
            row.appendChild(predictedSalesCell);

            predictionsTable.appendChild(row);
        });

    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while processing your request.');
    }
});
