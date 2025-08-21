import pytest

from translator.agents.workflow import SubtitleWorkflow
from agno.workflow import RunResponse


@pytest.mark.asyncio
class TestSubtitleWorkflow:
    async def test_arun_successful_flow(self, monkeypatch, tmp_path):
        # 构建一个简单的 SRT 内容
        srt_content = """1
00:00:01,000 --> 00:00:02,000
Hello

2
00:00:03,000 --> 00:00:04,000
World
"""

        in_file = tmp_path / "in.srt"
        out_file = tmp_path / "out.srt"
        in_file.write_text(srt_content)

        wf = SubtitleWorkflow(max_tokens=100)

        # mock SrtService.split: return a single chunk (list of Subtitle objects)
        async def fake_split(path, max_tokens):
            # reuse parser to parse and return a single chunk
            subs = wf.srt_service.parser.parse(srt_content)
            return [subs]

        monkeypatch.setattr(wf.srt_service, "split", fake_split)

        # mock proofer and translator agents
        class DummyResp:
            def __init__(self, content):
                self.content = content

        async def fake_proofer_arun(content):
            return DummyResp(content)

        async def fake_translator_arun(content):
            return DummyResp(content)

        # monkeypatch get_proofer and get_translator to return dummy agents
        class DummyAgent:
            def __init__(self, fn):
                self._fn = fn

            async def arun(self, content):
                return await self._fn(content)

        import translator.agents.proofer as proofer_mod
        import translator.agents.translator as translator_mod

        monkeypatch.setattr(
            proofer_mod,
            "get_proofer",
            lambda: DummyAgent(lambda c: fake_proofer_arun(c)),
        )
        monkeypatch.setattr(
            translator_mod,
            "get_translator",
            lambda: DummyAgent(lambda c: fake_translator_arun(c)),
        )

        # mock write to avoid actual file IO
        async def fake_write(path, subtitles):
            # ensure subtitles is a list
            assert isinstance(subtitles, list)
            return str(path)

        monkeypatch.setattr(wf.srt_service, "write", fake_write)

        responses = []
        async for resp in wf.arun(str(in_file), str(out_file)):
            assert isinstance(resp, RunResponse)
            responses.append(resp)

        # 最后的响应应包含完成的信息
        assert any("全部完成" in r.content for r in responses)

    async def test_arun_empty_split(self, monkeypatch, tmp_path):
        wf = SubtitleWorkflow(max_tokens=100)

        async def fake_split_empty(path, max_tokens):
            return []

        monkeypatch.setattr(wf.srt_service, "split", fake_split_empty)

        responses = []
        async for resp in wf.arun(
            "doesnotmatter.srt",
            str(tmp_path / "out.srt"),
        ):
            responses.append(resp)

        assert any("字幕分块失败" in r.content for r in responses)

    async def test_process_chunk_translate_fallback(self, monkeypatch):
        # 测试 translator 输出无效时回退到 proofed_content
        wf = SubtitleWorkflow(max_tokens=100)

        # fake parse/compose behavior
        srt = "1\n00:00:01,000 --> 00:00:02,000\nHello\n"
        # prepare parser.compose to return the srt string
        monkeypatch.setattr(wf.srt_service.parser, "compose", lambda x: srt)

        class DummyResp:
            def __init__(self, content):
                self.content = content

        async def fake_proofer_arun(content):
            # return valid srt
            return DummyResp(srt)

        async def fake_translator_arun(content):
            # return invalid content (no srt), should fallback
            return DummyResp("I am not SRT")

        import translator.agents.proofer as proofer_mod
        import translator.agents.translator as translator_mod

        monkeypatch.setattr(
            proofer_mod,
            "get_proofer",
            lambda: type("A", (), {"arun": fake_proofer_arun})(),
        )
        monkeypatch.setattr(
            translator_mod,
            "get_translator",
            lambda: type("A", (), {"arun": fake_translator_arun})(),
        )

        # run _process_chunk directly
        processed = await wf._process_chunk(srt, "en", "zh")
        # translator 返回无效，应回退到 proofed_content（即 srt）
        assert "Hello" in processed
