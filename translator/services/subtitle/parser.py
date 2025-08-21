import functools
import re
from datetime import timedelta
from typing import List


# 常量和正则表达式模式
RGX_TIMESTAMP_MAGNITUDE_DELIM = r"[,.:，．。：]"
RGX_TIMESTAMP_FIELD = r"[0-9]+"
RGX_TIMESTAMP_FIELD_OPTIONAL = r"[0-9]*"
RGX_TIMESTAMP = "".join(
    [
        RGX_TIMESTAMP_MAGNITUDE_DELIM.join([RGX_TIMESTAMP_FIELD] * 3),
        RGX_TIMESTAMP_MAGNITUDE_DELIM,
        "?",
        RGX_TIMESTAMP_FIELD_OPTIONAL,
    ]
)
RGX_TIMESTAMP_PARSEABLE = r"^{}$".format(
    "".join(
        [
            RGX_TIMESTAMP_MAGNITUDE_DELIM.join(["(" + RGX_TIMESTAMP_FIELD + ")"] * 3),
            RGX_TIMESTAMP_MAGNITUDE_DELIM,
            "?",
            "(",
            RGX_TIMESTAMP_FIELD_OPTIONAL,
            ")",
        ]
    )
)
RGX_INDEX = r"-?[0-9]+\.?[0-9]*"
RGX_PROPRIETARY = r"[^\r\n]*"
RGX_CONTENT = r".*?"
RGX_POSSIBLE_CRLF = r"\r?\n"

TS_REGEX = re.compile(RGX_TIMESTAMP_PARSEABLE)
MULTI_WS_REGEX = re.compile(r"\n\n+")
SRT_REGEX = re.compile(
    (
        r"\s*(?:({idx})\s*{eof})?({ts}) *-[ -] *> *({ts}) ?({proprietary}"
        r")(?:{eof}|\Z)({content})"
        r"(?:{eof}|\Z)(?:{eof}|\Z|(?=(?:{idx}\s*{eof}{ts})))"
        r"(?=(?:(?:{idx}\s*{eof})?{ts}|\Z))"
    ).format(
        idx=RGX_INDEX,
        ts=RGX_TIMESTAMP,
        proprietary=RGX_PROPRIETARY,
        content=RGX_CONTENT,
        eof=RGX_POSSIBLE_CRLF,
    ),
    re.DOTALL,
)

SECONDS_IN_HOUR = 3600
SECONDS_IN_MINUTE = 60
HOURS_IN_DAY = 24
MICROSECONDS_IN_MILLISECOND = 1000


@functools.total_ordering
class Subtitle:
    """
    单个字幕的元数据。
    """

    def __init__(self, index, start, end, content, proprietary=""):
        self.index = index
        self.start = start
        self.end = end
        self.content = content
        self.proprietary = proprietary

    def __hash__(self):
        return hash(frozenset(vars(self).items()))

    def __eq__(self, other):
        return isinstance(other, Subtitle) and vars(other) == vars(self)

    def __lt__(self, other):
        return (self.start, self.end, self.index) < (
            other.start,
            other.end,
            other.index,
        )

    def __repr__(self):
        var_items = vars(self).items()
        item_list = ", ".join(f"{k}={v!r}" for k, v in var_items)
        return f"{type(self).__name__}({item_list})"

    def to_srt(self, strict=True, eol="\n"):
        """
        将当前 Subtitle 对象转换为 SRT 块。
        """
        output_content = self.content
        output_proprietary = self.proprietary

        if output_proprietary:
            output_proprietary = " " + output_proprietary

        if strict:
            output_content = self._clean_content(output_content)

        if eol is None:
            eol = "\n"
        elif eol != "\n":
            output_content = output_content.replace("\n", eol)

        template = "{idx}{eol}{start} --> {end}{prop}{eol}{content}{eol}{eol}"
        return template.format(
            idx=self.index or 0,
            start=self._format_timestamp(self.start),
            end=self._format_timestamp(self.end),
            prop=output_proprietary,
            content=output_content,
            eol=eol,
        )

    def _clean_content(self, content):
        # 严格模式下，除了移除空行，还要确保每行内容都去除前后空格
        lines = content.split("\n")
        stripped_lines = [line.strip() for line in lines]
        # 移除空行（即只包含空白字符的行在strip后会变成空字符串）
        legal_content_lines = [line for line in stripped_lines if line]
        return "\n".join(legal_content_lines)

    def _format_timestamp(self, timedelta_timestamp):
        hrs, secs_remainder = divmod(timedelta_timestamp.seconds, SECONDS_IN_HOUR)
        hrs += timedelta_timestamp.days * HOURS_IN_DAY
        mins, secs = divmod(secs_remainder, SECONDS_IN_MINUTE)
        msecs = timedelta_timestamp.microseconds // MICROSECONDS_IN_MILLISECOND
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"


