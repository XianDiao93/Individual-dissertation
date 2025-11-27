// api.js
// Centralised API client for the frontend

const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * Generic helper to call a POST JSON API.
 * @param {string} endpoint - e.g. "/api/chat"
 * @param {object} payload - Request body JSON
 * @returns {Promise<any>} - Parsed JSON response
 */
async function callApi(endpoint, payload) {
      const res = await fetch(API_BASE_URL + endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
      });

    // Basic error handling
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
 * Call communication (business email) endpoint.
 * Expected backend route: POST /api/chat
 */
export function callCommunicationAPI({ message, language, region, tone }) {
    return callApi("/api/chat", {
        message,
        language,
        region,
        tone,
    });
}

/**
 * Call document-generation endpoint.
 * Expected backend route: POST /api/document
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
    });
}

/**
 * Call risk-analysis endpoint.
 * Expected backend route: POST /api/risk
 */
export function callRiskAPI({ message, country, transaction_type }) {
    return callApi("/api/risk", {
        message,
        country,
        transaction_type,
    });
}