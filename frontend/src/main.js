import { callCommunicationAPI } from "./api.js";

const API_BASE_URL = "http://127.0.0.1:8000";

/* =========================
   DOM refs
========================= */
const loginScreen = document.getElementById("loginScreen");
const workspaceShell = document.getElementById("workspaceShell");

const loginBtn = document.getElementById("loginBtn");
const loginError = document.getElementById("loginError");

const logoutBtn = document.getElementById("logoutBtn");

const responseBody = document.getElementById("responseBody");
const btnSubmit = document.getElementById("btnSubmit");
const btnClear = document.getElementById("btnClear");

const tabs = document.querySelectorAll(".tab-btn");
let currentMode = "communication";

const docTypeSelect = document.getElementById("docType");
const docTemplateGroup = document.getElementById("docTemplateGroup");
const docImageGroup = document.getElementById("docImageGroup");

// Sidebar
const navProfileBtn = document.getElementById("navProfileBtn");
const emailsListEl = document.getElementById("emailsList");
const emailsEmptyEl = document.getElementById("emailsEmpty");
const unarchivedCountEl = document.getElementById("unarchivedCount");

// Views
const viewHome = document.getElementById("view-home");
const viewProfile = document.getElementById("view-profile");
const viewEmailDetail = document.getElementById("view-email-detail");

const profileBackBtn = document.getElementById("profileBackBtn");
const emailDetailBackBtn = document.getElementById("emailDetailBackBtn");

// Email detail fields
const emailDetailTitle = document.getElementById("emailDetailTitle");
const emailDetailFrom = document.getElementById("emailDetailFrom");
const emailDetailCustomerType = document.getElementById("emailDetailCustomerType");
const emailDetailFiles = document.getElementById("emailDetailFiles");
const emailDetailRisks = document.getElementById("emailDetailRisks");

/* =========================
   Simple view routing
========================= */
let currentView = "home"; // "home" | "profile" | "emailDetail"
let selectedEmailId = null;

function showView(viewName) {
  currentView = viewName;

  viewHome.style.display = viewName === "home" ? "block" : "none";
  viewProfile.style.display = viewName === "profile" ? "block" : "none";
  viewEmailDetail.style.display = viewName === "emailDetail" ? "block" : "none";
}

/* =========================
   Sidebar data (local only)
   Later you can swap to backend.
========================= */
const EMAILS_KEY = "unarchived_emails_v1";

function seedEmailsIfEmpty() {
    const raw = localStorage.getItem(EMAILS_KEY);
    if (raw) return;

    const demo = [
        {
            id: "em_1001",
            subject: "Inquiry about LED panel lights (MOQ & lead time)",
            from: "buyer01@example.com",
            customer_type: "New buyer",
            files: ["spec_sheet.pdf", "catalog_2026.pdf"],
            risks: ["Sanctions: none", "Payment: unknown", "Region: EU"],
        },
        {
            id: "em_1002",
            subject: "Request for quotation: 10,000 units FOB Shanghai",
            from: "procurement@demo-import.com",
            customer_type: "Potential distributor",
            files: ["rfq.xlsx"],
            risks: ["Payment: T/T requested", "Delivery: tight schedule"],
        },
    ];

    localStorage.setItem(EMAILS_KEY, JSON.stringify(demo));
}

function getEmails() {
    try {
        return JSON.parse(localStorage.getItem(EMAILS_KEY) || "[]");
    } catch {
        return [];
    }
}

function renderEmailsList() {
    const emails = getEmails();

    unarchivedCountEl.textContent = String(emails.length);

    emailsListEl.innerHTML = "";

    if (!emails.length) {
        emailsEmptyEl.style.display = "block";
        return;
    }

    emailsEmptyEl.style.display = "none";

    for (const e of emails) {
        const item = document.createElement("div");
        item.className = "sidebar-item";
        item.dataset.emailId = e.id;

        const title = document.createElement("div");
        title.className = "t";
        title.textContent = e.subject || "(No subject)";

        const meta = document.createElement("div");
        meta.className = "m";
        meta.textContent = `${e.from || "-"} · ${e.customer_type || "-"}`;

        item.appendChild(title);
        item.appendChild(meta);

        item.addEventListener("click", () => openEmailDetail(e.id));

        emailsListEl.appendChild(item);
    }
}

function openEmailDetail(emailId) {
    const emails = getEmails();
    const found = emails.find(x => x.id === emailId);
    if (!found) return;

    selectedEmailId = emailId;

    emailDetailTitle.textContent = found.subject || "Email";
    emailDetailFrom.textContent = found.from || "-";
    emailDetailCustomerType.textContent = found.customer_type || "-";
    emailDetailFiles.textContent = (found.files && found.files.length) ? found.files.join(", ") : "-";
    emailDetailRisks.textContent = (found.risks && found.risks.length) ? found.risks.join(" · ") : "-";

    showView("emailDetail");
}

/* =========================
   Existing: docType visibility
========================= */
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
    updateDocFieldsVisibility();
}

/* =========================
   Existing: Mode switching
========================= */
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

/* =========================
   Existing: Backend call
========================= */
async function callBackend() {
    btnSubmit.disabled = true;
    btnSubmit.textContent = "Processing...";

    try {
        // communication
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

            responseBody.textContent = data.reply || JSON.stringify(data, null, 2);
            return;
        }

        // document (pdf)
        if (currentMode === "document") {
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
                    body: formData,
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

            return;
        }

    } catch (err) {
        responseBody.textContent = "Error: " + err.message;
    } finally {
        btnSubmit.disabled = false;
        btnSubmit.textContent = "Send Request";
    }
}

btnSubmit.addEventListener("click", callBackend);

/* =========================
   Existing: Clear inputs
========================= */
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

/* =========================
   Auth: login/logout
========================= */
async function login() {
    const userName = document.getElementById("loginUserName").value.trim();
    const password = document.getElementById("loginPassword").value.trim();

    if (!userName || !password) {
        loginError.textContent = "invalid login";
        return;
    }

    try {
        const res = await fetch(API_BASE_URL + "/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_name: userName, password })
        });

        const data = await res.json();

        if (data.ok) {
            localStorage.setItem("auth_token", data.token);
            loginError.textContent = "";

            loginScreen.style.display = "none";
            workspaceShell.style.display = "flex";

            seedEmailsIfEmpty();
            renderEmailsList();
            showView("home");
        } else {
            loginError.textContent = "invalid login";
        }
    } catch {
        loginError.textContent = "invalid login";
    }
}

loginBtn.addEventListener("click", login);

function logout() {
    const token = localStorage.getItem("auth_token");

    if (token) {
        fetch(API_BASE_URL + "/api/auth/logout", {
        method: "POST",
        headers: { "Authorization": "Bearer " + token }
        }).catch(() => {});
    }

    localStorage.removeItem("auth_token");

    workspaceShell.style.display = "none";
    loginScreen.style.display = "flex";
}

logoutBtn.addEventListener("click", logout);

window.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("auth_token");
    if (token) {
        loginScreen.style.display = "none";
        workspaceShell.style.display = "flex";

        seedEmailsIfEmpty();
        renderEmailsList();
        showView("home");
    }
});

/* =========================
   Sidebar navigation
========================= */
navProfileBtn.addEventListener("click", () => showView("profile"));
profileBackBtn.addEventListener("click", () => showView("home"));
emailDetailBackBtn.addEventListener("click", () => showView("home"));