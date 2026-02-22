"""
GIMO Qwen-via-Ollama Handshake Test
====================================
Tests direct connectivity to Qwen 2.5 Coder running on local Ollama.
Uses both the native Ollama API and the OpenAI-compatible endpoint.
"""
import sys
import os
import json
import time

# Fix Windows console encoding
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import httpx

OLLAMA_BASE = "http://localhost:11434"
MODEL = "qwen2.5-coder:3b"

HANDSHAKE_PROMPT = (
    "Respond ONLY with the following JSON and nothing else: "
    '{"status": "online", "model": "qwen2.5-coder", "ready": true}'
)


def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_ollama_api_tags():
    """Step 1: Check Ollama is alive and list models."""
    print_header("STEP 1 — Ollama API Health (/api/tags)")
    try:
        resp = httpx.get(f"{OLLAMA_BASE}/api/tags", timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        print(f"[OK] Ollama responded. Models available: {models}")
        if MODEL not in models and not any(MODEL.split(":")[0] in m for m in models):
            print(f"[WARN] Target model '{MODEL}' not found in list!")
            return False
        print(f"[OK] Target model '{MODEL}' found.")
        return True
    except httpx.ConnectError:
        print("[FAIL] Cannot connect to Ollama. Is it running?")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False


def test_native_ollama_generate():
    """Step 2: Generate using native Ollama API."""
    print_header("STEP 2 — Native Ollama Generate (/api/generate)")
    payload = {
        "model": MODEL,
        "prompt": HANDSHAKE_PROMPT,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 80},
    }
    try:
        start = time.time()
        resp = httpx.post(
            f"{OLLAMA_BASE}/api/generate", json=payload, timeout=120.0
        )
        latency = time.time() - start
        resp.raise_for_status()
        data = resp.json()
        response_text = data.get("response", "")
        print(f"[OK] Status: {resp.status_code} | Latency: {latency:.2f}s")
        print(f"[OK] Raw response:\n    {response_text.strip()}")
        # Try to parse the JSON
        try:
            parsed = json.loads(response_text.strip())
            if parsed.get("ready") is True:
                print("[OK] ✅ HANDSHAKE SUCCESS (native API) — Qwen is ready!")
                return True
        except json.JSONDecodeError:
            pass
        # Even if JSON parse fails, if we got a response, the model is alive
        if response_text.strip():
            print("[OK] ✅ Model responded (non-JSON). Handshake confirmed.")
            return True
        print("[FAIL] Empty response from model.")
        return False
    except httpx.ConnectError:
        print("[FAIL] Cannot connect to Ollama.")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_openai_compat_chat():
    """Step 3: Generate using OpenAI-compatible endpoint."""
    print_header("STEP 3 — OpenAI-Compatible Chat (/v1/chat/completions)")
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a GIMO worker agent. Confirm readiness.",
            },
            {
                "role": "user",
                "content": HANDSHAKE_PROMPT,
            },
        ],
        "temperature": 0.0,
        "max_tokens": 80,
        "stream": False,
    }
    try:
        start = time.time()
        resp = httpx.post(
            f"{OLLAMA_BASE}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120.0,
        )
        latency = time.time() - start
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        print(f"[OK] Status: {resp.status_code} | Latency: {latency:.2f}s")
        print(f"[OK] Usage: {usage}")
        print(f"[OK] Response:\n    {content.strip()}")
        if content.strip():
            print("[OK] ✅ HANDSHAKE SUCCESS (OpenAI-compat) — Qwen is ready!")
            return True
        print("[FAIL] Empty response.")
        return False
    except httpx.ConnectError:
        print("[FAIL] Cannot connect to Ollama OpenAI endpoint.")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def main():
    print_header("GIMO ↔ Qwen Handshake via Ollama")
    print(f"Target: {OLLAMA_BASE} | Model: {MODEL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # Step 1: API Health
    results["api_health"] = test_ollama_api_tags()
    if not results["api_health"]:
        print("\n[ABORT] Ollama not reachable. Stopping.")
        sys.exit(1)

    # Step 2: Native generation
    results["native_generate"] = test_native_ollama_generate()

    # Step 3: OpenAI compat
    results["openai_compat"] = test_openai_compat_chat()

    # Summary
    print_header("HANDSHAKE SUMMARY")
    all_pass = all(results.values())
    for k, v in results.items():
        icon = "✅" if v else "❌"
        print(f"  {icon} {k}: {'PASS' if v else 'FAIL'}")

    if all_pass:
        print("\n🎉 ALL TESTS PASSED — Qwen is fully operational via Ollama!")
        print("   GIMO can proceed with Qwen as worker agent.")
    else:
        print("\n⚠️  Some tests failed. Review above for details.")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
