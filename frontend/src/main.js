import {
  callCommunicationAPI,
  callDocumentAPI
} from "./api.js";

const logoutBtn = document.getElementById("logoutBtn");

const loginScreen = document.getElementById("loginScreen");
const appShell = document.getElementById("appShell");

const loginBtn = document.getElementById("loginBtn");
const loginError = document.getElementById("loginError");

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
});

async function login() {
    const userName = document.getElementById("loginUserName").value.trim();
    const password = document.getElementById("loginPassword").value.trim();

    if (!userName || !password) {
        loginError.textContent = "invalid login";
        return;
    }

    try {
        const res = await fetch("http://127.0.0.1:8000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
                user_name: userName,
                password: password
            })
        });

        const data = await res.json();

        if (data.ok) {
            // 登录成功
            localStorage.setItem("auth_token", data.token);
            loginError.textContent = "";

            loginScreen.style.display = "none";
            appShell.style.display = "block";
        } else {
            // 登录失败
            loginError.textContent = "invalid login";
        }

    } catch (err) {
        loginError.textContent = "invalid login";
    }
}

loginBtn.addEventListener("click", login);

window.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("auth_token");
    if (token) {
        loginScreen.style.display = "none";
        appShell.style.display = "block";
    }
});

function logout() {
    const token = localStorage.getItem("auth_token");

    // 可选：通知后端
    if (token) {
        fetch("http://127.0.0.1:8000/api/auth/logout", {
            method: "POST",
            headers: {
                "Authorization": "Bearer " + token
            }
        }).catch(() => {});
    }

    // 清除本地 token
    localStorage.removeItem("auth_token");

    // 切换界面
    appShell.style.display = "none";
    loginScreen.style.display = "flex";
}

logoutBtn.addEventListener("click", logout);