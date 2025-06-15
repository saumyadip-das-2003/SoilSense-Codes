import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import joblib

# 1. Load data
df = pd.read_csv('Crop_recommendation.csv')

# 2. Select input features and target outputs
features = ['temperature', 'humidity', 'rainfall']
targets = ['N', 'P', 'K', 'ph']

X = df[features]
y = df[targets]

# 3. Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 4. Train the model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 5. Evaluate the model
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred, multioutput='raw_values')
print("Mean Squared Error (MSE) for [N, P, K, ph]:", mse)

# 6. Save the model
joblib.dump(model, 'npk_ph_predictor.pkl')
print("Model saved as npk_ph_predictor.pkl")

# 7. Example: Predict new values
# Replace these numbers with your real sensor readings
example_input = [[26.0, 80.0, 100.0]]  # [temperature, humidity, rainfall]
predicted = model.predict(example_input)
print(f"Predicted [N, P, K, ph]: {predicted[0]}")
