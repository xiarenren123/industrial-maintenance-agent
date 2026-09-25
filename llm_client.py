import os

from dotenv import load_dotenv
from openai import OpenAI


def ask_model(prompt: str) -> str:
    """把 Prompt 发送给 DeepSeek，并返回模型生成的文字。"""

    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "没有配置 API Key，请在项目根目录的 .env 文件中填写。"
        )

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content