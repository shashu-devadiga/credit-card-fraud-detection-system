from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import joblib

app = Flask(__name__)
CORS(app)

# Load the new trained model and preprocessing files
model = joblib.load("models/credit_card_model.pkl")
scaler = joblib.load("models/scaler.pkl")
feature_columns = joblib.load("models/feature_columns.pkl")
encoders = joblib.load("models/encoders.pkl")

print("Credit card fraud detection model loaded successfully!")
print("Scaler loaded successfully!")
print("Feature columns loaded successfully!")
print("Encoders loaded successfully!")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():

    try:
        # Receive transaction details from the frontend
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "error": "Please provide valid JSON transaction data."
            }), 400

        # Required input fields
        required_fields = [
            "cc_num",
            "category",
            "amt",
            "gender",
            "state",
            "zip",
            "lat",
            "long",
            "city_pop",
            "merch_lat",
            "merch_long",
            "trans_date_trans_time"
        ]

        missing_fields = [
            field for field in required_fields
            if field not in data or data[field] is None
            or str(data[field]).strip() == ""
        ]

        if missing_fields:
            return jsonify({
                "error": "Missing required fields.",
                "missing_fields": missing_fields
            }), 400

        # Create a DataFrame from the submitted transaction
        input_data = pd.DataFrame([data])

        # Encode categorical features
        categorical_columns = [
            "category",
            "gender",
            "state"
        ]

        for column in categorical_columns:

            if column not in encoders:
                return jsonify({
                    "error": f"Encoder for '{column}' was not found."
                }), 500

            encoder = encoders[column]
            value = str(input_data.at[0, column])

            # Check whether the category was seen during training
            if value not in encoder.classes_:
                return jsonify({
                    "error": (
                        f"Unknown value '{value}' for '{column}'. "
                        "Please provide a value present in the "
                        "training dataset."
                    )
                }), 400

            input_data[column] = encoder.transform(
                input_data[column].astype(str)
            )

        # Convert transaction date/time
        transaction_datetime = pd.to_datetime(
            input_data["trans_date_trans_time"],
            errors="raise"
        )

        # Create the same date features used during training
        input_data["transaction_hour"] = transaction_datetime.dt.hour
        input_data["transaction_day"] = transaction_datetime.dt.day
        input_data["transaction_month"] = transaction_datetime.dt.month
        input_data["transaction_dayofweek"] = (
            transaction_datetime.dt.dayofweek
        )

        # Remove the original datetime column
        input_data = input_data.drop(
            columns=["trans_date_trans_time"]
        )

        # Arrange features in the exact training order
        input_data = input_data[feature_columns]

        # Convert model inputs to numeric values
        input_data = input_data.apply(
            pd.to_numeric,
            errors="raise"
        )

        # Scale the input features
        input_data = scaler.transform(input_data)

        # Predict the transaction
        prediction = int(model.predict(input_data)[0])

        if prediction == 1:
            result = "Fraudulent Transaction"
        else:
            result = "Legitimate Transaction"

        return jsonify({
            "prediction": prediction,
            "result": result
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 400


if __name__ == "__main__":
    app.run(debug=True)