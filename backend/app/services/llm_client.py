# backend/app/services/llm_client.py
import os
from typing import Optional

from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

***REMOVED***
    raise RuntimeError(
        "OPENAI_API_KEY environment variable is not set. "
        "Please set it before starting the backend."
    )

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_business_reply(
    message: str,
    language: str = "auto",
    region: str = "EU",
    tone: str = "formal",
    reply_form: str = "email",
    model: str = "gpt-4o-mini",
) -> str:
    # Normalise tone
    tone_str = tone.lower()
    if tone_str not in {"formal", "neutral", "friendly"}:
        tone_str = "formal"

    # Normalise reply_form
    reply_form_norm = reply_form.lower()
    if reply_form_norm not in {"email", "chat"}:
        reply_form_norm = "email"

    if reply_form_norm == "chat":
        mode_description = (
            "You are chatting with the user in a business context. "
            "Provide a short, direct conversational reply, as in a live chat or "
            "instant messaging tool. You may skip formal email headers and "
            "sign-offs (no need for 'Dear ...' and 'Best regards')."
        )
        formatting_instructions = (
            "- Keep the reply short (1–3 short paragraphs or a few sentences).\n"
            "- You can use 'Hi' or no greeting at all if it feels natural.\n"
            "- Do NOT include signatures or long closings."
        )
    else:
        mode_description = (
            "You are composing a full business email reply for the user. "
            "Include an appropriate greeting and closing, and use a clear email structure."
        )
        formatting_instructions = (
            "- Include a greeting (e.g. 'Dear ...').\n"
            "- Use one or more paragraphs to answer the inquiry clearly.\n"
            "- Finish with a polite closing (e.g. 'Best regards, ...')."
        )

    system_prompt = (
        "You are an AI assistant helping SMEs with international trade communication.\n\n"
        f"{mode_description}\n\n"
        "LANGUAGE HANDLING:\n"
        "1. First, detect the language of the user's message.\n"
        f"2. The requested output language is: '{language}'.\n"
        "- If the requested language is 'auto', always reply in the detected input language.\n"
        "- If the requested language is a specific language (e.g. 'en', 'zh') and it matches\n"
        "  the detected language, reply in that language.\n"
        "- If the requested language conflicts with the detected language, prioritise the\n"
        "  detected input language and reply in that detected language.\n\n"
        "REGION & TONE:\n"
        f"- Target region: {region}. Adapt the style, politeness and phrasing to typical\n"
        "  business communication practices in this region (e.g. EU/US/ME/ASIA).\n"
        f"- Tone: {tone_str}. Make the reply consistent with this tone.\n\n"
        "FORMATTING:\n"
        f"{formatting_instructions}\n"
        "- Do NOT explain what you are doing; just output the final text."
    )

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"User message (target region={region}, tone={tone_str}, "
                    f"reply_form={reply_form_norm}, requested_language={language}):\n"
                    f"{message}"
                ),
            },
        ],
    )

    reply_text: Optional[str] = getattr(response, "output_text", None)
    if not reply_text:
        reply_text = str(response)

    return reply_text
