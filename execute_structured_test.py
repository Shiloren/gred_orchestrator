"""
GIMO MCP Execution Test - Structured Plan
=========================================
Este script aprueba el borrador estructurado d_1771623965936_7fa676 y monitorea
la ejecución "en vivo".
"""
import asyncio
import os
import sys
import time
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def main():
    server_env = os.environ.copy()
    server_env["ORCH_REPO_ROOT"] = r"C:\Users\shilo\Documents\Github\gimo_prueba"
    server_env["DEBUG"] = "true"
    server_env["ORCH_LICENSE_ALLOW_DEBUG_BYPASS"] = "true"
    server_env["PYTHONIOENCODING"] = "utf-8"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "tools.gimo_server.mcp_server"],
        env=server_env,
    )

    draft_id = "d_1771624208614_d15d13"

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            print(f"\n[1] Aprobando Draft: {draft_id}...")
            # Aprobar y crear Run
            approve_result = await session.call_tool("gimo_approve_draft", {"draft_id": draft_id})
            print(f"Respuesta aprobación: {approve_result.content[0].text}")
            
            # Extraer Run ID del texto: "Run ID: r_..."
            import re
            run_id_match = re.search(r"r_\w+", approve_result.content[0].text)
            if not run_id_match:
                print("No se pudo encontrar el Run ID.")
                return
            
            run_id = run_id_match.group(0)
            print(f"\n[2] Monitoreando ejecución del Run: {run_id}...")
            
            # Polling "en vivo"
            for i in range(25): # Aumentamos tiempo para el plan estructurado
                status_result = await session.call_tool("gimo_get_task_status", {"run_id": run_id})
                status_text = status_result.content[0].text
                print(f"[{i*2}s] {status_text.splitlines()[1]}") # Solo mostramos el estado
                
                if "Estado: done" in status_text:
                    print("\n¡EJECUCIÓN COMPLETADA!")
                    # Mostrar grafo final actualizado (teóricamente el worker podría actualizar estados de las tareas si su lógica fuera más avanzada, 
                    # pero aquí mostramos que el RUN general terminó)
                    print(status_text)
                    break
                if "Estado: error" in status_text:
                    print("\n¡ERROR EN LA EJECUCIÓN!")
                    print(status_text)
                    break
                
                await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
