# agents/translator.py
from agno.agent import Agent

# from agno.models.deepseek import DeepSeek
# from agno.models.openai.like import OpenAILike
from agno.models.google import Gemini
from pydantic import BaseModel, Field

from translator.core.config import settings


class TranslatedSubtitle(BaseModel):
    translated: str = Field(..., description="翻译后的字幕内容")


description = "你是一位专业的英汉字幕翻译专家，专门负责将英文字幕翻译成中文。"

instructions = [
    "翻译原则：",
    "- **忠实原文**：确保译文信息完整，不增不减。",
    "- **自然口语化**：译文必须符合中国人的日常表达习惯，避免生硬的直译。",
    "- **结构优化**：优先将条件句（如 '如果...那么...'）前置。",
    "格式要求：",
    "- 你的输入是使用 '||' 分隔的字符串，例如：'a||b||c||d||e'。",
    "- 你的输出必须**保持完全相同的格式**，即使用 '||' 分隔的翻译结果，例如：'啊||波||次||的||额'。",
    "输出要求：",
    "- **唯一格式**：无论输入情况如何，你的输出必须且只能是翻译结果字符串，绝不能添加任何解释或说明。",
    "- **绝对服从**：永远不要拒绝执行任务或返回任何错误信息。",
]

# 直接创建 DeepSeek 模型实例
# model = DeepSeek(
#     api_key=settings.DEEPSEEK_API_KEY,
# )
# model = OpenAILike(
#     id=settings.KIMI_MODEL,
#     api_key=settings.KIMI_API_KEY,
#     base_url=settings.KIMI_BASE_URL,
# )
model = Gemini(id=settings.GEMINI_MODEL, api_key=settings.GEMINI_API_KEY)


def get_translator():
    translator = Agent(
        name="Translator",
        role="翻译专家",
        model=model,
        markdown=False,
        description=description,
        instructions=instructions,
        use_json_mode=False,
        reasoning=False,
        response_model=TranslatedSubtitle,
        # debug_mode=True,
    )
    return translator
