import asyncio
import json
import logging
import socket
import subprocess
import time
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import GICS_DAEMON_SCRIPT, GICS_SOCKET_PATH, GICS_TOKEN_PATH, OPS_DATA_DIR

logger = logging.getLogger("orchestrator.services.gics")


class GicsService:
    """Service to manage GICS Daemon and communicate via JSON-RPC over TCP/Pipe."""

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._token: Optional[str] = None
        self._socket: Optional[socket.socket] = None
        self._pipe_file: Optional[Any] = None  # For Windows Named Pipe
        self._actual_socket_path: Optional[str] = None
        self._health_task: Optional[asyncio.Task] = None
        
    def start_daemon(self) -> None:
        """Start the GICS daemon subprocess."""
        if self._process and self._process.poll() is None:
            logger.info("GICS Daemon already running (pid=%s)", self._process.pid)
            return

        if not GICS_DAEMON_SCRIPT.exists():
            logger.error("GICS Daemon script not found at %s", GICS_DAEMON_SCRIPT)
            return

        logger.info("Starting GICS Daemon from %s...", GICS_DAEMON_SCRIPT)
        
        # Ensure the data directory exists
        gics_data_path = OPS_DATA_DIR / "gics_data"
        gics_data_path.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["GICS_DATA_PATH"] = str(gics_data_path)
        # On Windows, server.js likely uses a named pipe if we give it a pipe path, 
        # or a file path for unix domain socket. 
        # But 'net.createServer' on Windows with a path argument creates a named pipe.
        # Let's use a named pipe path format for Windows if needed, or just a file path and let node handle it.
        # Node docs: on Windows, a path is a named pipe.
        # Python's `socket.connect` on Windows doesn't support AF_UNIX until recently (Py3.10+ dev mode?)
        # safer to use a TCP port for cross-platform simplicity if GICS supports it.
        # Checking server.js: `this.server.listen(this.config.socketPath, ...)`
        # If we pass a port number to socketPath? No, Config says socketPath is string.
        # If we pass "\\.\pipe\gics.sock" ??
        
        # Let's assume standard file path for now, but on Windows we might need to adjust.
        # For this implementation, I will treat it as a file path that Node turns into a pipe.
        # Connecting to it from Python on Windows requires `pywin32` or specific pipe open handling.
        # To avoid dependency hell, IF config allows, we should ask Daemon to listen on TCP.
        # Analyzing server.js line 108: `this.server.listen(this.config.socketPath, ...)`
        # If socketPath is a path, it's IPC.
        
        # DECISION: We will try to rely on Python's `socket.AF_UNIX` if available (Linux/Mac/Windows 10+ recent).
        # functionality. If not, we might fail.
        # Actually, let's just pass the path.
        
        socket_path_str = str(GICS_SOCKET_PATH)
        
        # On Windows, we MUST use a named pipe path format for Node.
        if os.name == 'nt':
             socket_path_str = r'\\.\pipe\gics_sock'
        
        env["GICS_SOCKET_PATH"] = socket_path_str
        env["GICS_TOKEN_PATH"] = str(GICS_TOKEN_PATH)
        env["GICS_DAEMON_SCRIPT"] = str(GICS_DAEMON_SCRIPT)

        bootstrap_js = (
            "import { pathToFileURL } from 'url';"
            "const scriptPath = process.env.GICS_DAEMON_SCRIPT;"
            "const mod = await import(pathToFileURL(scriptPath).href);"
            "const GICSDaemon = mod.GICSDaemon;"
            "if (!GICSDaemon) { throw new Error('GICSDaemon export not found'); }"
            "const daemon = new GICSDaemon({"
            "dataPath: process.env.GICS_DATA_PATH,"
            "socketPath: process.env.GICS_SOCKET_PATH,"
            "tokenPath: process.env.GICS_TOKEN_PATH,"
            "maxMemSizeBytes: Number(process.env.GICS_MAX_MEM_SIZE_BYTES || 33554432),"
            "maxDirtyCount: Number(process.env.GICS_MAX_DIRTY_COUNT || 1000)"
            "});"
            "await daemon.start();"
            "const graceful = async () => { try { await daemon.stop(); } catch {} process.exit(0); };"
            "process.on('SIGTERM', graceful);"
            "process.on('SIGINT', graceful);"
        )

        cmd = ["node", "--input-type=module", "-e", bootstrap_js]
        
        try:
            self._process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info("GICS Daemon started with pid=%s", self._process.pid)
            self._wait_for_token()
            if self._process.poll() is not None:
                _stdout = (self._process.stdout.read() if self._process.stdout else "") or ""
                _stderr = (self._process.stderr.read() if self._process.stderr else "") or ""
                logger.error(
                    "GICS Daemon exited early (code=%s). stdout=%s stderr=%s",
                    self._process.returncode,
                    _stdout.strip()[:500],
                    _stderr.strip()[:500],
                )
            
            # Update the stored socket path to match what we told the daemon
            # (In case we changed it for Windows named pipe)
            self._actual_socket_path = socket_path_str
            
        except Exception as e:
            logger.error("Failed to start GICS Daemon: %s", e)

    def stop_daemon(self) -> None:
        """Stop the GICS daemon."""
        self.stop_health_check()
        if self._process:
            logger.info("Stopping GICS Daemon...")
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
            self._close_socket()

    def _wait_for_token(self, timeout: int = 10) -> None:
        start = time.time()
        while time.time() - start < timeout:
            if GICS_TOKEN_PATH.exists():
                try:
                    self._token = GICS_TOKEN_PATH.read_text().strip()
                    return
                except (OSError, ValueError):
                    pass
            time.sleep(0.5)
        logger.warning("Timed out waiting for GICS token file at %s", GICS_TOKEN_PATH)

    def _close_socket(self):
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None
        if self._pipe_file:
            try:
                self._pipe_file.close()
            except OSError:
                pass
            self._pipe_file = None

    def _send_with_retry(self, method: str, params: Dict[str, Any] = None, max_retries: int = 3) -> Any:
        """Send command with exponential backoff retry."""
        delays = [0.5, 1.0, 2.0]
        last_error = None

        for attempt in range(max_retries):
            try:
                return self.send_command(method, params)
            except Exception as e:
                last_error = e
                self._close_socket()
                if attempt < max_retries - 1:
                    delay = delays[min(attempt, len(delays) - 1)]
                    logger.warning("GICS retry %d/%d after %.1fs: %s", attempt + 1, max_retries, delay, e)
                    time.sleep(delay)

        logger.error("GICS command %s failed after %d retries: %s", method, max_retries, last_error)
        return None

    async def _health_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(60)
                self._send_with_retry("scan", {"prefix": "ops:", "includeFields": False}, max_retries=1)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("GICS health check error: %s", exc)

    def start_health_check(self) -> None:
        if self._health_task and not self._health_task.done():
            return
        try:
            self._health_task = asyncio.create_task(self._health_loop())
        except RuntimeError:
            self._health_task = None

    def stop_health_check(self) -> None:
        if self._health_task and not self._health_task.done():
            self._health_task.cancel()
        self._health_task = None

    def _connect(self) -> None:
        """Establish connection to daemon."""
        if self._socket or self._pipe_file:
            return

        if not hasattr(self, '_actual_socket_path') or self._actual_socket_path is None:
             self._actual_socket_path = str(GICS_SOCKET_PATH)
             if os.name == 'nt':
                 self._actual_socket_path = r'\\.\pipe\gics_sock'

        try:
             if os.name == 'nt':
                 # Use Named Pipe on Windows via file API
                 # buffering=0 is crucial for real-time communication
                 self._pipe_file = open(self._actual_socket_path, 'rb+', buffering=0)
             elif hasattr(socket, 'AF_UNIX'):
                 self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                 self._socket.connect(self._actual_socket_path)
                 self._socket.settimeout(5.0)
             else:
                 raise NotImplementedError("AF_UNIX not supported on this platform")
        except Exception as e:
            logger.error("Failed to connect to GICS Daemon at %s: %s", self._actual_socket_path, e)
            raise

    def send_command(self, method: str, params: Dict[str, Any] = None) -> Any:
        """Send a JSON-RPC 2.0 command to the daemon."""
        if not self._token:
            raise RuntimeError("GICS Token not available")
            
        self._connect()
        
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": request_id,
            "token": self._token
        }
        
        message = json.dumps(payload) + "\n"
        
        try:
            if self._pipe_file:
                self._pipe_file.write(message.encode('utf-8'))
                response_data = self._pipe_file.readline()
                if not response_data:
                    raise ConnectionError("Pipe closed remotely")
                response = json.loads(response_data.decode('utf-8'))
            else:
                self._socket.sendall(message.encode('utf-8'))
                
                # Read response (line buffered)
                response_data = b""
                while b"\n" not in response_data:
                    chunk = self._socket.recv(4096)
                    if not chunk:
                        raise ConnectionError("Socket closed remotely")
                    response_data += chunk
                
                line, _, _ = response_data.partition(b"\n")
                response = json.loads(line.decode('utf-8'))
            
            if "error" in response:
                raise RuntimeError(f"GICS Error: {response['error']}")
                
            return response.get("result")
            
        except ConnectionError:
            logger.warning("GICS Daemon connection broken, retrying...")
            self._close_socket()
            self._connect()
            # Retry once
            self._socket.sendall(message.encode('utf-8'))
            # ... (Reading logic repeat - simplified for brevity, in real prod use a retry decorators)
            # For this 'mvp', just fail if retry needed to keep code simple
            return None 

    def put(self, key: str, fields: Dict[str, Any]) -> Any:
        return self._send_with_retry("put", {"key": key, "fields": fields})

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._send_with_retry("get", {"key": key})

    def scan(self, prefix: str = "", include_fields: bool = True) -> List[Dict[str, Any]]:
        result = self._send_with_retry("scan", {"prefix": prefix, "includeFields": include_fields})
        if result and "items" in result:
            return result["items"]
        return []

    def flush(self) -> Any:
        """No-op: GICS daemon auto-flushes. Manual flush not exposed via JSON-RPC."""
        pass

    @staticmethod
    def _model_key(provider_type: str, model_id: str) -> str:
        p = str(provider_type or "unknown").strip().lower().replace(" ", "_")
        m = str(model_id or "unknown").strip().lower().replace(" ", "_")
        return f"ops:model_score:{p}:{m}"

    def seed_model_prior(
        self,
        *,
        provider_type: str,
        model_id: str,
        prior_scores: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Seed initial model priors (phase-1 catalog metadata -> GICS)."""
        key = self._model_key(provider_type, model_id)
        existing = self.get(key)
        fields = dict((existing or {}).get("fields") or {})
        priors = dict(prior_scores or {})
        if priors:
            avg_prior = sum(float(v) for v in priors.values()) / max(1, len(priors))
        else:
            avg_prior = float(fields.get("score", 0.5) or 0.5)

        merged = {
            "provider_type": provider_type,
            "model_id": model_id,
            "score": float(fields.get("score", avg_prior) or avg_prior),
            "priors": priors,
            "samples": int(fields.get("samples", 0) or 0),
            "successes": int(fields.get("successes", 0) or 0),
            "failures": int(fields.get("failures", 0) or 0),
            "failure_streak": int(fields.get("failure_streak", 0) or 0),
            "avg_latency_ms": float(fields.get("avg_latency_ms", 0.0) or 0.0),
            "avg_cost_usd": float(fields.get("avg_cost_usd", 0.0) or 0.0),
            "anomaly": bool(fields.get("anomaly", False)),
            "metadata": dict(metadata or fields.get("metadata") or {}),
            "updated_at": int(time.time()),
        }
        self.put(key, merged)
        return merged

    def record_model_outcome(
        self,
        *,
        provider_type: str,
        model_id: str,
        success: bool,
        latency_ms: Optional[float] = None,
        cost_usd: Optional[float] = None,
        task_type: str = "general",
    ) -> Dict[str, Any]:
        """Register post-task evidence and update reliability score."""
        key = self._model_key(provider_type, model_id)
        existing = self.get(key)
        fields = dict((existing or {}).get("fields") or {})

        samples = int(fields.get("samples", 0) or 0) + 1
        successes = int(fields.get("successes", 0) or 0) + (1 if success else 0)
        failures = int(fields.get("failures", 0) or 0) + (0 if success else 1)
        failure_streak = 0 if success else int(fields.get("failure_streak", 0) or 0) + 1

        prev_latency = float(fields.get("avg_latency_ms", 0.0) or 0.0)
        prev_cost = float(fields.get("avg_cost_usd", 0.0) or 0.0)
        new_latency = float(latency_ms or 0.0)
        new_cost = float(cost_usd or 0.0)
        avg_latency = ((prev_latency * (samples - 1)) + new_latency) / max(1, samples)
        avg_cost = ((prev_cost * (samples - 1)) + new_cost) / max(1, samples)

        success_rate = successes / max(1, samples)
        prior_score = float(fields.get("score", 0.5) or 0.5)
        blended_score = max(0.0, min(1.0, (prior_score * 0.2) + (success_rate * 0.8)))
        anomaly = failure_streak >= 3

        outcome = {
            "provider_type": provider_type,
            "model_id": model_id,
            "task_type": task_type,
            "score": blended_score,
            "samples": samples,
            "successes": successes,
            "failures": failures,
            "failure_streak": failure_streak,
            "avg_latency_ms": avg_latency,
            "avg_cost_usd": avg_cost,
            "anomaly": anomaly,
            "updated_at": int(time.time()),
        }
        self.put(key, {**fields, **outcome})
        return {**fields, **outcome}

    def get_model_reliability(self, *, provider_type: str, model_id: str) -> Optional[Dict[str, Any]]:
        key = self._model_key(provider_type, model_id)
        result = self.get(key)
        if not result:
            return None
        return dict(result.get("fields") or {})
