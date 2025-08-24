from typing import List
from .parser import Subtitle


class SubtitleMerger:
    """字幕合并器"""

    def merge(
        self, subtitles: List[Subtitle], punct_end: str = ",，.。?？!！;；"
    ) -> List[Subtitle]:
        """
        智能合并时间上连续的字幕条目，将逻辑上属于"一句话"但被分割的字幕合并。
        合并逻辑只考虑字幕内容是否以给定的标点符号结尾。

        Args:
            subtitles: 原始 Subtitle 对象的列表。
            punct_end: 标点符号字符串。如果一个字幕以这些标点符号结尾，
                       它被视为一个句子的结束，不会与下一个字幕合并。
                       默认为 ",，.。?？!！;；"。

        Returns:
            List[Subtitle]: 合并后的 Subtitle 对象列表。
        """
        if not subtitles:
            return []

        # 确保字幕按时间顺序排列
        sorted_subtitles = sorted(subtitles, key=lambda s: s.start)

        # 使用滑动窗口方法进行合并
        result = []
        window_start = 0

        for i in range(len(sorted_subtitles)):
            current_content = sorted_subtitles[i].content.strip()

            # 检查当前字幕是否以标点符号结尾
            ends_with_punct = False
            if current_content and current_content[-1] in punct_end:
                ends_with_punct = True

            # 如果当前字幕以标点结尾或是最后一个字幕，则合并窗口内的所有字幕
            if ends_with_punct or i == len(sorted_subtitles) - 1:
                # 合并窗口内的所有字幕
                if window_start <= i:
                    merged_subtitle = self._merge_subtitles_in_window(
                        sorted_subtitles[window_start : i + 1]
                    )
                    result.append(merged_subtitle)
                    window_start = i + 1

        return result

    def _merge_subtitles_in_window(self, subtitles: List[Subtitle]) -> Subtitle | None:
        """合并窗口内的所有字幕"""
        if not subtitles:
            return None

        if len(subtitles) == 1:
            return subtitles[0]

        # 合并内容
        merged_content = " ".join([s.content.strip() for s in subtitles])

        # 使用第一个字幕的开始时间和最后一个字幕的结束时间
        start_time = subtitles[0].start
        end_time = subtitles[-1].end

        # 保留第一个字幕的其他属性
        return Subtitle(
            index=None,
            start=start_time,
            end=end_time,
            content=merged_content,
            proprietary=subtitles[0].proprietary,
        )
