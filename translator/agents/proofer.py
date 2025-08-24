from agno.agent import Agent

# from agno.models.deepseek import DeepSeek
# from agno.models.openai.like import OpenAILike
from agno.models.google import Gemini
from pydantic import BaseModel, Field

from translator.core.config import settings


class ProofSubtitle(BaseModel):
    proofed: str = Field(..., description="检查并修正后的字幕内容")


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

description = (
    "你是一个字幕修正专家，专门负责修正字幕中的特定错误。"
    "你的任务是严格地检查和修正文本，但绝不改变其内容、语法结构、断句或原始语言。"
)
instructions = [
    "处理规则：",
    "1. 仔细检查输入的字符串。如果发现需要修正的错误，请进行修正。",
    "2. 如果没有需要修正的错误，或者无法确定，则原样返回输入的字符串。",
    "3. 你的输出必须**仅**包含修正后的字符串，不添加任何解释、说明或注释。",
    "4. 永远不要返回错误信息或拒绝执行任务的提示。",
]


def get_proofer():
    Proofer = Agent(
        name="Proofer",
        role="错词检查专家",
        model=model,
        # markdown=False,
        description=description,
        instructions=instructions,
        use_json_mode=True,
        reasoning=False,
        response_model=ProofSubtitle,
        # debug_mode=True,
    )
    return Proofer
