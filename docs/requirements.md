# 需求文档（Requirements）

## 概述
srtranslator 是一个命令行字幕翻译工具，目标是将 SRT 字幕文件通过 AI agent（Proofer、Translator）处理后输出目标语言 SRT。系统聚焦可扩展的处理流水线、可测试性及与本地文件系统的一致性。

## 目标用户
- 需要批量翻译字幕文件的开发者或内容制作者。

## 功能性需求
1. 单文件翻译
   - 接收单个 `.srt` 文件路径，运行 Proofer 与 Translator 流程，并输出目标语言 SRT 文件。
   - 输出文件默认与输入文件同目录，文件名在原名后添加目标语言后缀（如 `movie_en.srt` -> `movie_zh.srt`）。
2. 目录批量翻译
   - 支持递归查找目录下所有子孙目录中的 `.srt` 文件并逐个处理。
   - 当传入输出目录时，保持输入目录的相对结构写入输出目录。
3. 流程可观察性
   - CLI 在处理过程中应有进度与阶段性消息（分割、处理、保存等）。
4. 可替换 AI Agent
   - Proofer 与 Translator 通过工厂函数返回 Agent 对象；在测试/运行时可替换为 mock/dummy 实现。

## 非功能性需求
- 可测试性：关键 I/O 与外部依赖（file read/write、agent 调用）应支持被 mock。
- 稳定性：对模型返回的非 SRT 文本应有提取/回退策略，避免流程中断。
- 性能：支持分块（chunk）处理以控制每个请求的 token 数。
- 可维护性：模块化（services/、agents/、core/）明确职责。

## 错误处理与边界情况
- 输入文件不存在或不可读 -> CLI 报错并退出。
- Agent 返回非 SRT 文本 -> workflow 尝试提取 SRT 块或回退到上一步输出，不抛异常导致流程中断。
- 解析不连续导致 SRTParseError -> parse 可通过 ignore_errors 参数在需要时降级处理。

## 依赖
- Python 3.12+, pytest, pytest-asyncio（测试）
- aiofiles（异步文件 I/O）
- agno（Agent/Workflow 抽象与模型）
- tiktoken（splitter 中的 tokenizer，可选）

## 验收准则
- 对示例 SRT 文件运行 CLI `trans file` 能生成带后缀的目标 SRT 文件并且格式正确。
- 单元测试覆盖 workflow 的主要路径（成功、agent 返回无效、split 返回空）。
- 在指定 `out_dir` 时，输出目录保持相对结构。
