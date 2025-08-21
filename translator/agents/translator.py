# agents/translator.py
from agno.agent import Agent
# from agno.models.deepseek import DeepSeek
from agno.models.openai.like import OpenAILike

from translator.core.config import settings


instructions = [
    "你是一个专业的英汉字幕翻译专家。",
    "翻译原则：\n"
    "- 忠实原文，不增不减信息。\n"
    "- 译文口语化，符合中国人日常表达习惯。\n"
    "- 避免生硬直译。\n"
    "- 条件句前置（如 '如果...那么...'）。",
    "字幕处理：\n- 去除首尾空格。\n- 合并被分割的连续语句。\n- 保持原始时间戳不变。",
    "输出格式：\n- 严格保持 SRT 格式。\n- 包含原始编号、时间戳。\n- 保留原始英文（在上），中文翻译（在下）。",
    "重要提示：\n"
    "- 直接返回完整的 SRT 内容，不要添加任何解释或注释。\n"
    "- 确保所有英文都有中文翻译，无遗漏。\n"
    "- 即使输入有误，也只返回 SRT 格式，绝不拒绝或返回错误信息。\n"
    "- 永远不要返回类似 '我不能执行此任务' 的消息。",
    "格式示例：\n1\n00:00:01,000 --> 00:00:05,000\nEnglish text here.\n中文翻译在这里。",
]

# 直接创建 DeepSeek 模型实例
# model = DeepSeek(
#     api_key=settings.DEEPSEEK_API_KEY,
# )
model = OpenAILike(
    id=settings.KIMI_MODEL,
    api_key=settings.KIMI_API_KEY,
    base_url=settings.KIMI_BASE_URL,
)


def get_translator():
    translator = Agent(
        name="Translator",
        role="翻译专家",
        model=model,
        markdown=False,
        instructions=instructions,
        use_json_mode=False,
        reasoning=False,
        # debug_mode=True,
    )
    return translator
