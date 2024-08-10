from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import os
from sklearn.impute import SimpleImputer

app = Flask(__name__)
CORS(app)

current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, 'models', 'sales_model.pkl')

# Debug: Print the model path
print(f"Model path: {model_path}")

if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found at path: {model_path}")
model = joblib.load(model_path)
# Initialize the imputer to fill missing values with the mean of the column
imputer = SimpleImputer(strategy='mean')
# Load model and setup imputer as before...
expected_features = ['QUANTITYORDERED']  # replace with actual feature names
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        try:
            data = pd.read_csv(file, encoding='ISO-8859-1')
            data = data.reindex(columns=expected_features, fill_value=0)
            data = pd.DataFrame(imputer.fit_transform(data), columns=expected_features)
            
            monthly_averages = []
            for i in range(6):  # Predict for the next 6 months
                monthly_data = data.copy()
                monthly_prediction = model.predict(monthly_data)
                average_sales = np.mean(monthly_prediction)
                monthly_averages.append(round(average_sales, 2))

            return jsonify(monthly_averages)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)