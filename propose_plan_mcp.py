import asyncio
import os
import sys
import json
import logging
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def propose_plan():
    server_env = os.environ.copy()
    server_env["ORCH_REPO_ROOT"] = r"c:\Users\shilo\Documents\Github"
    server_env["PYTHONIOENCODING"] = "utf-8"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "tools.gimo_server.mcp_server"],
        env=server_env,
    )

    task_instructions = (
        "Crea un plan donde Antigravity es el Orquestador principal. "
        "El plan debe incluir un agente llamado 'Qwen' (modelo qwen2.5-coder:32b). "
        "La tarea de Qwen es crear un archivo 'qwen_test.txt' con el contenido: "
        "'yo soy qwen, esto es una prueba. puedo escribir texto y crear archivos.'."
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print(f"Invocando gimo_propose_structured_plan...")
            response = await session.call_tool(
                "gimo_propose_structured_plan",
                {"task_instructions": task_instructions},
            )
            output = response.content[0].text
            print("Respuesta recibida:")
            print(output.encode("ascii", errors="replace").decode("ascii"))

if __name__ == "__main__":
    asyncio.run(propose_plan())
