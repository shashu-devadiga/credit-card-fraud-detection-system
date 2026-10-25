const form = document.querySelector("form");

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    // Read values using the names defined in index.html
    const getValue = (name) =>
        form.querySelector(`[name="${name}"]`).value;

    const cardNumber = getValue("card_number");
    const amount = getValue("amount");
    const category = getValue("category");
    const gender = getValue("Gender");
    const state = getValue("State");
    const zip = getValue("zip");
    const cityPopulation = getValue("city_population");
    const customerLatitude = getValue("customer_latitude");
    const customerLongitude = getValue("customer_longitude");
    const merchantLatitude = getValue("merchant_latitude");
    const merchantLongitude = getValue("merchant_longitude");
    const transactionDateTime = getValue("transaction_datetime");

    // Prepare data for Flask
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

    // Find result elements using the classes in index.html
    const resultIcon = document.querySelector(".result-icon");
    const resultText = document.querySelector(".result-text");
    const submitButton = form.querySelector('button[type="submit"]');

    resultIcon.textContent = "⏳";
    resultText.textContent = "Analyzing transaction...";

    submitButton.disabled = true;

    try {
        // Send the prediction request to the same deployed website
        const response = await fetch("/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(transactionData)
        });

        // Safely read the server response
        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.error || "Prediction failed. Please check the transaction details."
            );
        }

        // Display the prediction
        if (Number(result.prediction) === 1) {
            resultIcon.textContent = "🚨";
            resultText.textContent =
                result.result || "Fraudulent Transaction Detected!";
        } else {
            resultIcon.textContent = "✅";
            resultText.textContent =
                result.result || "Legitimate Transaction";
        }

    } catch (error) {
        console.error("Prediction error:", error);

        resultIcon.textContent = "❌";
        resultText.textContent =
            error.message || "Unable to predict this transaction.";

    } finally {
        submitButton.disabled = false;
    }
});
