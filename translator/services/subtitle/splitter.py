from typing import List
import tiktoken

from .parser import Subtitle


class SubtitleSplitter:
    """字幕文件分割"""

    def __init__(self, encoder: str = "cl100k_base"):
        """
        初始化 SubtitleService

        Args:
            encoder: 用于 token 计数的编码模型名称，
                     默认为 "cl100k_base" (用于 GPT-3.5/4)。
                     你可以根据需要更改为其他 tiktoken 支持的编码
                     例如 "p50k_base" 或 "gpt2"
        """
        try:
            self._tokenizer = tiktoken.get_encoding(encoder)
        except ValueError:
            raise ValueError(f"无效的 tiktoken 编码名称: {encoder}")

    def _count_tokens(self, text: str) -> int:
        """
        使用 tiktoken 计算给定文本的 token 数量。

        Args:
            text: 要计算 token 数量的文本。对于 Subtitle 对象，应该传入其 SRT 格式的字符串表示。

        Returns:
            int: 文本的 token 数量。
        """
        return len(self._tokenizer.encode(text))

    def _is_sentence_ender(self, char: str) -> bool:
        """检查字符是否是句子结束标点。"""
        return char in {".", "?", "!", "。", "？", "！"}

    def split_subtitles(
        self, subtitles: List[Subtitle], max_tokens: int = 2000
    ) -> List[List[Subtitle]]:
        """
        根据指定的 token 数量上限，将字幕列表切分成多个子列表（字幕块）。
        每个字幕块包含一个或多个完整的字幕
        且总 token 数（包括 SRT 格式的索引、时间戳和内容）不超过 max_tokens。
        同时确保每个块的最后一条字幕是一个完整的句子（以句子结束符结尾）。

        Args:
            subtitles: 原始 Subtitle 对象的列表。
            max_tokens: 每个字幕块允许的最大 token 数量。

        Returns:
            List[List[Subtitle]]: 包含多个字幕块的列表，每个字幕块是一个 Subtitle 列表。
        """
        if not subtitles or max_tokens <= 0:
            return []

        chunks: List[List[Subtitle]] = []
        current: List[Subtitle] = []
        current_tokens = 0

        # Greedy accumulation: add subtitles until adding the next one would
        # exceed max_tokens, then flush current chunk.
        for sub in subtitles:
            sub_srt = sub.to_srt()
            sub_tokens = self._count_tokens(sub_srt)

            # If a single subtitle exceeds the budget, emit it as its own
            # chunk.
            if sub_tokens > max_tokens:
                if current:
                    chunks.append(current)
                    current = []
                    current_tokens = 0
                chunks.append([sub])
                continue

            # If adding this subtitle would exceed the budget, flush current.
            if current and (current_tokens + sub_tokens) > max_tokens:
                chunks.append(current)
                current = [sub]
                current_tokens = sub_tokens
            else:
                current.append(sub)
                current_tokens += sub_tokens

        if current:
            chunks.append(current)

        # Post-process: merge very small chunks (e.g. length 1) with neighbors to
        # avoid many tiny chunks. Heuristic: ensure each chunk has at least
        # min_items or merge with previous when possible.
        min_items = 3
        merged: List[List[Subtitle]] = []
        for c in chunks:
            if not merged:
                merged.append(c)
                continue
            if len(c) < min_items:
                # try to merge into previous chunk if token budget allows
                prev = merged[-1]
                combined_tokens = self._count_tokens(
                    "".join(s.to_srt() for s in prev + c)
                )
                if combined_tokens <= max_tokens:
                    merged[-1] = prev + c
                else:
                    # otherwise, try to merge with next by appending here
                    merged.append(c)
            else:
                merged.append(c)

        return merged
