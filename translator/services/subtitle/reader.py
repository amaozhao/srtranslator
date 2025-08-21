import os
from typing import List

import aiofiles

from .parser import SubtitleParser, Subtitle


class SubtitleReader:
    """字幕文件读取服务"""

    def __init__(self):
        self.parser = SubtitleParser()

    async def load(self, file_path: str, encoding: str = "utf-8") -> str:
        """异步读取文本文件的内容。

        Args:
            file_path: 文件路径
            encoding: 文件编码，默认为 UTF-8

        Returns:
            str: 文件内容

        Raises:
            FileNotFoundError: 如果文件不存在
            PermissionError: 如果没有权限读取文件
            UnicodeDecodeError: 如果文件编码不匹配
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 检查文件是否可读
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"没有权限读取文件: {file_path}")

        async with aiofiles.open(file_path, "r", encoding=encoding) as file:
            content = await file.read()
            return content

    async def read(
        self, file_path: str, ignore_errors: bool = False
    ) -> List[Subtitle]:
        """
        异步从 SRT 文件中解析字幕内容。

        Args:
            file_path: SRT 字幕文件的路径。
            encoding: 文件编码，默认为 UTF-8。
            ignore_errors: 如果为 True，则忽略解析错误。

        Returns:
            List[Subtitle]: 解析后的 Subtitle 对象列表。

        Raises:
            FileNotFoundError: 如果文件不存在。
            PermissionError: 如果没有读取文件的权限。
            UnicodeDecodeError: 如果文件编码不匹配。
            SRTParseError: 如果解析过程中遇到不可恢复的错误且 ignore_errors 为 False。
        """
        srt_content = await self.load(file_path)
        return self.parser.parse(srt_content, ignore_errors)
