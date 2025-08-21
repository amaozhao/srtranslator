from translator.services.subtitle.connector import SubtitleConnector


class TestSubtitleConnector:
    def test_connect_empty(self):
        assert SubtitleConnector().connect([]) == []

    def test_connect_chunks(self, make_sub):
        a = make_sub(1, 0, 1, "a")
        b = make_sub(2, 1, 2, "b")
        connected = SubtitleConnector().connect([[a], [b]])
        assert len(connected) == 2
