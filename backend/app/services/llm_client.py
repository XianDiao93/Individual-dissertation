# backend/app/services/llm_client.py
import os
from typing import Optional

from openai import OpenAI

# 从环境变量读取 API Key：你需要自己在系统里设置 OPENAI_API_KEY
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

***REMOVED***
    # 开发阶段可以直接抛异常，提醒你没配好 key
    raise RuntimeError(
        "OPENAI_API_KEY environment variable is not set. "
        "Please set it before starting the backend."
    )

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_business_reply(
    message: str,
    language: str = "en",
    region: str = "EU",
    tone: str = "formal",
    model: str = "gpt-4o-mini",  # 便宜的小模型，适合开发阶段
) -> str:
    """
    Call OpenAI Responses API to generate a business email reply.
    No training, pure inference.
    """

    system_prompt = (
        "You are an AI assistant helping SMEs with international trade communication. "
        "Generate clear, professional, and culturally appropriate business email replies in English. "
        "Always respond in English unless explicitly instructed otherwise. "
        f"Target region: {region}. Tone: {tone}. "
        "Keep the email concise and polite, and include a proper greeting and closing."
    )

    # 使用 Responses API（推荐的统一接口）
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
    )

    # 官方文档提供的便捷属性：output_text，适合纯文本场景
    # https://platform.openai.com/docs/api-reference/responses/create :contentReference[oaicite:2]{index=2}
    reply_text: Optional[str] = getattr(response, "output_text", None)

    if not reply_text:
        # 兜底：如果没有 output_text，就把整个对象转成字符串返回
        reply_text = str(response)

    return reply_text