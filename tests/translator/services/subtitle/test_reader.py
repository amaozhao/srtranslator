import pytest

from translator.services.subtitle.parser import SRTParseError
from translator.services.subtitle.reader import SubtitleReader


class TestSubtitleReader:
    """测试字幕读取。"""
    srt_path = 'tests/test.srt'
    invalid_srt = 'tests/test2.srt'

    @pytest.mark.asyncio
    async def test_read(self):
        """测试读取SRT文件。"""
        # 准备测试文件

        # 测试读取字幕
        subtitles = await SubtitleReader().read(self.srt_path)
        assert len(subtitles) > 0

    @pytest.mark.asyncio
    async def test_read_invalid_srt(self):
        """测试读取无效的SRT文件。"""

        # 测试读取无效SRT文件
        with pytest.raises(SRTParseError):
            await SubtitleReader().read(self.invalid_srt)
