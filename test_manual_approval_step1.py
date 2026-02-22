"""
GIMO MCP Manual Approval Test - Paso 1: Crear Borrador
=====================================================
Este script crea un borrador (draft) en GIMO y muestra el plan propuesto.
NO lo ejecuta automáticamente.
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
            
            task = "Escribe 'hello world' en un archivo llamado hello.txt en la raíz del repositorio gimo_prueba."
            print(f"\n[1] Solicitando creación de draft para: '{task}'")
            
            # Llamamos a la herramienta que genera el plan (propose)
            result = await session.call_tool("gimo_create_draft", {"task_instructions": task})
            print("\n[RESUMEN DEL DRAFT RECIBIDO]:")
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())
