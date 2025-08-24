from pathlib import Path
from typing import AsyncGenerator, List, Optional

from agno.workflow import RunResponse, Workflow

from translator.core.logger import workflow_logger as logger
from translator.services.subtitle.parser import Subtitle
from translator.services.subtitle.srt import SrtService

from .proofer import get_proofer
from .translator import get_translator


class SubtitleWorkflow(Workflow):
    """
    一个使用 AI 代理处理字幕的工作流。
    """

    def __init__(self, tokens: int = 2500):
        """
        初始化 SubtitleWorkflow。

        Args:
            tokens: 每个处理块的最大 token 数
        """
        super().__init__()
        self.srt_service = SrtService()
        self.tokens = tokens

    async def arun(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        source_lang: str = "English",
        target_lang: str = "Chinese",
    ) -> AsyncGenerator[RunResponse, None]:
        """异步生成器入口点，处理字幕并分块返回状态。"""
        # 解析输入/输出路径
        output_file = await self._get_out_path(input_path, output_path, target_lang)

        yield RunResponse(content=f"开始处理字幕文件: {input_path}", run_id=self.run_id)

        # 1. 分割字幕为可处理的块
        yield RunResponse(content="分割字幕为处理块...", run_id=self.run_id)
        chunks = await self._split_subtitles(input_path)
        if not chunks:
            yield RunResponse(content="字幕分块失败，流程终止。", run_id=self.run_id)
            return

        yield RunResponse(content=f"分割为 {len(chunks)} 个块。", run_id=self.run_id)
        final_subs = []

        # 2. 依次处理每个块
        for i, chunk in enumerate(chunks, 1):
            yield RunResponse(content=f"处理第 {i}/{len(chunks)} 块...", run_id=self.run_id)

            process_chunk = await self._run_chunk(chunk, i, input_path, target_lang)

            if not process_chunk:
                yield RunResponse(content=f"第 {i} 块字幕处理失败，流程终止。", run_id=self.run_id)
                return

            final_subs.extend(process_chunk)
            yield RunResponse(content=f"已完成第 {i}/{len(chunks)} 块。", run_id=self.run_id)

        # 3. 保存处理后的字幕
        yield RunResponse(content=f"保存处理后的字幕到 {output_file}...", run_id=self.run_id)
        await self.srt_service.write(str(output_file), final_subs)
        yield RunResponse(content=f"全部完成，输出文件: {output_file}", run_id=self.run_id)

    async def _get_out_path(self, in_path: str, out_path: Optional[str], lang: str) -> Path:
        """解析输出路径"""
        input_path_obj = Path(in_path)
        if out_path:
            output_path_obj = Path(out_path)
            if output_path_obj.exists() and output_path_obj.is_dir():
                output_file = output_path_obj / input_path_obj.with_stem(f"{input_path_obj.stem}_{lang}").name
            else:
                output_file = output_path_obj
        else:
            output_file = input_path_obj.with_stem(f"{input_path_obj.stem}_{lang}")

        return output_file

    async def _split_subtitles(self, in_path: str) -> Optional[List[List[Subtitle]]]:
        """分割字幕为处理块"""
        return await self.srt_service.split(in_path, self.tokens)

    async def _run_chunk(
        self, chunk: List[Subtitle], chunk_index: int, in_path: str, lang: str
    ) -> Optional[List[Subtitle]]:
        """处理单个字幕块并验证结果。"""
        chunk_count = len(chunk)
        logger.info(f"第 {chunk_index} 块原始字幕条数: {chunk_count}")

        # 1. 尝试从缓存加载已处理的 SRT 块
        cached = await self._get_cache(in_path, chunk_index, lang)

        if cached:
            _chunk = self.srt_service.parser.parse(cached)
            if _chunk and len(_chunk) == chunk_count:
                logger.info(f"第 {chunk_index} 块命中缓存，跳过处理")
                return _chunk
            else:
                logger.warning("缓存解析失败或条目数不匹配，将重新处理。")

        # 2. 如果缓存不可用，调用代理进行翻译
        final_text = await self._call_agents(chunk, chunk_count)
        if not final_text:
            return None

        # 3. 验证并重组字幕
        final_texts = final_text.split("||")
        if len(final_texts) != chunk_count:
            logger.warning(f"第 {chunk_index} 块代理返回的条目数不匹配，处理失败。")
            return None

        final_subs = []
        for i, text in enumerate(final_texts):
            item_from_chunk = chunk[i]
            # 合并原始内容和翻译内容
            new_content = f"{item_from_chunk.content.strip()}\n{text.strip()}"
            final_subs.append(
                Subtitle(
                    index=item_from_chunk.index,
                    start=item_from_chunk.start,
                    end=item_from_chunk.end,
                    content=new_content,
                    proprietary=item_from_chunk.proprietary,
                )
            )

        # 4. 将处理后的 SRT 块保存到缓存
        cache_content = self.srt_service.parser.compose(final_subs)
        await self._save_cache(in_path, chunk_index, lang, cache_content)

        return final_subs

    async def _get_cache(self, in_path: str, index: int, lang: str) -> Optional[str]:
        """尝试从缓存获取已处理的 SRT 格式块"""
        try:
            cached = await self.srt_service.get_processed_chunk(in_path, index, lang)
            if cached and self.srt_service.parser.parse(cached):
                return cached
        except Exception as e:
            logger.warning(f"尝试从缓存获取失败: {e}")
        return None

    async def _save_cache(self, in_path: str, index: int, lang: str, content: str) -> None:
        """如果需要，将处理后的 SRT 块保存到缓存"""
        try:
            await self.srt_service.save_processed_chunk(in_path, index, lang, content)
        except Exception as e:
            logger.warning(f"保存第 {index} 块缓存失败: {e}")

    async def _call_agents(self, chunk: List[Subtitle], item_count: int, retry_count: int = 0) -> str:
        """调用代理进行拼写检查和翻译，并处理重试。"""
        # 从 SRT 块中提取纯文本内容
        input_text = "||".join([item.content for item in chunk])

        # 1. 拼写检查 (Proofer)
        try:
            logger.info("开始拼写检查...")
            proof_result = await get_proofer().arun(input_text)
            proofed = proof_result.content.proofed
            logger.info(f"Proofer 返回内容: {proofed[:150]}...")
        except Exception as e:
            logger.error(f"Proofer 调用失败: {e}。回退到原始内容。")
            proofed = input_text

        # 2. 翻译 (Translator)
        try:
            logger.info("开始翻译处理...")
            trans_result = await get_translator().arun(proofed)
            translated = trans_result.content.translated
            logger.info(f"Translator 返回内容: {translated[:150]}...")
        except Exception as e:
            logger.error(f"Translator 调用失败: {e}。返回空字符串。")
            return ""

        # 3. 验证翻译结果数量
        trans_texts = translated.split("||")
        if len(trans_texts) != item_count:
            logger.warning(f"翻译结果条目数不匹配（翻译后: {len(trans_texts)} vs 原始: {item_count}）。尝试重试...")
            if retry_count < 2:
                return await self._call_agents(chunk, item_count, retry_count + 1)
            else:
                logger.error("重试次数耗尽，翻译失败。")
                return ""

        return translated
