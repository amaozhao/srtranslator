# 设计文档（Design）

## 概要
本设计把字幕处理分为几层：CLI（`command.py`）、Workflow（`SubtitleWorkflow`）、SRT 服务（`SrtService`）、低级组件（reader/parser/splitter/merger/writer）以及外部 Agent（Proofer、Translator）。每一层职责清晰，便于测试和替换实现。

## 组件职责
- CLI (`command.py`)
  - 负责解析命令行参数，收集用户 intent（输入路径、输出目录、语言、token 限制），将工作委派给 `SubtitleWorkflow`。
  - 现在改为把 `output_path`（可为 None 或目录）传入 workflow，由 workflow 负责为单文件生成目标路径。

- Workflow (`translator.agents.workflow.SubtitleWorkflow`)
  - 核心控制流：读取/分割 -> 对每个 chunk 执行 proofer -> translator -> 解析 -> 聚合 -> 写入。
  - 负责生成最终输出路径（当 `output_path` 为 None 或为目录时）。
  - 负责从 agent 返回中提取有效 SRT（`is_valid_srt_format`、`_extract_valid_srt`）。

- SRT 服务 (`SrtService`)
  - 组合 reader/parser/splitter/merger/writer 提供高阶接口：`split(file_path, max_tokens)`, `write(file_path, subtitles)` 等。

- Agents
  - 通过 `get_proofer()` 与 `get_translator()` 返回 Agent 实例（agno.Agent），在测试中通过 monkeypatch 替换。

## 接口契约（Contract）
- SubtitleWorkflow.arun(input_path: str, output_path: Optional[str], source_lang: str, target_lang: str) -> AsyncGenerator[RunResponse, None]
  - 输入：input_path 为文件路径；output_path 可为 None（在此情形下 workflow 将在输入文件同目录自动创建目标路径）、或目录（将写到该目录并保持相对结构）、或具体文件路径。
  - 输出：yield RunResponse 以传递进度/错误/完成信息。

- SrtService.split(file_path: str, max_tokens: int) -> List[List[Subtitle]]
  - 返回值为按 chunk 分组的 Subtitle 列表列表。

- SrtService.write(file_path: str, subtitles: List[Subtitle]) -> None
  - 将合并后的 Subtitle 列表写入到指定路径。

## 数据流（高层）
1. CLI 调用 Workflow.arun
2. Workflow 调用 SrtService.split -> 得到 chunks
3. 对每个 chunk：
   a. composer -> 得到 chunk srt 文本
   b. 调用 proofer.arun
   c. 尝试提取有效 SRT（若失败记录警告，但流程继续）
   d. 调用 translator.arun
   e. 尝试提取有效 SRT（若失败回退到 proofed_content）
   f. parser.parse -> 转为 Subtitle 对象，加入 processed_subtitles
4. write 到 output_path（由 workflow 生成或由 CLI 提供）

## 错误处理策略
- 对外层调用（CLI）应捕获未处理异常并打印友好错误。
- 对 agent 返回非 SRT：尝试提取（首个时间戳块或代码块），若仍失败：
  - Proofer 失败：记录并回退（继续使用原始 chunk_srt）
  - Translator 失败：回退到 proofed_content

## 测试策略
- 单元测试（pytest + pytest-asyncio）
  - mock SrtService.split、SrtService.write、Agent.arun，测试 workflow 在不同返回下的行为。
  - 覆盖路径：成功路径、split 返回空、proofer 返回含代码块的 SRT、translator 返回非 SRT（应回退）。
- 集成测试（可选）
  - 使用小型 SRT 文件进行端到端执行，校验输出 SRT 格式。

## 扩展点
- 支持更多模型（在 agents 模块添加工厂）；
- 增加并发处理多个 chunk（目前按顺序处理，可扩展为并发 with semaphore）；
- 自定义提取策略 plugin（比如更复杂的正则或启发式解析）。
