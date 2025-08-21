import re
from pathlib import Path
from typing import AsyncGenerator, Optional

from agno.workflow import RunResponse, Workflow

from .proofer import get_proofer
from .translator import get_translator
from translator.core.logger import get_logger
from translator.services.subtitle.srt import SrtService
from translator.services.subtitle.parser import (
    RGX_INDEX, RGX_POSSIBLE_CRLF, RGX_TIMESTAMP
)

logger = get_logger(__name__)


class SubtitleWorkflow(Workflow):
    """
    A workflow for processing subtitles using AI agents.
    """

    # 定义匹配 SRT 块开始的正则表达式
    SRT_BLOCK_START_PATTERN = re.compile(
        r"\s*({idx})\s*{eof}({ts}) *-[ -] *> *({ts})".format(
            idx=RGX_INDEX,
            ts=RGX_TIMESTAMP,
            eof=RGX_POSSIBLE_CRLF
        )
    )

    # 定义匹配代码块的正则表达式
    CODE_BLOCK_PATTERN = re.compile(r'```(?:srt)?\s*\n([\s\S]*?)\n\s*```')

    def __init__(self, max_tokens: int = 2500):
        """
        Initialize the SubtitleWorkflow.

        Args:
            max_tokens: Maximum number of tokens per chunk for processing
        """
        super().__init__()
        self.srt_service = SrtService()
        self.max_tokens = max_tokens

    async def arun(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        source_lang: str = "en",
        target_lang: str = "zh",
    ) -> AsyncGenerator[RunResponse, None]:
        """Async generator entry point for this workflow.

        This yields the same items as `_arun_impl` and is the
        normal method consumers call.
        """
        async for resp in self._arun_impl(
            input_path, output_path, source_lang, target_lang
        ):
            yield resp

    async def _arun_impl(
        self,
        input_path: str,
        output_path: Optional[str],
        source_lang: str = "en",
        target_lang: str = "zh",
    ) -> AsyncGenerator[RunResponse, None]:
        """
        实际的处理实现（如果基类需要直接调用 generator，实现放在这里）。
        """
        # 解析输入/输出路径，确保输出文件默认在输入同目录并添加目标语言后缀
        in_path_obj = Path(input_path)
        if output_path:
            out_path_obj = Path(output_path)
            # 如果给定的是目录，保留原始目录结构并添加后缀
            if out_path_obj.exists() and out_path_obj.is_dir():
                out_file = out_path_obj / in_path_obj.with_stem(
                    f"{in_path_obj.stem}_{target_lang}"
                ).name
            else:
                # 当作文件路径处理（即使不存在，也按文件路径写入）
                out_file = out_path_obj
        else:
            out_file = in_path_obj.with_stem(
                f"{in_path_obj.stem}_{target_lang}"
            )

        yield RunResponse(
            content=f"开始处理字幕文件: {input_path}",
            run_id=self.run_id,
        )
        # 1. Split into manageable chunks
        yield RunResponse(content="分割字幕为处理块...", run_id=self.run_id)
        chunks = await self.srt_service.split(input_path, self.max_tokens)
        if not chunks:
            yield RunResponse(
                content="字幕分块失败，流程终止。",
                run_id=self.run_id,
            )
            return
        yield RunResponse(content=f"分割为 {len(chunks)} 个块。", run_id=self.run_id)
        processed_subtitles = []
        # 2. Process each chunk
        for i, chunk in enumerate(chunks, 1):
            yield RunResponse(
                content=f"处理第 {i}/{len(chunks)} 块...", run_id=self.run_id
            )
            chunk_srt = self.srt_service.parser.compose(chunk)
            if not chunk_srt:
                yield RunResponse(
                    content=f"第 {i} 块字幕合成失败，流程终止。",
                    run_id=self.run_id,
                )
                return
            processed_srt = await self._process_chunk(
                chunk_srt, source_lang, target_lang
            )
            if not processed_srt:
                yield RunResponse(
                    content=f"第 {i} 块字幕处理失败，流程终止。",
                    run_id=self.run_id,
                )
                return
            processed_chunk = self.srt_service.parser.parse(processed_srt)
            if not processed_chunk:
                yield RunResponse(
                    content=f"第 {i} 块字幕解析失败，流程终止。",
                    run_id=self.run_id,
                )
                return
            processed_subtitles.extend(processed_chunk)
            yield RunResponse(
                content=f"已完成第 {i}/{len(chunks)} 块。", run_id=self.run_id
            )
        # 3. Save the processed subtitles
        yield RunResponse(
            content=f"保存处理后的字幕到 {out_file}...", run_id=self.run_id
        )
        await self.srt_service.write(str(out_file), processed_subtitles)
        yield RunResponse(
            content=f"全部完成，输出文件: {out_file}",
            run_id=self.run_id,
        )

    # 为兼容底层 Workflow 的调用约定，提供一个带参数的 generator 方法
    async def arun_workflow_generator(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        source_lang: str = "en",
        target_lang: str = "zh",
    ) -> AsyncGenerator[RunResponse, None]:
        """兼容层：将调用转发到实现层 `_arun_impl`。"""
        async for resp in self._arun_impl(
            input_path, output_path, source_lang, target_lang
        ):
            yield resp

    def is_valid_srt_format(self, content: str) -> tuple[bool, str]:
        """
        验证内容是否符合 SRT 格式，如果不符合则尝试提取有效的 SRT 部分。

        Args:
            content: 要验证的内容

        Returns:
            (是否有效, 错误信息)
        """
        if not content or not content.strip():
            return False, "内容为空"

        # 首先尝试直接解析
        try:
            subtitle = self.srt_service.parser.parse(content)
            if subtitle:
                return True, ""
        except Exception:
            pass

        # 尝试提取 SRT 内容
        try:
            # 查找第一个匹配项
            match = self.SRT_BLOCK_START_PATTERN.search(content)
            if match:
                # 从匹配到的第一个字幕编号开始截取内容
                start_pos = match.start(1)
                extracted_content = content[start_pos:]

                # 尝试解析提取的内容
                subtitle = self.srt_service.parser.parse(extracted_content)
                if subtitle:
                    return True, ""

            # 尝试从代码块中提取 SRT 内容
            code_match = self.CODE_BLOCK_PATTERN.search(content)
            if code_match:
                extracted_content = code_match.group(1)
                subtitle = self.srt_service.parser.parse(extracted_content)
                if subtitle:
                    return True, ""

            return False, "未找到有效的 SRT 格式内容"
        except Exception as e:
            return False, f"SRT 内容提取失败: {str(e)}"

    def _extract_valid_srt(
        self, content: str, label: str = "Agent"
    ) -> tuple[bool, str, str]:
        """
        尝试验证并从给定文本中提取有效的 SRT 内容。

        Returns:
            (is_valid, srt_content_or_original, error_msg)
        """
        # 先尝试直接验证（该方法本身也会尝试解析和提取）
        is_valid, error_msg = self.is_valid_srt_format(content)
        if is_valid:
            return True, content, ""

        # 1) 尝试通过匹配第一个字幕块开始截取
        match = self.SRT_BLOCK_START_PATTERN.search(content)
        if match:
            start_pos = match.start(1)
            extracted = content[start_pos:]
            try:
                subtitle = self.srt_service.parser.parse(extracted)
                if subtitle:
                    logger.info(f"成功从 {label} 输出中提取有效的 SRT 内容")
                    return True, extracted, ""
            except Exception:
                pass

        # 2) 尝试从代码块中提取
        code_match = self.CODE_BLOCK_PATTERN.search(content)
        if code_match:
            extracted = code_match.group(1)
            try:
                subtitle = self.srt_service.parser.parse(extracted)
                if subtitle:
                    logger.info(f"成功从 {label} 代码块中提取有效的 SRT 内容")
                    return True, extracted, ""
            except Exception:
                pass

        # 都失败，返回原始内容和错误信息
        return False, content, error_msg

    async def _process_chunk(
        self, chunk_srt: str, source_lang: str, target_lang: str
    ) -> str:
        """
        Process a single subtitle chunk with agents in sequence,
        with detailed logging.
        Args:
            chunk_srt: SRT string for the chunk
            source_lang: Source language
            target_lang: Target language
        Returns:
            Processed subtitles in SRT format
        """

        # 1. 拼写检查 (Proofer)
        logger.info("开始拼写检查")
        proof = await get_proofer().arun(chunk_srt)
        proofed_content = proof.content

        # 记录 Proofer 返回的原始内容（截取前500个字符）
        logger.info(f"Proofer 返回内容前500字符: {proofed_content[:500]}")

        # 验证 Proofer 输出格式并尝试提取有效 SRT
        is_valid, proofed_content, error_msg = self._extract_valid_srt(
            proofed_content, label="Proofer"
        )
        if not is_valid:
            logger.warning(
                f"Proofer 输出格式无效: {error_msg}，回退到上一步输出"
            )
            logger.debug(f"Proofer 完整输出内容: '''{proofed_content}'''")
        else:
            logger.info("Proofer 输出格式有效")

        # 2. 翻译 (Translator)
        logger.info("开始翻译处理")
        translated = await get_translator().arun(proofed_content)
        translated_content = translated.content

        # 记录 Translator 返回的原始内容（截取前500个字符）
        logger.info(f"Translator 返回内容前500字符: {translated_content[:500]}")

        # 验证 Translator 输出格式并尝试提取有效 SRT
        is_valid, translated_content, error_msg = self._extract_valid_srt(
            translated_content, label="Translator"
        )
        if not is_valid:
            logger.warning(
                f"Translator 输出格式无效: {error_msg}，回退到上一步输出"
            )
            logger.debug(f"Translator 完整输出内容: '''{translated_content}'''")
            translated_content = proofed_content
        else:
            logger.info("Translator 输出格式有效")

        return translated_content
