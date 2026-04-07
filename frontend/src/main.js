import { callCommunicationAPI, getMyProfile } from "./api.js";

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

const emailDetailBodyBox = document.getElementById("emailDetailBodyBox");
const emailDetailReplyBox = document.getElementById("emailDetailReplyBox");

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
const emailDetailDeleteBtn = document.getElementById("emailDetailDeleteBtn");

// Profile fields
const profileStatus = document.getElementById("profileStatus");
const profileUid = document.getElementById("profileUid");
const profileUserName = document.getElementById("profileUserName");
const profileRole = document.getElementById("profileRole");
const profileName = document.getElementById("profileName");
const profileEmail = document.getElementById("profileEmail");
const profilePhone = document.getElementById("profilePhone");
const profileRegion = document.getElementById("profileRegion");
const profileCompanyName = document.getElementById("profileCompanyName");

/* =========================
   Helpers
========================= */
function getToken() {
    return localStorage.getItem("auth_token");
}

function authHeaders() {
    const token = getToken();
    return token ? { Authorization: "Bearer " + token } : {};
}

async function fetchJson(url, options = {}) {
    const res = await fetch(url, options);
    if (!res.ok) {
        let detail = "";
        try {
            detail = await res.text();
        } catch {}
        const err = new Error(
            `Request failed with status ${res.status}` + (detail ? `: ${detail}` : "")
        );
        err.status = res.status;
        throw err;
    }
    return res.json();
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function getSeverityClass(severity) {
    const s = String(severity || "unknown").toLowerCase();
    if (s === "critical" || s === "high") return "risk-high";
    if (s === "medium") return "risk-medium";
    if (s === "low") return "risk-low";
    return "risk-unknown";
}

function normalizeRiskTags(source) {
    if (!source || typeof source !== "object") return [];

    if (Array.isArray(source.risk_tags)) {
        return source.risk_tags;
    }

    const risk = source.risk;
    if (!risk || typeof risk !== "object") {
        return [];
    }

    if (Array.isArray(risk.tags)) {
        return risk.tags;
    }

    if (Array.isArray(risk.flags)) {
        return risk.flags;
    }

    return [];
}

function renderRiskTags(tags) {
    if (!Array.isArray(tags) || !tags.length) {
        return `<span class="risk-tag risk-unknown">unknown</span>`;
    }

    return tags
        .map((item) => {
            const tag = typeof item === "string" ? item : (item.tag || "unknown");
            const severity = typeof item === "string" ? "unknown" : (item.severity || "unknown");
            return `<span class="risk-tag ${getSeverityClass(severity)}">${escapeHtml(tag)}</span>`;
        })
        .join(" ");
}

function resetCommunicationInputs() {
    const commMessage = document.getElementById("commMessage");
    if (commMessage) commMessage.value = "";
}

function resetDocumentInputs() {
    const ids = [
        "docSeller",
        "docBuyer",
        "docProduct",
        "docQuantity",
        "docUnitPrice",
        "docIncoterm",
        "docPaymentTerm",
        "docExtra",
    ];

    ids.forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.value = "";
    });

    const docType = document.getElementById("docType");
    const docCurrency = document.getElementById("docCurrency");
    const tplInput = document.getElementById("docTemplate");
    const imgInput = document.getElementById("docImage");

    if (docType) docType.value = "sales_contract";
    if (docCurrency) docCurrency.value = "USD";
    if (tplInput) tplInput.value = "";
    if (imgInput) imgInput.value = "";

    if (docTypeSelect) {
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
    }
}

function resetResponsePanel() {
    responseBody.textContent = "The AI response will appear here.";
}

function resetEmailDetailPanel() {
    selectedEmailId = null;
    emailDetailTitle.textContent = "Email";
    emailDetailFrom.textContent = "-";
    emailDetailCustomerType.textContent = "-";
    emailDetailFiles.textContent = "-";
    emailDetailRisks.innerHTML = "-";
    emailDetailBodyBox.textContent = "(empty)";
    emailDetailReplyBox.textContent = "No reply";
}

function resetProfilePanel() {
    profileStatus.textContent = "Loading...";
    profileUid.textContent = "-";
    profileUserName.textContent = "-";
    profileRole.textContent = "-";
    profileName.textContent = "-";
    profileEmail.textContent = "-";
    profilePhone.textContent = "-";
    profileRegion.textContent = "-";
    profileCompanyName.textContent = "-";
}

function resetEmailsSidebar() {
    unarchivedCountEl.textContent = "0";
    emailsListEl.innerHTML = "";
    emailsEmptyEl.style.display = "block";
}

function resetWorkspaceState() {
    currentMode = "communication";
    showView("home");

    tabs.forEach((t) => t.classList.toggle("active", t.dataset.mode === "communication"));

    const commMode = document.getElementById("mode-communication");
    const docMode = document.getElementById("mode-document");
    if (commMode) commMode.style.display = "block";
    if (docMode) docMode.style.display = "none";

    resetCommunicationInputs();
    resetDocumentInputs();
    resetResponsePanel();
    resetEmailDetailPanel();
    resetProfilePanel();
    resetEmailsSidebar();

    loginError.textContent = "";

    const loginUserName = document.getElementById("loginUserName");
    const loginPassword = document.getElementById("loginPassword");
    if (loginUserName) loginUserName.value = "";
    if (loginPassword) loginPassword.value = "";
}

