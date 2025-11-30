import {
  callCommunicationAPI,
  callDocumentAPI,
  callRiskAPI,
} from "./api.js";

const API_BASE_URL = "http://127.0.0.1:8000";

const responseBody = document.getElementById("responseBody");
const btnSubmit = document.getElementById("btnSubmit");
const btnClear = document.getElementById("btnClear");

const tabs = document.querySelectorAll(".tab-btn");
let currentMode = "communication";

const docTypeSelect = document.getElementById("docType");
const docTemplateGroup = document.getElementById("docTemplateGroup");
const docImageGroup = document.getElementById("docImageGroup");

if (docTypeSelect) {
  const updateDocFieldsVisibility = () => {
    const t = docTypeSelect.value;
    if (t === "sales_contract" || t === "quotation") {
      docTemplateGroup.style.display = "block";
      docImageGroup.style.display = "none";
    } else if (t === "product_manual") {
      docTemplateGroup.style.display = "none";
      docImageGroup.style.display = "block";
    } else {
      docTemplateGroup.style.display = "block";
      docImageGroup.style.display = "none";
    }
  };

  docTypeSelect.addEventListener("change", updateDocFieldsVisibility);
  updateDocFieldsVisibility(); // initialize
}


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

        // communication branch
        if (currentMode === "communication") {
            const message = document.getElementById("commMessage").value.trim();
            const language = document.getElementById("commLanguage").value;
            const region = document.getElementById("commRegion").value;
            const tone = document.getElementById("commTone").value;
            const replyForm = document.getElementById("commReplyForm").value;

            if (!message) {
                responseBody.textContent = "Please enter a message before sending.";
                return;
            }

            const data = await callCommunicationAPI({
                message,
                language,
                region,
                tone,
                replyForm,
            });

            responseBody.textContent =
                data.reply || JSON.stringify(data, null, 2);

            return;
        }

        // document branch
        else if (currentMode === "document") {
            const docType = document.getElementById("docType").value;
            const currency = document.getElementById("docCurrency").value;
            const seller = document.getElementById("docSeller").value;
            const buyer = document.getElementById("docBuyer").value;
            const product = document.getElementById("docProduct").value;
            const quantityRaw = document.getElementById("docQuantity").value;
            const unitPriceRaw = document.getElementById("docUnitPrice").value;
            const incoterm = document.getElementById("docIncoterm").value;
            const paymentTerm = document.getElementById("docPaymentTerm").value;
            const extra = document.getElementById("docExtra").value;

            const quantity = quantityRaw === "" ? 0 : Number(quantityRaw);
            const unitPrice = unitPriceRaw === "" ? 0 : Number(unitPriceRaw);

            const templateFileInput = document.getElementById("docTemplate");
            const imageFileInput = document.getElementById("docImage");

            const formData = new FormData();
            formData.append("document_type", docType);
            formData.append("currency", currency);
            formData.append("seller_name", seller);
            formData.append("buyer_name", buyer);
            formData.append("product", product);
            formData.append("quantity", quantity.toString());
            formData.append("unit_price", unitPrice.toString());
            formData.append("incoterm", incoterm);
            formData.append("payment_term", paymentTerm);
            formData.append("extra_notes", extra);

            if ((docType === "sales_contract" || docType === "quotation") && templateFileInput.files.length > 0) {
                formData.append("template_file", templateFileInput.files[0]);
            }

            if (docType === "product_manual" && imageFileInput.files.length > 0) {
                formData.append("product_image", imageFileInput.files[0]);
            }

            try {
                const res = await fetch(API_BASE_URL + "/api/document/pdf", {
                    method: "POST",
                    body: formData,          // ❗❗ 不要手动写 Content-Type
                });

                if (!res.ok) {
                    const detail = await res.text();
                    throw new Error(`Request failed with status ${res.status}: ${detail}`);
                }

                const desc = res.headers.get("X-Doc-Description") || "Document PDF has been generated.";

                const blob = await res.blob();
                const url = URL.createObjectURL(blob);

                const a = document.createElement("a");
                a.href = url;
                a.download = `${docType}.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                URL.revokeObjectURL(url);

                responseBody.textContent = desc;
            } catch (err) {
                responseBody.textContent = "Error while generating PDF: " + err.message;
            }

            return; // ❗ 记得 return，防止落到后面的 JSON fetch
        }


        // risk branch
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
        ].forEach(id => { document.getElementById(id).value = ""; });

        const tplInput = document.getElementById("docTemplate");
        if (tplInput) tplInput.value = "";

        const imgInput = document.getElementById("docImage");
        if (imgInput) imgInput.value = "";
    }
    if (currentMode === "risk") {
        document.getElementById("riskMessage").value = "";
        document.getElementById("riskCountry").value = "";
    }
});