import json
import importlib
import builtins
import shutil
from pathlib import Path

import pytest


def load_bot_with_config(monkeypatch, tmp_path, config_data):
    config_file = tmp_path / "config.json"

    config_file.write_text(
        json.dumps(config_data)
    )

    monkeypatch.chdir(tmp_path)

    import bot

    return importlib.reload(bot)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_clips_dir():
    yield

    for root_name in ("clips", "vods"):
        test_channel_dir = Path(root_name) / "testchannel"
        if test_channel_dir.exists():
            shutil.rmtree(test_channel_dir)

        root_dir = Path(root_name)
        if root_dir.is_dir() and not any(root_dir.iterdir()):
            root_dir.rmdir()


builtins.load_bot_with_config = load_bot_with_config