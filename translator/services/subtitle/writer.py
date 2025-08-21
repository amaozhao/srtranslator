import os
from typing import List

import aiofiles

from .parser import SubtitleParser, Subtitle


class SubtitleWriter:
    """字幕写入"""

    def __init__(self):
        self._srt_parser = SubtitleParser()
        self.compose = self._srt_parser.compose

    async def save(self, content: str, file_path: str, encoding: str = "utf-8") -> str:
        """异步将内容写入文本文件。

        Args:
            content: 要写入的文本内容
            file_path: 目标文件路径
            encoding: 文件编码，默认为 UTF-8

        Returns:
            str: 写入的文件路径

        Raises:
            PermissionError: 如果没有权限写入文件
            OSError: 如果目录不存在或无法创建
        """
        # 确保目标目录存在
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        async with aiofiles.open(file_path, "w", encoding=encoding) as file:
            await file.write(content)
            return file_path

    async def write(
        self,
        file_path: str,
        subtitles: List[Subtitle],
        encoding: str = "utf-8",
        reindex: bool = True,
        start_index: int = 1,
        strict: bool = True,
        eol: str = "\n",
    ) -> str:
        """
        异步将 Subtitle 对象列表合成 SRT 字符串并写入文件。

        Args:
            subtitles: 要合成的 Subtitle 对象列表。
            file_path: 目标 SRT 文件的路径。
            encoding: 文件编码，默认为 UTF-8。
            reindex: 是否根据开始时间重新索引字幕。
            start_index: 如果重新索引，起始索引。
            strict: 是否启用严格模式（移除内容中的空行）。
            eol: 使用的行结束符（默认为 "\\n"）。

        Returns:
            str: 写入的文件路径。

        Raises:
            PermissionError: 如果没有权限写入文件。
            OSError: 如果目录不存在或无法创建。
        """
        composed = self.compose(subtitles, reindex, start_index, strict, eol)
        return await self.save(composed, file_path, encoding)
