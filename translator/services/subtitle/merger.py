from datetime import timedelta
from typing import List

from .parser import Subtitle


class SubtitleMerger:
    """字幕合并"""

    def merge(
        self,
        subtitles: List[Subtitle],
        max_pause: timedelta = timedelta(seconds=0.7),
        punct_end: str = ",，.。?？!！",
        max_dur: timedelta = timedelta(seconds=15),
    ) -> List[Subtitle]:
        """
        智能合并时间上连续或重叠的字幕条目，旨在将逻辑上属于“一句话”但被分割的字幕合并。
        合并逻辑考虑：
        1. 相邻字幕之间的时间间隔。
        2. 字幕内容是否以句子结束标点符号结尾。
        3. 合并后的字幕总时长限制。

        Args:
            subtitles: 原始 Subtitle 对象的列表。
            max_pause: 允许合并的相邻字幕之间的最大暂停时间。
                       如果字幕结束和下一个字幕开始之间的实际暂停时间超过此值，则不合并。
                       默认为 0.7 秒。
            punct_end: 严格的句子结束标点符号字符串。如果一个字幕以这些标点符号结尾，
                       它通常被视为一个句子的结束，即使时间间隔很短，也不会与下一个字幕合并。
                       可以设置为空字符串 "" 来禁用此检查。
            max_dur: 单个合并后的字幕允许的最大持续时间。
                     防止将非常长的多句话合并成一个字幕条目，这可能不利于阅读。
                     默认为 15 秒。

        Returns:
            List[Subtitle]: 合并后的 Subtitle 对象列表，其中逻辑上连续的短字幕已合并为更长的字幕。
        """
        if not subtitles:
            return []

        sorted_subtitles = sorted(subtitles, key=lambda s: s.start)

        merged_subtitles: List[Subtitle] = []

        if not sorted_subtitles:
            return []

        current_subtitle = sorted_subtitles[0]

        for next_subtitle in sorted_subtitles[1:]:
            current_content_stripped = current_subtitle.content.strip()
            ends_with_sentence_punct = False
            if punct_end:
                if (
                    current_content_stripped
                    and current_content_stripped[-1] in punct_end
                ):
                    ends_with_sentence_punct = True

            pause_duration = next_subtitle.start - current_subtitle.end
            potential_total_duration = next_subtitle.end - \
                current_subtitle.start

            should_merge = (
                not ends_with_sentence_punct
                and pause_duration <= max_pause
                and potential_total_duration <= max_dur
            )

            if should_merge:
                merged_content = (
                    current_subtitle.content.strip()
                    + " "
                    + next_subtitle.content.strip()
                )
                new_start = current_subtitle.start
                new_end = max(current_subtitle.end, next_subtitle.end)

                current_subtitle = Subtitle(
                    index=None,
                    start=new_start,
                    end=new_end,
                    content=merged_content,
                    proprietary=current_subtitle.proprietary,
                )
            else:
                merged_subtitles.append(current_subtitle)
                current_subtitle = next_subtitle

        merged_subtitles.append(current_subtitle)

        return merged_subtitles
