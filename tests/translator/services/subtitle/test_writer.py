import asyncio

from translator.services.subtitle.writer import SubtitleWriter


class TestSubtitleWriter:
    def test_writer_save_and_write(self, tmp_path, make_sub):
        writer = SubtitleWriter()
        fp = tmp_path / "out.srt"
        composed = writer.compose([make_sub(1, 0, 1, "hi")], reindex=False)
        # test save
        loop = asyncio.get_event_loop()
        out = loop.run_until_complete(writer.save(composed, str(fp)))
        assert out == str(fp)

    def test_writer_write_file(self, tmp_path, make_sub):
        writer = SubtitleWriter()
        fp = tmp_path / "out2.srt"
        loop = asyncio.get_event_loop()
        out = loop.run_until_complete(
            writer.write(str(fp), [make_sub(1, 0, 1, "hi")]))
        assert out == str(fp)
