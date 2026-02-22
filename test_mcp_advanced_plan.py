"""
GIMO MCP Advanced Plan Test
===========================
Este script solicita un plan estructurado (JSON + Grafo) para una tarea multi-paso.
"""
import asyncio
import os
import sys
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

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            task = "Escribe 'hello world' en hello.txt dentro de gimo_prueba. Hazlo en 3 pasos claros: 1. Crear el dir si no existe, 2. Escribir el arcivo, 3. Verificar con cat."
            print(f"\n[1] Solicitando PLAN ESTRUCTURADO para: '{task}'")
            
            result = await session.call_tool("gimo_propose_structured_plan", {"task_instructions": task})
            print("\n[RESULTADO DEL ORQUESTADOR]:")
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())
