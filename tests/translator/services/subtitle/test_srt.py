from datetime import timedelta

from translator.services.subtitle.srt import Subtitle


class TestSRTModel:
    def test_subtitle_to_srt_and_formatting(self):
        s = Subtitle(
            index=1,
            start=timedelta(seconds=0),
            end=timedelta(seconds=1, milliseconds=500),
            content=" hello \n\n world ",
        )
        out = s.to_srt()
        assert "00:00:00,000 --> 00:00:01,500" in out
        # 严格模式会去掉空行并修剪每行
        assert "hello" in out
        assert "world" in out

    def test_clean_content_keeps_lines(self):
        s = Subtitle(
            index=1,
            start=timedelta(0),
            end=timedelta(seconds=1),
            content=" a\n\n b \n ",
        )
        cleaned = s._clean_content(s.content)
        assert cleaned == "a\nb"
