import os
import pandas as pd
import joblib
import gdown

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS


# --------------------------------------------------
# Step 1: Initialize Flask application
# --------------------------------------------------

app = Flask(__name__)
CORS(app)


# --------------------------------------------------
# Step 2: Define project and model paths
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "credit_card_model.pkl"
)

SCALER_PATH = os.path.join(
    MODEL_DIR,
    "scaler.pkl"
)

FEATURE_COLUMNS_PATH = os.path.join(
    MODEL_DIR,
    "feature_columns.pkl"
)

ENCODERS_PATH = os.path.join(
    MODEL_DIR,
    "encoders.pkl"
)


# --------------------------------------------------
# Step 3: Download model from Google Drive
# --------------------------------------------------

GOOGLE_DRIVE_FILE_ID = "1iXG1JPh8ZYGGEif3QweMn-exUIhUAmJ6"


def download_model():

    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 0:
        print("Model file already exists.")
        return

    print("Downloading credit card fraud detection model...")

    downloaded_file = gdown.download(
        id=GOOGLE_DRIVE_FILE_ID,
        output=MODEL_PATH,
        quiet=False,
        fuzzy=True
    )

    if (
        downloaded_file is None
        or not os.path.exists(MODEL_PATH)
        or os.path.getsize(MODEL_PATH) == 0
    ):
        raise RuntimeError(
            "Model download failed. Check the Google Drive sharing "
            "permission and file ID."
        )

    print("Model downloaded successfully.")


download_model()


# --------------------------------------------------
# Step 4: Load model and preprocessing files
# --------------------------------------------------

model = joblib.load(MODEL_PATH)

scaler = joblib.load(SCALER_PATH)

feature_columns = joblib.load(
    FEATURE_COLUMNS_PATH
)

encoders = joblib.load(
    ENCODERS_PATH
)

print("Credit card fraud detection model loaded successfully!")
print("Scaler loaded successfully!")
print("Feature columns loaded successfully!")
print("Encoders loaded successfully!")


# --------------------------------------------------
# Step 5: Home page
# --------------------------------------------------

@app.route("/")
def home():

    return render_template("index.html")


# --------------------------------------------------
# Step 6: Fraud prediction
# --------------------------------------------------

@app.route("/predict", methods=["POST"])
def predict():

    try:

        # Receive transaction details from frontend
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

        # Check missing fields
        missing_fields = [
            field
            for field in required_fields
            if (
                field not in data
                or data[field] is None
                or str(data[field]).strip() == ""
            )
        ]

        if missing_fields:

            return jsonify({
                "error": "Missing required fields.",
                "missing_fields": missing_fields
            }), 400

        # Create DataFrame
        input_data = pd.DataFrame([data])

        # ------------------------------------------
        # Step 6A: Encode categorical features
        # ------------------------------------------

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

            # Check unseen categorical values
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

        # ------------------------------------------
        # Step 6B: Extract transaction date features
        # ------------------------------------------

        transaction_datetime = pd.to_datetime(
            input_data["trans_date_trans_time"],
            errors="raise"
        )

        input_data["transaction_hour"] = (
            transaction_datetime.dt.hour
        )

        input_data["transaction_day"] = (
            transaction_datetime.dt.day
        )

        input_data["transaction_month"] = (
            transaction_datetime.dt.month
        )

        input_data["transaction_dayofweek"] = (
            transaction_datetime.dt.dayofweek
        )

        # Remove original datetime column
        input_data.drop(
            columns=["trans_date_trans_time"],
            inplace=True
        )

        # ------------------------------------------
        # Step 6C: Arrange features in training order
        # ------------------------------------------

        input_data = input_data[feature_columns]

        # Convert features to numeric values
        input_data = input_data.apply(
            pd.to_numeric,
            errors="raise"
        )

        # ------------------------------------------
        # Step 6D: Scale input features
        # ------------------------------------------

        input_scaled = scaler.transform(input_data)

        # ------------------------------------------
        # Step 6E: Predict transaction
        # ------------------------------------------

        prediction = int(
            model.predict(input_scaled)[0]
        )

        if prediction == 1:

            result = "Fraudulent Transaction"

        else:

            result = "Legitimate Transaction"

        return jsonify({
            "prediction": prediction,
            "result": result
        })

    except Exception as e:

        app.logger.exception("Prediction failed")

        return jsonify({
            "error": str(e)
        }), 400

if __name__ == "__main__":

    app.run(debug=False)
