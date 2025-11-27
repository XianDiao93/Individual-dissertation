const API_BASE_URL = "http://127.0.0.1:8000";

const responseBody = document.getElementById("responseBody");
const btnSubmit = document.getElementById("btnSubmit");
const btnClear = document.getElementById("btnClear");

const tabs = document.querySelectorAll(".tab-btn");
let currentMode = "communication";

// Mode switching
tabs.forEach(tab => {
    tab.addEventListener("click", () => {
        const mode = tab.dataset.mode;

        if (mode === currentMode) return;

        currentMode = mode;
        tabs.forEach(t => t.classList.toggle("active", t === tab));

        document.getElementById("mode-communication").style.display = mode === "communication" ? "block" : "none";
        document.getElementById("mode-document").style.display = mode === "document" ? "block" : "none";
        document.getElementById("mode-risk").style.display = mode === "risk" ? "block" : "none";

        responseBody.textContent = "The AI response will appear here.";
    });
});

// Backend call
async function callBackend() {
    btnSubmit.disabled = true;
    btnSubmit.textContent = "Processing...";

    try {
        let endpoint = "";
        let payload = {};

        if (currentMode === "communication") {
            alert("function have not been implemented yet");
            return;
            endpoint = "/api/chat";
            payload = {
                message: document.getElementById("commMessage").value,
                language: document.getElementById("commLanguage").value,
                region: document.getElementById("commRegion").value,
                tone: document.getElementById("commTone").value,
            };
        }

        else if (currentMode === "document") {
            alert("function have not been implemented yet");
            return;
            endpoint = "/api/document";
            payload = {
                document_type: document.getElementById("docType").value,
                currency: document.getElementById("docCurrency").value,
                seller_name: document.getElementById("docSeller").value,
                buyer_name: document.getElementById("docBuyer").value,
                product: document.getElementById("docProduct").value,
                quantity: Number(document.getElementById("docQuantity").value),
                unit_price: Number(document.getElementById("docUnitPrice").value),
                incoterm: document.getElementById("docIncoterm").value,
                payment_term: document.getElementById("docPaymentTerm").value,
                extra_notes: document.getElementById("docExtra").value,
            };
        }

        else if (currentMode === "risk") {
            alert("function have not been implemented yet");
            return;
            endpoint = "/api/risk";
            payload = {
                message: document.getElementById("riskMessage").value,
                country: document.getElementById("riskCountry").value,
                transaction_type: document.getElementById("riskTransactionType").value,
            };
        }

    const res = await fetch(API_BASE_URL + endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    const data = await res.json();
    responseBody.textContent =
        data.reply ||
        data.document_text ||
        JSON.stringify(data, null, 2);

    } catch (err) {
        responseBody.textContent = "Error: " + err.message;
    } finally {
        btnSubmit.disabled = false;
        btnSubmit.textContent = "Send Request";
    }
}

btnSubmit.addEventListener("click", callBackend);

// Clear inputs
btnClear.addEventListener("click", () => {
    if (currentMode === "communication") {
        document.getElementById("commMessage").value = "";
    }
    if (currentMode === "document") {
        [
        "docSeller",
        "docBuyer",
        "docProduct",
        "docQuantity",
        "docUnitPrice",
        "docIncoterm",
        "docPaymentTerm",
        "docExtra"
        ].forEach(id => document.getElementById(id).value = "");
    }
    if (currentMode === "risk") {
        document.getElementById("riskMessage").value = "";
        document.getElementById("riskCountry").value = "";
    }
});