/* =========================
   Simple view routing
========================= */
let currentView = "home";
let selectedEmailId = null;

function showView(viewName) {
    currentView = viewName;

    viewHome.style.display = viewName === "home" ? "block" : "none";
    viewProfile.style.display = viewName === "profile" ? "block" : "none";
    viewEmailDetail.style.display = viewName === "emailDetail" ? "block" : "none";
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
tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        const mode = tab.dataset.mode;
        if (mode === currentMode) return;

        currentMode = mode;
        tabs.forEach((t) => t.classList.toggle("active", t === tab));

        document.getElementById("mode-communication").style.display =
            mode === "communication" ? "block" : "none";
        document.getElementById("mode-document").style.display =
            mode === "document" ? "block" : "none";

        resetResponsePanel();
    });
});

/* =========================
   Backend call
========================= */
async function callBackend() {
    btnSubmit.disabled = true;
    btnSubmit.textContent = "Processing...";

    try {
        if (currentMode === "communication") {
            const message = document.getElementById("commMessage").value.trim();

            if (!message) {
                responseBody.textContent = "Please enter a message before sending.";
                return;
            }

            const data = await callCommunicationAPI({
                message,
            });

            responseBody.textContent = data.reply || JSON.stringify(data, null, 2);
            await renderEmailsList();
            return;
        }

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

            if (
                (docType === "sales_contract" || docType === "quotation") &&
                templateFileInput.files.length > 0
            ) {
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

                const desc =
                    res.headers.get("X-Doc-Description") || "Document PDF has been generated.";

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
   Clear inputs
========================= */
btnClear.addEventListener("click", () => {
    if (currentMode === "communication") {
        resetCommunicationInputs();
    }

    if (currentMode === "document") {
        resetDocumentInputs();
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
            body: JSON.stringify({ user_name: userName, password }),
        });

        const data = await res.json();

        if (data.ok) {
            localStorage.setItem("auth_token", data.token);
            loginError.textContent = "";

            loginScreen.style.display = "none";
            workspaceShell.style.display = "flex";

            showView("home");
            await renderEmailsList();
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
            headers: { Authorization: "Bearer " + token },
        }).catch(() => {});
    }

    localStorage.removeItem("auth_token");
    resetWorkspaceState();

    workspaceShell.style.display = "none";
    loginScreen.style.display = "flex";

    location.reload();
}

logoutBtn.addEventListener("click", logout);

window.addEventListener("DOMContentLoaded", async () => {
    resetWorkspaceState();

    const token = localStorage.getItem("auth_token");
    if (token) {
        loginScreen.style.display = "none";
        workspaceShell.style.display = "flex";
        showView("home");
        await renderEmailsList();
    } else {
        workspaceShell.style.display = "none";
        loginScreen.style.display = "flex";
    }
});

/* =========================
   Profile loading
========================= */
async function loadProfile() {
    if (!profileStatus) return;

    const token = getToken();
    if (!token) {
        profileStatus.textContent = "Not logged in.";
        profileUid.textContent = "-";
        profileUserName.textContent = "-";
        profileRole.textContent = "-";
        profileName.textContent = "-";
        profileEmail.textContent = "-";
        profilePhone.textContent = "-";
        profileRegion.textContent = "-";
        profileCompanyName.textContent = "-";
        return;
    }

    profileStatus.textContent = "Loading...";

    try {
        const data = await getMyProfile();

        if (!data.ok) {
            profileStatus.textContent = "Error: " + (data.error || "unknown_error");
            return;
        }

        const p = data.profile || {};
        profileUid.textContent = p.uid ?? "-";
        profileUserName.textContent = p.user_name ?? "-";
        profileRole.textContent = p.role ?? "-";
        profileName.textContent = p.name ?? "-";
        profileEmail.textContent = p.email ?? "-";
        profilePhone.textContent = p.phone ?? "-";
        profileRegion.textContent = p.region ?? "-";
        profileCompanyName.textContent = p.company_name ?? "-";

        profileStatus.textContent = "Loaded.";
    } catch (err) {
        profileStatus.textContent = "Error: " + err.message;
    }
}

/* =========================
   Emails: list + detail
========================= */
async function renderEmailsList() {
    const token = getToken();
    if (!token) {
        unarchivedCountEl.textContent = "0";
        emailsListEl.innerHTML = "";
        emailsEmptyEl.style.display = "block";
        return;
    }

    emailsListEl.innerHTML = "";
    emailsEmptyEl.style.display = "none";
    unarchivedCountEl.textContent = "...";

    try {
        const data = await fetchJson(API_BASE_URL + "/api/emails?archived=false", {
            method: "GET",
            headers: {
                ...authHeaders(),
            },
        });

        if (!data.ok) {
            unarchivedCountEl.textContent = "0";
            emailsListEl.innerHTML = "";
            emailsEmptyEl.style.display = "block";
            return;
        }

        const emails = data.emails || [];
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
            title.textContent = e.subject || `Email ${e.id}`;

            const meta = document.createElement("div");
            meta.className = "m";

            const fromText = e.from || "-";
            const riskLevel = e.risk_level || e?.risk?.level || "unknown";

            const riskLevelHtml = `<span class="risk-tag ${getSeverityClass(riskLevel)}">${escapeHtml(riskLevel)}</span>`;

            meta.innerHTML = `
                ${escapeHtml(fromText)} · ${riskLevelHtml} · ${escapeHtml(e.status || "draft")}
            `;

            item.appendChild(title);
            item.appendChild(meta);

            item.addEventListener("click", () => openEmailDetail(e.id));

            emailsListEl.appendChild(item);
        }
    } catch (err) {
        unarchivedCountEl.textContent = "0";
        emailsListEl.innerHTML = "";
        emailsEmptyEl.style.display = "block";
    }
}

