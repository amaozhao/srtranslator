from typing import List

from .parser import Subtitle


class SubtitleConnector:
    """字幕串联"""

    def connect(self, chunks: List[List[Subtitle]]) -> List[Subtitle]:
        """
        将多个字幕块连接成一个完整的字幕列表。

        Args:
            chunks: 包含多个字幕块的列表，每个块是一个 Subtitle 列表。

        Returns:
            List[Subtitle]: 连接后的完整 Subtitle 列表。
        """
        if not chunks:
            return []

        connected_subtitles = []
        for chunk in chunks:
            connected_subtitles.extend(chunk)

        return connected_subtitles
