# GIMO Secure Launcher Documentation

The GIMO Launcher (`GIMO_LAUNCHER.cmd`) is designed for a safe and robust development experience.

## Security Features

### 1. High-Entropy Authentication (`ORCH_TOKEN`)
On the first run, the launcher generates a 32-byte cryptographically secure random token (Base64 encoded) and saves it to your `.env` file.
- **Why**: This prevents unauthorized access to the GIMO backend, even if other local processes try to connect.

### 2. Localhost Binding (`127.0.0.1`)
Both the backend and frontend are explicitly bound to `127.0.0.1`.
- **Why**: This ensures that GIMO is not accessible from other machines on your local network (e.g., public Wi-Fi), minimizing the network attack surface.

### 3. Port Hygiene
The launcher automatically identifies and terminates any processes listening on GIMO ports (9325 and 5173).
- **Why**: Prevents "Address already in use" errors and ensures you are always running the latest code without zombie processes interfering.

### 4. Dependency Management
The launcher detects and uses isolated virtual environments (`.venv` or `venv`) if they exist.
- **Why**: Ensures that GIMO runs with the correct versions of its dependencies, avoiding conflicts with global Python packages.

### 5. Health Verification
The launcher waits for the backend to be fully initialized and healthy (via `scripts/dev/health_check.py`) before starting the frontend and opening the browser.
- **Why**: Provides a much more stable startup experience compared to fixed-time delays.

## Usage

Simply run `GIMO_LAUNCHER.cmd` from the root of the repository.

```bash
.\GIMO_LAUNCHER.cmd
```

## Troubleshooting

- **Backend Error**: If the backend fails to start, check the "GIMO Backend" window for logs.
- **Node/NPM missing**: Ensure you have Node.js installed to run the frontend.
- **Python missing**: Ensure Python 3.10+ is in your PATH or in a `.venv` folder.