async function openEmailDetail(emailId) {
    const token = getToken();
    if (!token) return;

    selectedEmailId = emailId;

    emailDetailTitle.textContent = `Email ${emailId}`;
    emailDetailFrom.textContent = "-";
    emailDetailCustomerType.textContent = "-";
    emailDetailFiles.textContent = "-";
    emailDetailRisks.innerHTML = `<span class="risk-tag risk-unknown">loading...</span>`;
    emailDetailBodyBox.textContent = "(loading...)";
    emailDetailReplyBox.textContent = "No reply";

    showView("emailDetail");

    try {
        const data = await fetchJson(API_BASE_URL + "/api/emails/" + encodeURIComponent(emailId), {
            method: "GET",
            headers: {
                ...authHeaders(),
            },
        });

        if (!data.ok) {
            emailDetailRisks.textContent = "Error: " + (data.error || "unknown_error");
            emailDetailBodyBox.textContent = "(empty)";
            emailDetailReplyBox.textContent = "No reply";
            return;
        }

        const e = data.email || {};

        emailDetailTitle.textContent = e.subject || `Email ${e.id || emailId}`;
        emailDetailFrom.textContent = e.from || "-";

        const lang = e.language || "unknown";
        const region = e.source_region || "unknown";
        const status = e.status || "draft";
        emailDetailCustomerType.textContent = `lang:${lang} · region:${region} · status:${status}`;

        emailDetailFiles.textContent = "N/A";

        const risk = e.risk || {};
        const level = risk.level || "unknown";
        const tags = normalizeRiskTags(e);
        const tagsHtml = renderRiskTags(tags);

        emailDetailRisks.innerHTML = `
            <span class="risk-tag ${getSeverityClass(level)}">level:${escapeHtml(level)}</span>
            ${tagsHtml}
        `;

        const body = e.body && String(e.body).trim() ? e.body : "(empty)";
        const reply = e.reply && String(e.reply).trim() ? e.reply : "No reply";
        emailDetailBodyBox.textContent = body;
        emailDetailReplyBox.textContent = reply;
    } catch (err) {
        const msg = err && err.message ? err.message : String(err);

        if (
            msg.includes("no such file") ||
            msg.includes("email not found") ||
            msg.includes("404")
        ) {
            alert(`Email ${emailId} no longer exists (it may have been deleted).`);
            selectedEmailId = null;
            showView("home");
            await renderEmailsList();
            return;
        }

        emailDetailRisks.textContent = "Error: " + msg;
        emailDetailBodyBox.textContent = "(empty)";
        emailDetailReplyBox.textContent = "No reply";
    }
}

/* =========================
   Sidebar navigation
========================= */
navProfileBtn.addEventListener("click", async () => {
    showView("profile");
    await loadProfile();
});

profileBackBtn.addEventListener("click", () => showView("home"));
emailDetailBackBtn.addEventListener("click", () => showView("home"));

emailDetailDeleteBtn.addEventListener("click", async () => {
    const token = getToken();
    if (!token) return;

    if (!selectedEmailId) {
        alert("No email selected.");
        return;
    }

    const ok = confirm(
        `Delete email ${selectedEmailId}? This will remove the JSON file from user_data.`
    );
    if (!ok) return;

    try {
        const data = await fetchJson(
            API_BASE_URL + "/api/emails/" + encodeURIComponent(selectedEmailId),
            {
                method: "DELETE",
                headers: {
                    ...authHeaders(),
                },
            }
        );

        if (!data.ok) {
            alert("Delete failed: " + (data.error || "unknown_error"));
            return;
        }

        const deletedId = selectedEmailId;
        selectedEmailId = null;

        const node = emailsListEl.querySelector(`[data-email-id="${deletedId}"]`);
        if (node) node.remove();

        const cur = parseInt(unarchivedCountEl.textContent || "0", 10);
        if (!Number.isNaN(cur) && cur > 0) {
            unarchivedCountEl.textContent = String(cur - 1);
        }

        if (!emailsListEl.querySelector(".sidebar-item")) {
            emailsEmptyEl.style.display = "block";
        }

        showView("home");
        resetResponsePanel();

        await renderEmailsList();
    } catch (err) {
        alert("Delete failed: " + err.message);
    }
});