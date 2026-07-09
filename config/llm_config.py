"""
LLM Provider Configuration Loader
=================================
Dead-simple LLM provider switching. To switch providers, just change LLM_PROVIDER env var
or edit config/llm_providers.json active_provider field.

Usage:
    from llm_config import get_llm_config, get_provider, get_n8n_http_config

    config = get_llm_config()           # get active provider config
    anthropic = get_provider("anthropic") # get specific provider config
    chain = get_fallback_chain()          # get fallback chain
"""

import json
import os
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path(__file__).parent / "llm_providers.json"


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_active_provider_name() -> str:
    """Returns the name of the currently active LLM provider."""
    config = _load_config()
    return config.get("active_provider", "minimax")


def get_llm_config(provider: Optional[str] = None) -> dict:
    """
    Get the config for a provider.
    If provider is None, returns the active (default) provider config.
    """
    config = _load_config()
    providers = config.get("providers", {})

    target = provider or os.environ.get("LLM_PROVIDER") or config.get("active_provider")

    if target not in providers:
        raise ValueError(
            f"Unknown LLM provider: '{target}'. "
            f"Available: {list(providers.keys())}"
        )

    prov = providers[target]

    return {
        "provider_name": target,
        "is_default": prov.get("default", False),
        **prov,
    }


def get_provider(name: str) -> dict:
    """Get a specific provider by name, regardless of which is active."""
    return get_llm_config(provider=name)


def get_fallback_chain() -> list[str]:
    """Returns the configured fallback chain."""
    config = _load_config()
    return config.get("fallback_chain", ["minimax", "anthropic", "openai"])


def get_n8n_http_config(provider: Optional[str] = None) -> dict:
    """
    Returns the HTTP configuration needed to call the provider from n8n.
    """
    prov = get_llm_config(provider)

    return {
        "provider": prov["provider_name"],
        "method": prov.get("n8n_http_method", "POST"),
        "endpoint": prov.get("n8n_endpoint", ""),
        "headers": prov.get("n8n_headers", {}),
        "body_template": prov.get("n8n_body_template", {}),
        "query_params": prov.get("n8n_query_params", {}),
    }


def switch_provider(name: str) -> dict:
    """
    Switch the active provider by updating the config file.
    """
    providers = _load_config().get("providers", {})

    if name not in providers:
        raise ValueError(
            f"Unknown provider: '{name}'. Available: {list(providers.keys())}"
        )

    config = _load_config()
    config["active_provider"] = name

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    return get_llm_config(name)


def list_providers() -> list[dict]:
    """List all available providers with name, free tier, and price."""
    config = _load_config()
    result = []
    active = config.get("active_provider")

    for key, prov in config.get("providers", {}).items():
        pricing = prov.get("pricing", {})
        free = prov.get("free_tier", {})
        result.append({
            "id": key,
            "name": prov.get("name", key),
            "active": key == active,
            "function_calling": prov.get("features", {}).get("function_calling", False),
            "json_schema_output": prov.get("features", {}).get("json_schema_output", False),
            "free_tier_note": free.get("note", ""),
            "input_price_per_1m": pricing.get("input_per_1m_tokens", 0),
            "output_price_per_1m": pricing.get("output_per_1m_tokens", 0),
        })
    return result


if __name__ == "__main__":
    import pprint

    print("=== Active LLM Provider ===")
    pprint.pprint(get_llm_config())

    print("\n=== All Providers ===")
    pprint.pprint(list_providers())

    print("\n=== n8n HTTP Config (active) ===")
    pprint.pprint(get_n8n_http_config())
