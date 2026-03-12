from __future__ import annotations

from typing import Callable, Dict

from ..ops_models import ProviderEntry
from ..providers.base import ProviderAdapter
from ..providers.cli_account import CliAccountAdapter
from ..providers.openai_compat import OpenAICompatAdapter

OPENAI_COMPAT_ADAPTER_TYPES = {
    "custom_openai_compatible",
    "ollama_local",
    "sglang",
    "lm_studio",
    "openai",
    "codex",
    "groq",
    "openrouter",
    "anthropic",
    "claude",
    "google",
    "mistral",
    "cohere",
    "deepseek",
    "qwen",
    "moonshot",
    "zai",
    "minimax",
    "baidu",
    "tencent",
    "bytedance",
    "iflytek",
    "01-ai",
    "together",
    "fireworks",
    "replicate",
    "huggingface",
    "azure-openai",
    "aws-bedrock",
    "vertex-ai",
    "vllm",
    "llama-cpp",
    "tgi",
}

DEFAULT_BASE_URLS: Dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "codex": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "claude": "https://api.anthropic.com/v1",
    "google": "https://generativelanguage.googleapis.com/v1beta/openai",
    "mistral": "https://api.mistral.ai/v1",
    "cohere": "https://api.cohere.ai/compatibility/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "moonshot": "https://api.moonshot.cn/v1",
    "zai": "https://api.z.ai/api/paas/v4",
    "minimax": "https://api.minimax.chat/v1",
    "baidu": "https://qianfan.baidubce.com/v2",
    "tencent": "https://api.lkeap.cloud.tencent.com/v1",
    "bytedance": "https://ark.cn-beijing.volces.com/api/v3",
    "iflytek": "https://spark-api-open.xf-yun.com/v1",
    "01-ai": "https://api.lingyiwanwu.com/v1",
    "together": "https://api.together.xyz/v1",
    "fireworks": "https://api.fireworks.ai/inference/v1",
    "huggingface": "https://router.huggingface.co/v1",
    "sglang": "http://localhost:30000/v1",
    "lm_studio": "http://localhost:1234/v1",
}


def build_provider_adapter(
    *,
    entry: ProviderEntry,
    canonical_type: str,
    resolve_secret: Callable[[ProviderEntry], str | None],
) -> ProviderAdapter:
    if canonical_type in {"codex", "claude"} and str(entry.auth_mode or "").strip().lower() == "account":
        binary = "codex" if canonical_type == "codex" else "claude"
        return CliAccountAdapter(binary=binary)

    if canonical_type in OPENAI_COMPAT_ADAPTER_TYPES:
        if not entry.base_url:
            base_url = DEFAULT_BASE_URLS.get(canonical_type)
            if not base_url:
                raise ValueError(f"{canonical_type} provider missing base_url")
        else:
            base_url = entry.base_url
        return OpenAICompatAdapter(
            base_url=base_url,
            model=entry.model,
            api_key=resolve_secret(entry),
        )

    raise ValueError(f"Unsupported provider type: {entry.type}")
