from typing import List
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
            self,
            file_path: str, max_tokens: int = 200
    ) -> List[List[Subtitle]]:
        """
        异步读取并解析 SRT 文件, 并合并相邻的字幕条目

        Args:
            file_path: SRT 文件的路径。

        Returns:
            List[List[Subtitle]]: 解析后的 List 对象列表。
        """
        subtitles = await self.reader.read(file_path)
        subtitles = self.merger.merge(subtitles)
        chunked_subtitles = self.splitter.split_subtitles(
            subtitles,
            max_tokens=max_tokens
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
