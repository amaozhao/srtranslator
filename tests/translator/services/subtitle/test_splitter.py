import pytest

from translator.services.subtitle.splitter import SubtitleSplitter


class TestSubtitleSplitter:
    def test_splitter_basic(self, make_sub):
        splitter = SubtitleSplitter(encoder="cl100k_base")
        subs = [
            make_sub(1, 0, 1, "Hello world."),
            make_sub(2, 1, 2, "Another line."),
        ]
        chunks = splitter.split_subtitles(subs, max_tokens=1000)
        assert isinstance(chunks, list)
        assert len(chunks) >= 1

    def test_splitter_invalid_encoder(self):
        with pytest.raises(ValueError):
            SubtitleSplitter(encoder="nonexistent-encoder")
