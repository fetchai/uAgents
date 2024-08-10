from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import joblib
import pandas as pd
import traceback

app = Flask(__name__)
CORS(app)

model_path = '/Users/prathmesh/Downloads/hackathon/sales_prediction_updated 2/models/sales_prediction_model.pkl'
model = joblib.load(model_path)

expected_features = ['QUANTITYORDERED', 'PRICEEACH', 'MSRP']

def preprocess_input_data(df):
    df['YEAR_ID'] = pd.to_numeric(df['YEAR_ID'], errors='coerce')
    df['MONTH_ID'] = pd.to_numeric(df['MONTH_ID'], errors='coerce')

    # Corrected line for zfill
    df['ORDERDATE'] = pd.to_datetime(df['YEAR_ID'].astype(int).astype(str) + '-' + df['MONTH_ID'].astype(int).astype(str).str.zfill(2) + '-01', errors='coerce')

    df['day_of_week'] = df['ORDERDATE'].dt.dayofweek
    df['day_of_month'] = df['ORDERDATE'].dt.day
    df['week_of_year'] = df['ORDERDATE'].dt.isocalendar().week
    df['is_weekend'] = (df['ORDERDATE'].dt.dayofweek >= 5).astype(int)
    
    df = df.reindex(columns=expected_features, fill_value=0)
    return df

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
            data = preprocess_input_data(data)
            predictions = model.predict(data)

            # Pair predictions with original data for display
            results = [{'Original Data': row._asdict(), 'Sales Prediction': pred} for row, pred in zip(data.itertuples(index=False), predictions)]
            
            return jsonify(results)

        except Exception as e:  
            # Log the traceback to see the full error
            print(traceback.format_exc())
            return jsonify({'error': 'Error processing file', 'details': str(e)}), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file:
            try:
                data = pd.read_csv(file, encoding='ISO-8859-1')
                data = preprocess_input_data(data)
                predictions = model.predict(data)

                session['predictions'] = predictions.tolist()

                return jsonify({'success': True})

            except Exception as e:  
                return jsonify({'error': 'Error processing file', 'details': str(e)}), 500

    return render_template('index.html', predictions=session.get('predictions', None))

if __name__ == '__main__':
    app.run(debug=True)