class SRTParseError(Exception):
    """
    解析 SRT 块时出错。
    """

    def __init__(self, expected_start, actual_start, unmatched_content):
        message = (
            "Expected contiguous start of match or "
            f"end of input at char {expected_start}, "
            f"but started at char {actual_start} "
            f"(unmatched content: {unmatched_content!r})"
        )
        super().__init__(message)
        self.expected_start = expected_start
        self.actual_start = actual_start
        self.unmatched_content = unmatched_content


class TimestampParseError(ValueError):
    """
    解析 SRT 时间戳时出错。
    """

    pass


class SubtitleParser:

    def parse(self, srt_data: str, ignore_errors: bool = False) -> List[Subtitle]:
        """
        将 SRT 格式的字符串或文件对象解析为 Subtitle 对象列表。
        解析时会自动删除字幕内容每行前后的所有空格。

        :param srt_data: SRT 格式的字幕内容，可以是字符串或文件对象。
        :param ignore_errors: 如果为 True，则忽略解析错误并继续。
        :returns: Subtitle 对象的列表。
        :raises SRTParseError: 如果匹配不连续且 ignore_errors 为 False。
        """
        expected_start = 0
        subtitles = []

        for match in SRT_REGEX.finditer(srt_data):
            actual_start = match.start()
            self._check_continuity(
                srt_data, expected_start, actual_start, ignore_errors
            )
            (
                raw_index,
                raw_start,
                raw_end,
                proprietary,
                content,
            ) = match.groups()

            processed_content_lines = [
                line.strip() for line in content.replace("\r\n", "\n").split("\n")
            ]
            content_cleaned_per_line = "\n".join(processed_content_lines).strip()

            try:
                raw_index = int(raw_index)
            except (ValueError, TypeError):
                raw_index = None

            subtitles.append(
                Subtitle(
                    index=raw_index,
                    start=self._parse_timestamp(raw_start),
                    end=self._parse_timestamp(raw_end),
                    content=content_cleaned_per_line,
                    proprietary=proprietary or "",
                )
            )
            expected_start = match.end()

        self._check_continuity(srt_data, expected_start, len(srt_data), ignore_errors)
        return subtitles

    def compose(
        self,
        subtitles: List[Subtitle],
        reindex: bool = True,
        start_index: int = 1,
        strict: bool = True,
        eol: str | None = None,
    ) -> str:
        """
        将 Subtitle 对象列表合成 SRT 格式的字符串。

        :param subtitles: Subtitle 对象的列表或迭代器。
        :param reindex: 是否根据开始时间重新索引字幕。
        :param start_index: 如果重新索引，起始索引。
        :param strict: 是否启用严格模式（移除内容中的空行）。
        :param eol: 使用的行结束符（默认为 "\\n"）。
        :returns: SRT 格式的字符串。
        """
        if reindex:
            processed_subtitles = []
            for i, subtitle in enumerate(sorted(subtitles), start=start_index):
                new_subtitle = Subtitle(
                    index=i,
                    start=subtitle.start,
                    end=subtitle.end,
                    content=subtitle.content,
                    proprietary=subtitle.proprietary,
                )
                processed_subtitles.append(new_subtitle)
            subtitles_to_compose = processed_subtitles
        else:
            subtitles_to_compose = subtitles

        return "".join(
            subtitle.to_srt(strict=strict, eol=eol or "\n")
            for subtitle in subtitles_to_compose
        )

    def _parse_timestamp(self, timestamp: str) -> timedelta:
        match = TS_REGEX.match(timestamp)
        if match is None:
            raise TimestampParseError(f"无法解析时间戳: {timestamp}")
        hrs, mins, secs, msecs = [int(m) if m else 0 for m in match.groups()]
        return timedelta(hours=hrs, minutes=mins, seconds=secs, milliseconds=msecs)

    def _check_continuity(
        self, srt: str, expected_start: int, actual_start: int, warn_only: bool
    ):
        if expected_start != actual_start:
            unmatched_content = srt[expected_start:actual_start]
            if expected_start == 0 and (
                unmatched_content.isspace() or unmatched_content == "\ufeff"
            ):
                return
            if not warn_only:
                raise SRTParseError(expected_start, actual_start, unmatched_content)
