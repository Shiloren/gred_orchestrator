import asyncio
import sys
import os
import subprocess
from pathlib import Path

# Ensure project root is in path
sys.path.append(os.getcwd())

from tools.gimo_server.services.sub_agent_manager import SubAgentManager
from tools.gimo_server.services.provider_catalog_service import ProviderCatalogService

async def exact_proof():
    print("====================================================")
    print("GIMO EXACT PROOF: DISK-BASED DISCOVERY INDEPENDENCE")
    print("====================================================\n")

    # 1. ATTEMPT OFFICIAL CLI (Should fail if offline)
    print("[1] TESTING OFFICIAL 'ollama list' CLI...")
    try:
        # We run it synchronously for simplicity in the proof script
        res = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            print("    \u274c CLI Status: ONLINE (Cannot prove offline robustness right now)")
            print("    (Ollama auto-restarted too fast. But watch the disk scan below...)")
        else:
            print("    \u2705 CLI Status: OFFLINE (As expected, it failed)")
            print(f"    Error: {res.stderr.strip()}")
    except Exception as e:
        print(f"    Error running CLI: {e}")

    # 2. GIMO DISK-BASED SCAN (The Robust Fallback)
    print("\n[2] TESTING GIMO DISK SCAN (BYPASSING API/CLI)...")
    disk_agents = ProviderCatalogService._ollama_list_from_disk()
    if disk_agents:
        print(f"    \u2705 SUCCESS: GIMO found {len(disk_agents)} models on disk despite CLI status:")
        for m in disk_agents:
            print(f"       - {m.id}")
    else:
        print("    \u274c FAILED: GIMO could not find models on disk. Check OLLAMA_MODELS path.")

    # 3. GIMO SMART WAKE DEMO
    print("\n[3] TESTING GIMO SMART WAKE...")
    is_alive = await ProviderCatalogService._ollama_health()
    if not is_alive:
        print("    Service is OFFLINE. Triggering wake-up...")
        success = await ProviderCatalogService.ensure_ollama_ready()
        if success:
             print("    \u2705 SUCCESS: GIMO woke up Ollama successfully!")
        else:
             print("    \u274c FAILED: Could not wake up Ollama.")
    else:
        print("    Service is already ONLINE. Smart Wake skipped.")

    print("\n====================================================")

if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    asyncio.run(exact_proof())
