import json
import importlib
import builtins

def load_bot_with_config(monkeypatch, tmp_path, config_data):
    config_file = tmp_path / "config.json"

    config_file.write_text(
        json.dumps(config_data)
    )

    monkeypatch.chdir(tmp_path)

    import bot

    return importlib.reload(bot)


builtins.load_bot_with_config = load_bot_with_config