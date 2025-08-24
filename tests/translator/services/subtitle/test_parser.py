import pathlib
from datetime import timedelta

import pytest

import translator.services.subtitle.parser as pmod


TEST_SRT = pathlib.Path(__file__).parents[3] / "tests" / "test.srt"


def load_test_srt():
    return TEST_SRT.read_text(encoding="utf-8")


class TestSubtitleParser:
    def test_parse_basic(self, load_test_srt):
        parser = pmod.SubtitleParser()
        subs = parser.parse(load_test_srt)
        assert isinstance(subs, list)
        assert len(subs) > 0

        first = subs[0]
        assert hasattr(first, "start")
        assert hasattr(first, "end")
        assert hasattr(first, "content")
        # 简单时间断言（第一个字幕从 0 开始）
        assert first.start == timedelta(hours=0, minutes=0, seconds=0, milliseconds=0)

    def test_parse_invalid_timestamp_raises(self):
        parser = pmod.SubtitleParser()
        with pytest.raises(pmod.TimestampParseError):
            parser._parse_timestamp("not-a-timestamp")

    def test_compose_roundtrip(self, load_test_srt):
        parser = pmod.SubtitleParser()
        subs = parser.parse(load_test_srt)
        composed = parser.compose(subs, reindex=False)
        # 重新解析合成结果，数量保持一致
        subs2 = parser.parse(composed)
        assert len(subs2) == len(subs)
