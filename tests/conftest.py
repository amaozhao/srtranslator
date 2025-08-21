"""pytest 配置文件，用于设置测试环境并提供共享 fixtures。"""

import pathlib
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from translator.services.subtitle.parser import Subtitle

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def make_sub():

    def _make(idx, start_s, end_s, text):
        return Subtitle(
            index=idx,
            start=timedelta(seconds=start_s),
            end=timedelta(seconds=end_s),
            content=text,
        )

    return _make


@pytest.fixture
def load_test_srt():
    path = pathlib.Path(__file__).parent / "test.srt"
    return path.read_text(encoding="utf-8")
