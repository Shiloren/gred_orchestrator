import asyncio
import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from tools.gimo_server.services.sub_agent_manager import SubAgentManager
from tools.gimo_server.services.provider_catalog_service import ProviderCatalogService
from tools.gimo_server.models import SubAgent, SubAgentConfig

async def demo_universal_activation():
    print("====================================================")
    print("DEMO: UNIVERSAL DISCOVERY & QWEN HELLO WORLD")
    print("====================================================\n")

    # 1. VERIFY OFFLINE
    is_alive = await ProviderCatalogService._ollama_health()
    print(f"[1] OLLAMA STATUS: {'CONNECTED' if is_alive else 'OFFLINE'}")
    
    # 2. UNIVERSAL DISCOVERY
    print("\n[2] PERFORMING UNIVERSAL DISK SCAN...")
    models = await ProviderCatalogService._ollama_list_installed()
    print(f"    GIMO found {len(models)} models on disk:")
    
    # Register as 'idle' to allow execute_task to proceed into the Smart Wake logic.
    # In a real scenario, the sync_with_ollama logic handles this.
    for m in models:
        print(f"    - {m.id} (Registrando...)")
        agent_id = f"ollama_{m.id.replace(':', '_')}"
        if agent_id not in SubAgentManager._sub_agents:
            SubAgentManager._sub_agents[agent_id] = SubAgent(
                id=agent_id,
                parentId="system_discovery",
                name=f"Ollama: {m.id}",
                model=m.id,
                status="idle", # Mandatory for execute_task to accept the job
                config=SubAgentConfig(model=m.id),
                description=f"Auto-discovered {m.id}"
            )
    
    # Identify Qwen for the task demo
    agent_id = next((aid for aid in SubAgentManager._sub_agents.keys() if "qwen" in aid.lower()), None)
    
    if not agent_id:
        print(f"\n    \u274c ERROR: Qwen not found. Agents: {list(SubAgentManager._sub_agents.keys())}")
        return

    print(f"    \u2705 Target Agent READY: {agent_id}")

    # 3. SMART WAKE DEMO
    print(f"\n[3] TASKING AGENT: {agent_id}")
    print("    GIMO will now auto-start Ollama and execute the task...")
    
    try:
        # The execute_task method handles ensure_ollama_ready internally
        response = await SubAgentManager.execute_task(agent_id, "Say exactly 'Hello World' and nothing else.")
        print(f"\n[4] RESPONSE FROM {agent_id.upper()}:\n    {response}")
        
    except Exception as e:
        print(f"\n    \u274c EXECUTION FAILED: {e}")

    print("\n====================================================")

if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    asyncio.run(demo_universal_activation())
