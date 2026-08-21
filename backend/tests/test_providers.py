from app.providers.base import RemoteModel
from app.providers.registry import is_coder_model, pick_council_models


def _m(provider: str, name: str) -> RemoteModel:
    return RemoteModel(
        id=f"{provider}/{name}",
        name=name,
        provider_id=provider,
        provider_name=provider,
        raw_name=name,
    )


def test_is_coder_model():
    assert is_coder_model("qwen2.5-coder:7b")
    assert is_coder_model("deepseek-coder-v2")
    assert not is_coder_model("llama3.2")


def test_pick_council_prefers_diversity():
    models = [
        _m("ollama", "qwen2.5-coder:7b"),
        _m("ollama", "codellama:7b"),
        _m("lmstudio", "deepseek-coder"),
        _m("localai", "llama3.2"),
        _m("jan", "mistral"),
    ]
    picked = pick_council_models(models, max_models=3)
    providers = {m.provider_id for m in picked}
    assert len(picked) == 3
    assert "ollama" in providers
    assert "lmstudio" in providers
