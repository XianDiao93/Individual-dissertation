// api.js
// Centralised API client for the frontend

const API_BASE_URL = "http://127.0.0.1:8000";

function getToken() {
    return localStorage.getItem("auth_token");
}

/**
 * Generic helper to call a JSON API.
 * @param {string} endpoint
 * @param {object} options
 * @returns {Promise<any>}
 */
async function callApi(endpoint, options = {}) {
    const {
        method = "POST",
        payload = null,
        token = null,
    } = options;

    const headers = {};

    if (payload !== null) {
        headers["Content-Type"] = "application/json";
    }

    if (token) {
        headers["Authorization"] = "Bearer " + token;
    }

    const res = await fetch(API_BASE_URL + endpoint, {
        method,
        headers,
        body: payload !== null ? JSON.stringify(payload) : undefined,
    });

    if (!res.ok) {
        let detail = "";
        try {
            detail = await res.text();
        } catch {
            // ignore
        }
        throw new Error(
            `Request failed with status ${res.status}` +
            (detail ? `: ${detail}` : "")
        );
    }

    return res.json();
}

/**
 * Call communication endpoint.
 * Backend route: POST /api/chat
 */
export function callCommunicationAPI({
    message,
    language,
    region,
    tone,
    replyForm,
}) {
    return callApi("/api/chat", {
        method: "POST",
        token: getToken(),
        payload: {
            message,
            language,
            region,
            tone,
            reply_form: replyForm,
        },
    });
}

/**
 * Call document-generation endpoint.
 * Backend route: POST /api/document
 */
export function callDocumentAPI({
    document_type,
    currency,
    seller_name,
    buyer_name,
    product,
    quantity,
    unit_price,
    incoterm,
    payment_term,
    extra_notes,
}) {
    return callApi("/api/document", {
        method: "POST",
        payload: {
            document_type,
            currency,
            seller_name,
            buyer_name,
            product,
            quantity,
            unit_price,
            incoterm,
            payment_term,
            extra_notes,
        },
    });
}

/**
 * Get current user's profile.
 * Backend route: GET /api/profile/me
 */
export function getMyProfile() {
    return callApi("/api/profile/me", {
        method: "GET",
        token: getToken(),
    });
}