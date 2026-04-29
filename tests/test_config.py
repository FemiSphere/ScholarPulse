from pathlib import Path

from literature_digest.config import load_config
from literature_digest.llm import LLMError
from literature_digest.llm.openai_compatible import OpenAICompatibleClient


def test_load_config_merges_external_llm_config(tmp_path, monkeypatch):
    llm_dir = tmp_path / "config" / "llm"
    llm_dir.mkdir(parents=True)
    (llm_dir / "deepseek.local.yaml").write_text(
        """
provider: "openai_compatible"
timeout_seconds: 300
max_output_tokens: 4000
openai_compatible:
  base_url: "https://api.deepseek.com"
  api_key_env: "DEEPSEEK_API_KEY"
  model: "deepseek-v4-flash"
  extra_body:
    thinking:
      type: "disabled"
""",
        encoding="utf-8",
    )
    config_path = tmp_path / "config.local.yaml"
    config_path.write_text(
        """
llm:
  config_path: "config/llm/deepseek.local.yaml"
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    config = load_config(config_path)

    assert config["llm"]["provider"] == "openai_compatible"
    assert config["llm"]["timeout_seconds"] == 300
    assert config["llm"]["openai_compatible"]["model"] == "deepseek-v4-flash"
    assert config["llm"]["openai_compatible"]["extra_body"]["thinking"]["type"] == "disabled"


def test_openai_compatible_rejects_api_key_as_env_name():
    client = OpenAICompatibleClient(
        base_url="https://api.deepseek.com",
        api_key_env="sk-testsecret1234567890",
        model="deepseek-v4-flash",
    )

    try:
        client.complete("hello")
    except LLMError as exc:
        message = str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected LLMError")

    assert "looks like an API key" in message
    assert "sk-testsecret" not in message
