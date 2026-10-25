import os
import pandas as pd
import joblib
import gdown

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "credit_card_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
FEATURE_COLUMNS_PATH = os.path.join(MODEL_DIR, "feature_columns.pkl")
ENCODERS_PATH = os.path.join(MODEL_DIR, "encoders.pkl")

GOOGLE_DRIVE_FILE_ID = "1iXG1JPh8ZYGGEif3QweMn-exUIhUAmJ6"


def download_model():
    if os.path.isfile(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 0:
        print("Model file already exists.")
        return

    print("Downloading credit card fraud detection model...")

    if os.path.exists(MODEL_PATH):
        os.remove(MODEL_PATH)

    downloaded_file = gdown.download(
        id=GOOGLE_DRIVE_FILE_ID,
        output=MODEL_PATH,
        quiet=False,
        fuzzy=True
    )

    if (
        not downloaded_file
        or not os.path.isfile(MODEL_PATH)
        or os.path.getsize(MODEL_PATH) == 0
    ):
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)

        raise RuntimeError(
            "Model download failed. Check Google Drive sharing permissions, "
            "the file ID, and Google Drive download limits."
        )

    print("Model downloaded successfully.")


download_model()

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
feature_columns = joblib.load(FEATURE_COLUMNS_PATH)
encoders = joblib.load(ENCODERS_PATH)

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
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "error": "Please provide valid JSON transaction data."
            }), 400

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
            if field not in data
            or data[field] is None
            or str(data[field]).strip() == ""
        ]

        if missing_fields:
            return jsonify({
                "error": "Missing required fields.",
                "missing_fields": missing_fields
            }), 400

        input_data = pd.DataFrame([data])

        categorical_columns = ["category", "gender", "state"]

        for column in categorical_columns:
            if column not in encoders:
                app.logger.error("Encoder for '%s' was not found.", column)
                return jsonify({
                    "error": f"Encoder for '{column}' was not found."
                }), 500

            encoder = encoders[column]
            value = str(input_data.at[0, column])

            if value not in encoder.classes_:
                return jsonify({
                    "error": (
                        f"Unknown value '{value}' for '{column}'. "
                        "Please provide a value present in the training dataset."
                    )
                }), 400

            input_data[column] = encoder.transform(
                input_data[column].astype(str)
            )

        transaction_datetime = pd.to_datetime(
            input_data["trans_date_trans_time"],
            errors="raise"
        )

        input_data["transaction_hour"] = transaction_datetime.dt.hour
        input_data["transaction_day"] = transaction_datetime.dt.day
        input_data["transaction_month"] = transaction_datetime.dt.month
        input_data["transaction_dayofweek"] = (
            transaction_datetime.dt.dayofweek
        )

        input_data.drop(
            columns=["trans_date_trans_time"],
            inplace=True
        )

        input_data = input_data[feature_columns]
        input_data = input_data.apply(pd.to_numeric, errors="raise")

        input_scaled = scaler.transform(input_data)
        prediction = int(model.predict(input_scaled)[0])

        result = (
            "Fraudulent Transaction"
            if prediction == 1
            else "Legitimate Transaction"
        )

        return jsonify({
            "prediction": prediction,
            "result": result
        })

    except Exception:
        app.logger.exception("Prediction failed")
        return jsonify({
            "error": "Prediction failed. Please check the submitted transaction data."
        }), 400


if __name__ == "__main__":
    app.run(debug=False)
