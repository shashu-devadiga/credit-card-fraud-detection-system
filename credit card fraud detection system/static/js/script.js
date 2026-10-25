const form = document.querySelector("form");

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    // Get transaction details from the existing HTML form
    const cardNumber = document.querySelector(
        'input[name="card_number"]'
    ).value.trim();

    const amount = document.querySelector(
        'input[name="amount"]'
    ).value.trim();

    const category = document.querySelector(
        'select[name="category"]'
    ).value;

    const gender = document.querySelector(
        'select[name="Gender"]'
    ).value;

    const state = document.querySelector(
        'select[name="State"]'
    ).value;

    const zip = document.querySelector(
        'input[name="zip"]'
    ).value.trim();

    const cityPopulation = document.querySelector(
        'input[name="city_population"]'
    ).value.trim();

    const customerLatitude = document.querySelector(
        'input[name="customer_latitude"]'
    ).value.trim();

    const customerLongitude = document.querySelector(
        'input[name="customer_longitude"]'
    ).value.trim();

    const merchantLatitude = document.querySelector(
        'input[name="merchant_latitude"]'
    ).value.trim();

    const merchantLongitude = document.querySelector(
        'input[name="merchant_longitude"]'
    ).value.trim();

    const transactionDateTime = document.querySelector(
        'input[name="transaction_datetime"]'
    ).value;

    // Validate required fields
    if (
        !cardNumber ||
        !amount ||
        !category ||
        !gender ||
        !state ||
        !zip ||
        !cityPopulation ||
        !customerLatitude ||
        !customerLongitude ||
        !merchantLatitude ||
        !merchantLongitude ||
        !transactionDateTime
    ) {
        alert("Please fill in all transaction details before checking.");
        return;
    }

    // Validate card number
    if (!/^\d{1,19}$/.test(cardNumber)) {
        alert("Please enter a valid card number.");
        return;
    }

    // Validate numeric inputs
    const numericValues = [
        amount,
        zip,
        cityPopulation,
        customerLatitude,
        customerLongitude,
        merchantLatitude,
        merchantLongitude
    ];

    if (!numericValues.every(value => Number.isFinite(Number(value)))) {
        alert("Please enter valid numeric transaction details.");
        return;
    }

    if (Number(amount) < 0 || Number(cityPopulation) < 0) {
        alert("Amount and city population cannot be negative.");
        return;
    }

    if (!/^\d+$/.test(zip)) {
        alert("Please enter a valid ZIP code.");
        return;
    }

    // Prepare data using the NEW model's expected feature names
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

    // Show a temporary status while waiting for prediction
    const resultIcon = document.querySelector(".result-icon");
    const resultText = document.querySelector(".result-text");
    const submitButton = form.querySelector(
        'button[type="submit"]'
    );

    resultIcon.textContent = "⏳";
    resultText.textContent = "Checking transaction...";
    submitButton.disabled = true;

    try {
        // Connect to the Flask prediction API
        const response = await fetch(
            "http://127.0.0.1:5000/predict",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(transactionData)
            }
        );

        const result = await response.json();

        // Handle errors returned by Flask
        if (!response.ok) {
            throw new Error(
                result.error || "Unable to predict this transaction."
            );
        }

        // Display the model's prediction
        if (result.prediction === 1) {
            resultIcon.textContent = "⚠️";
            resultText.innerHTML = `
                <strong>Fraudulent Transaction</strong>
                <br>
                This transaction has been identified as potentially fraudulent.
            `;
        } else if (result.prediction === 0) {
            resultIcon.textContent = "✓";
            resultText.innerHTML = `
                <strong>Legitimate Transaction</strong>
                <br>
                This transaction appears to be legitimate.
            `;
        } else {
            throw new Error("The server returned an unexpected prediction.");
        }

        console.log("Prediction:", result);

    } catch (error) {
        resultIcon.textContent = "❌";
        resultText.textContent = error.message;

        console.error("Prediction error:", error);

    } finally {
        submitButton.disabled = false;
    }
});