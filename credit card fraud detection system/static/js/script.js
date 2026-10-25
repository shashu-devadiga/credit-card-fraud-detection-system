const form = document.querySelector("form");

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    // Get form input values
    const cardNumber = document.getElementById("cc_num").value;
    const category = document.getElementById("category").value;
    const amount = document.getElementById("amt").value;
    const gender = document.getElementById("gender").value;
    const state = document.getElementById("state").value;
    const zip = document.getElementById("zip").value;
    const customerLatitude = document.getElementById("lat").value;
    const customerLongitude = document.getElementById("long").value;
    const cityPopulation = document.getElementById("city_pop").value;
    const merchantLatitude = document.getElementById("merch_lat").value;
    const merchantLongitude = document.getElementById("merch_long").value;
    const transactionDateTime = document.getElementById(
        "trans_date_trans_time"
    ).value;

    // Prepare transaction data
    const transactionData = {
        cc_num: Number(cardNumber),
        category: category,
        amt: Number(amount),
        gender: gender,
        state: state,
        zip: Number(zip),
        lat: Number(customerLatitude),
        long: Number(customerLongitude),
        city_pop: Number(cityPopulation),
        merch_lat: Number(merchantLatitude),
        merch_long: Number(merchantLongitude),
        trans_date_trans_time: transactionDateTime
    };

    // Get result display elements
    const resultIcon = document.getElementById("result-icon");
    const resultText = document.getElementById("result-text");
    const submitButton = form.querySelector('button[type="submit"]');

    // Display loading status
    resultIcon.textContent = "⏳";
    resultText.textContent = "Analyzing transaction...";

    if (submitButton) {
        submitButton.disabled = true;
    }

    try {
        // Send the request to the deployed Flask application.
        // Relative URL works locally and on Render.
        const response = await fetch("/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(transactionData)
        });

        // Read the server response
        const result = await response.json();

        // Handle unsuccessful responses
        if (!response.ok) {
            throw new Error(
                result.error || "Unable to predict this transaction."
            );
        }

        // Display prediction
        resultIcon.textContent = result.prediction === 1 ? "🚨" : "✅";

        resultText.textContent =
            result.result ||
            (result.prediction === 1
                ? "Fraudulent Transaction Detected!"
                : "Legitimate Transaction");

    } catch (error) {
        console.error("Prediction error:", error);

        resultIcon.textContent = "❌";

        resultText.textContent =
            error.message === "Failed to fetch"
                ? "Unable to connect to the prediction server. Please check your internet connection and try again."
                : error.message || "Something went wrong. Please try again.";

    } finally {
        if (submitButton) {
            submitButton.disabled = false;
        }
    }
});
