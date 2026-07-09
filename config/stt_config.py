"""
STT Provider Configuration Loader
================================
Dead-simple provider switching. To switch providers, just change STT_PROVIDER env var
or edit config/stt_providers.json active_provider field.

Usage:
    from stt_config import get_stt_config, get_provider

    config = get_stt_config()           # get active provider config
    fallback = get_provider("deepgram")  # get specific provider config
    chain = get_fallback_chain()         # get fallback chain
"""

import json
import os
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path(__file__).parent / "stt_providers.json"


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_active_provider_name() -> str:
    """Returns the name of the currently active STT provider."""
    config = _load_config()
    return config.get("active_provider", "speechmatics")


def get_stt_config(provider: Optional[str] = None) -> dict:
    """
    Get the config for a provider.
    If provider is None, returns the active (default) provider config.
    """
    config = _load_config()
    providers = config.get("providers", {})

    target = provider or os.environ.get("STT_PROVIDER") or config.get("active_provider")

    if target not in providers:
        raise ValueError(
            f"Unknown STT provider: '{target}'. "
            f"Available: {list(providers.keys())}"
        )

    prov = providers[target]

    # Merge in provider-level defaults
    return {
        "provider_name": target,
        "is_default": prov.get("default", False),
        **prov,
    }


def get_provider(name: str) -> dict:
    """Get a specific provider by name, regardless of which is active."""
    return get_stt_config(provider=name)


def get_fallback_chain() -> list[str]:
    """Returns the configured fallback chain, e.g. ['speechmatics', 'deepgram']"""
    config = _load_config()
    return config.get("fallback_chain", ["speechmatics"])


def get_n8n_http_config(provider: Optional[str] = None) -> dict:
    """
    Returns the HTTP configuration needed to call the provider from n8n.
    Includes:
      - method, endpoint, headers, body_template, query_params
    """
    prov = get_stt_config(provider)

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
    Returns the new active config.
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

    return get_stt_config(name)


# ── Convenience display ──────────────────────────────────────────────────────

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
            "diarization": prov.get("features", {}).get("diarization", False),
            "free_tier_minutes": free.get("minutes_per_month", 0),
            "free_tier_unlimited": free.get("unlimited", False),
            "price_per_minute": pricing.get("per_minute", 0),
            "note": free.get("note", ""),
        })
    return result


if __name__ == "__main__":
    import pprint

    print("=== Active Provider ===")
    pprint.pprint(get_stt_config())

    print("\n=== All Providers ===")
    pprint.pprint(list_providers())

    print("\n=== n8n HTTP Config (active) ===")
    pprint.pprint(get_n8n_http_config())
