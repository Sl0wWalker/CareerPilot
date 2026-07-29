from careerpilot.models.global_platform import ModelRoutingPolicy


def routing_decision(policy: ModelRoutingPolicy, local_available: bool) -> dict:
    if policy.local_first and local_available:
        provider = "ollama"
        reason = "local provider available and policy is local-first"
    elif policy.allow_cloud_fallback:
        provider = policy.preferred_provider
        reason = "local provider unavailable; approved cloud fallback selected"
    else:
        provider = None
        reason = "no privacy-compliant provider is currently available"
    return {
        "provider": provider,
        "model": policy.preferred_model if provider else None,
        "reason": reason,
        "privacy_class": policy.privacy_class,
        "cloud_fallback_allowed": policy.allow_cloud_fallback,
    }
