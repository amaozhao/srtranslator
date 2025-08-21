# 架构文档（Architecture）

## 总览
项目采用分层模块化架构：

- CLI 层：`command.py`（Typer） — 负责参数解析与用户交互（进度、错误信息）。
- 流程层：`translator.agents.workflow.SubtitleWorkflow`（基于 agno.Workflow） — 负责总体控制流与错误回退策略。
- 服务层：`translator.services.subtitle.SrtService` — 封装对文件 I/O、解析、分割和写入的调用。
- 基础组件：`reader`, `parser`, `splitter`, `merger`, `writer`, `connector` — 单一职责实现。
- Agent 层：`translator.agents.proofer` 与 `translator.agents.translator` — 将 AI 模型封装为 Agent 对象。

组件通过明确接口（方法契约）解耦，便于在测试中通过 monkeypatch 替换。

## 关键模块与交互
- `command.py` -> `SubtitleWorkflow.arun`
- `SubtitleWorkflow` -> `SrtService.split` -> (`SubtitleReader.read` -> `SubtitleParser.parse`)
- `SubtitleWorkflow` -> agents（`get_proofer().arun`, `get_translator().arun`）
- `SubtitleWorkflow` -> `SrtService.write` -> `SubtitleWriter.write`

## 部署与运行
- 运行环境：Python 3.12+
- 依赖把控：使用 `requirements.txt` 管理第三方依赖（aiofiles、agno、pytest 等）。
- 本地运行示例：

  - 单文件：

    ```bash
    python command.py file path/to/foo.srt -t zh
    ```

  - 目录（递归）：

    ```bash
    python command.py dir path/to/dir -o path/to/outdir
    ```

## 可观测性与监控
- 日志：`translator.core.logger` 提供模块级日志；workflow 在关键阶段记录 INFO/WARNING/DEBUG。
- 运行时反馈：CLI 使用 rich 展示进度与阶段性反馈。

## 安全与配置
- 模型密钥：从 `translator.core.config.settings` 加载（如 `DEEPSEEK_API_KEY`）；不要把密钥写入源码或版本控制。

## 扩展与替换指南
- 更换模型：修改 `translator.agents.proofer.get_proofer` / `translator.agents.translator.get_translator` 返回的 Agent 配置。
- 增加新的后处理：在 `SubtitleWorkflow` `_process_chunk` 后添加步骤或替换 `SrtService.merger`。

## 备选架构思路（未来改造）
- 并发处理：把 chunk 处理并行化，依赖异步并发限制（如 asyncio.Semaphore）。
- 插件化 agent：使用插件接口动态加载多种 agent 策略。

---

以上文档基于当前代码实现和约定生成，必要时可以进一步扩展为图表（如序列图、组件图）或添加示例 YAML 配置文件。
