import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import joblib

# Load data
data = pd.read_csv('../data/sales_data.csv')

# Data preprocessing
data = data.dropna()

# Feature selection
X = data[['feature1', 'feature2', 'feature3']]
y = data['sales']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = LinearRegression()
model.fit(X_train, y_train)

# Save the model
joblib.dump(model, 'sales_model.pkl')
