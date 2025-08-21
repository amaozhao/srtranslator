from datetime import timedelta

from translator.services.subtitle.merger import SubtitleMerger


class TestSubtitleMerger:
    def test_merge_short_pause(self, make_sub):
        subs = [
            make_sub(1, 0, 1, "Hello"),
            make_sub(2, 1.2, 2, "world"),
        ]
        merged = SubtitleMerger().merge(subs, max_pause=timedelta(seconds=1))
        assert len(merged) == 1

    def test_merge_respects_punctuation(self, make_sub):
        subs = [
            make_sub(1, 0, 1, "Hello."),
            make_sub(2, 1.1, 2, "world"),
        ]
        merged = SubtitleMerger().merge(
            subs, max_pause=timedelta(seconds=1), punct_end=".,"
        )
        assert len(merged) == 2
