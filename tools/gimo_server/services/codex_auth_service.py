import asyncio
import re
import logging
import shutil
from typing import Optional, Dict, Any

logger = logging.getLogger("orchestrator.services.codex_auth")


class CodexAuthService:
    """Gestiona la autenticacion Device Code Flow para Codex."""
    @classmethod
    async def start_device_flow(cls) -> Dict[str, Any]:
        """
        Starts the codex login --device-auth process and captures the verification
        URL and user code. Returns a token polling identifier (the process itself
        or a mock).
        """
        if shutil.which("codex") is None:
            return {
                "status": "error",
                "message": "Codex CLI no detectado",
                "action": "npm install -g @openai/codex",
            }

        try:
            # Note: The codex CLI writes instructions to stdout/stderr. We parse it:
            # e.g., "Please open https://openai.com/device and enter the code: XXXX-YYYY"
            process = await asyncio.create_subprocess_exec(
                "codex",
                "login",
                "--device-auth",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except FileNotFoundError:
            return {
                "status": "error",
                "message": "Codex CLI no detectado",
                "action": "npm install -g @openai/codex",
            }

        verification_url = None
        user_code = None

        url_pattern = re.compile(r"https?://\S+")
        code_pattern = re.compile(r"([A-Z0-9]{4}-[A-Z0-9]{4})")

        # Read output until we find the URL and code (timeout after 10s)
        try:
            async with asyncio.timeout(10.0):
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    decoded_line = line.decode(errors="replace").strip()
                    logger.debug(f"Codex login output: {decoded_line}")
                    
                    if not verification_url:
                        url_match = url_pattern.search(decoded_line)
                        if url_match:
                            verification_url = url_match.group(0)
                            
                    if not user_code:
                        code_match = code_pattern.search(decoded_line)
                        if code_match:
                            user_code = code_match.group(1)
                            
                    if verification_url and user_code:
                        break
        except asyncio.TimeoutError:
            process.kill()
            return {
                "status": "error",
                "message": "Timeout esperando instrucciones de login de Codex CLI",
                "action": "Reintenta el login o reinstala Codex CLI: npm install -g @openai/codex",
            }

        if not verification_url or not user_code:
            process.kill()
            return {
                "status": "error",
                "message": "No se pudo extraer verification_url/user_code de Codex CLI",
                "action": "Actualiza o reinstala Codex CLI: npm install -g @openai/codex",
            }

        # In a real implementation, we would register `process` in a background task dictionary
        # keyed by some unique ID, and poll it. 
        # For simplicity, we just return the parsed URL/code and instruct the user.
        # Codex CLI caches the session token in the global environment once the flow completes.
        
        # We start a background task to wait for completion
        asyncio.create_task(cls._wait_for_login(process))

        return {
            "status": "pending",
            "verification_url": verification_url,
            "user_code": user_code,
            "message": "Please open the URL and enter the code to authenticate.",
            "poll_id": "real_poll_id"
        }

    @classmethod
    async def _wait_for_login(cls, process: asyncio.subprocess.Process):
        """Wait for the codex login process to complete."""
        try:
            await process.wait()
            if process.returncode == 0:
                logger.info("Codex CLI device auth completed successfully.")
                # We could broadcast a websocket event here if we wanted to push to the UI.
            else:
                logger.error(f"Codex CLI device auth failed with exit code {process.returncode}.")
        except Exception as e:
            logger.error(f"Error waiting for codex login: {e}")
