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

        chunks = []
        current_chunk = []
        pending_subs = []  # 存储未完成句子的字幕

        for sub in subtitles:
            # 计算当前字幕的 SRT 格式字符串的 token 数量
            sub_srt = sub.to_srt()
            sub_tokens = self._count_tokens(sub_srt)

            # 如果单个字幕就超过了最大 token 限制，则单独作为一个块
            if sub_tokens > max_tokens:
                # 先处理之前积累的未完成句子
                if pending_subs:
                    if current_chunk:
                        chunks.append(current_chunk)
                    chunks.append(pending_subs)
                    pending_subs = []
                    current_chunk = []

                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []

                chunks.append([sub])
                continue

            # 检查字幕内容是否以句子结束符结尾
            content = sub.content.strip()
            is_sentence_end = (
                content and self._is_sentence_ender(content[-1]) if content else False
            )

            # 将当前字幕添加到待处理列表
            pending_subs.append(sub)

            # 检查添加当前待处理字幕后是否会超过 token 限制
            all_subs = current_chunk + pending_subs
            all_srt = "".join(s.to_srt() for s in all_subs)
            all_tokens = self._count_tokens(all_srt)

            # 如果添加后不超过限制且当前字幕是句子结束，则合并到当前块
            if all_tokens <= max_tokens:
                if is_sentence_end:
                    current_chunk.extend(pending_subs)
                    pending_subs = []
            else:
                # 超过限制，需要开始新块
                if current_chunk:
                    chunks.append(current_chunk)

                # 如果待处理字幕本身不超过限制，则作为新块的开始
                pending_srt = "".join(s.to_srt() for s in pending_subs)
                pending_tokens = self._count_tokens(pending_srt)

                if pending_tokens <= max_tokens:
                    if is_sentence_end:
                        chunks.append(pending_subs)
                        pending_subs = []
                        current_chunk = []
                    else:
                        current_chunk = pending_subs
                        pending_subs = []
                else:
                    # 待处理字幕太大，需要进一步拆分
                    # 这种情况应该很少发生，因为我们已经处理了单个字幕超限的情况
                    for p_sub in pending_subs:
                        p_srt = p_sub.to_srt()
                        p_tokens = self._count_tokens(p_srt)

                        if (
                            current_chunk
                            and self._count_tokens(
                                "".join(s.to_srt() for s in current_chunk)
                            )
                            + p_tokens
                            > max_tokens
                        ):
                            chunks.append(current_chunk)
                            current_chunk = [p_sub]
                        else:
                            current_chunk.append(p_sub)

                    pending_subs = []

        # 处理剩余的字幕
        if pending_subs:
            if (
                current_chunk
                and self._count_tokens(
                    "".join(s.to_srt() for s in current_chunk + pending_subs)
                )
                <= max_tokens
            ):
                current_chunk.extend(pending_subs)
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = pending_subs

        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)

        return chunks
