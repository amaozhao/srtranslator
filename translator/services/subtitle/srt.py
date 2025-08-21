from typing import List
from pathlib import Path
from .connector import SubtitleConnector
from .merger import SubtitleMerger
from .parser import Subtitle, SubtitleParser
from .reader import SubtitleReader
from .splitter import SubtitleSplitter
from .writer import SubtitleWriter


class SrtService:
    """SRT 字幕处理服务，集成读取、解析、分割、合并和写入功能"""

    def __init__(self):
        self.connector = SubtitleConnector()
        self.reader = SubtitleReader()
        self.parser = SubtitleParser()
        self.splitter = SubtitleSplitter()
        self.merger = SubtitleMerger()
        self.writer = SubtitleWriter()

    async def split(
        self, file_path: str, max_tokens: int = 200
    ) -> List[List[Subtitle]]:
        """
        异步读取并解析 SRT 文件, 并合并相邻的字幕条目

        Args:
            file_path: SRT 文件的路径。

        Returns:
            List[List[Subtitle]]: 解析后的 List 对象列表。
        """
        # 如果存在预先生成的合并文件（同目录、后缀 _merged），优先使用它作为分割来源
        in_path = Path(file_path)
        merged_candidate = in_path.with_stem(f"{in_path.stem}_merged")
        if merged_candidate.exists():
            source_path = str(merged_candidate)
        else:
            source_path = file_path

        subtitles = await self.reader.read(source_path)
        # 合并相邻字幕条目，得到用于后续分割的字幕列表
        merged_subtitles = self.merger.merge(subtitles)

        # 如果之前不存在合并文件，则保存一个，供下一次直接复用
        try:
            if not merged_candidate.exists():
                # 使用 writer 将合并后的字幕异步写入磁盘
                merged_path = str(merged_candidate)
                await self.writer.write(merged_path, merged_subtitles)
        except Exception:
            # 写入失败不应阻塞分割流程；记录或处理可在更高层完成
            pass

        chunked_subtitles = self.splitter.split_subtitles(
            merged_subtitles, max_tokens=max_tokens
        )
        return chunked_subtitles

    def connect(self, chunks: List[List[Subtitle]]) -> List[Subtitle]:
        """
        连接到指定的 URL。

        Args:
            url: 要连接的 URL。
        """
        return self.connector.connect(chunks)

    async def write(self, file_path: str, subtitles: List[Subtitle]) -> None:
        """
        异步写入字幕到 SRT 文件。

        Args:
            file_path: 要写入的 SRT 文件路径。
            subtitles: 要写入的字幕列表。
        """
        await self.writer.write(file_path, subtitles)
