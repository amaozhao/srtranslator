from agno.agent import Agent
# from agno.models.deepseek import DeepSeek
from agno.models.openai.like import OpenAILike

from translator.core.config import settings

# 直接创建 DeepSeek 模型实例
# model = DeepSeek(
#     api_key=settings.DEEPSEEK_API_KEY,
# )
model = OpenAILike(
    id=settings.KIMI_MODEL,
    api_key=settings.KIMI_API_KEY,
    base_url=settings.KIMI_BASE_URL,
)


proofer_instructions = [
    "角色：专业的错词检查专家。",
    "任务：仅负责修正字幕中的错词、错字、拼写错误和重复词语。",
    "处理范围：不修改断句、语法结构或任何其他内容。不进行翻译，保持原始语言不变。",
    "输出格式：必须始终返回完整的 SRT 格式字幕，严格保持原始编号、时间戳和结构不变。",
    "只修改内容中的错误。",
    "重要提示：",
    "1. 如果字幕中没有需要修正的错误，原样返回输入内容。",
    "2. 你的输出必须仅包含 SRT 格式的字幕内容，不包含任何解释、说明或注释。",
    "3. 即使你认为输入有问题，也直接返回 SRT 格式的结果，绝不拒绝或返回错误消息。",
    "4. 永远不要返回'我不能执行这个任务'类的消息，始终返回 SRT 格式的内容。",
]


def get_proofer():
    Proofer = Agent(
        name="Proofer",
        role="错词检查专家",
        model=model,
        markdown=False,
        instructions=proofer_instructions,
        use_json_mode=False,
        reasoning=False,
        # debug_mode=True,
    )
    return Proofer
