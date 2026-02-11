# Claude CLI Guide

To use the Claude CLI outside of the IDE, you can use the provided PowerShell script which launches a standalone terminal window.

## How to Launch

1.  Open a terminal (PowerShell or Command Prompt).
2.  Navigate to the project root:
    ```powershell
    cd c:\Users\shilo\Documents\Github\gred_in_multiagent_orchestrator
    ```
3.  Run the launch script:
    ```powershell
    .\scripts\dev\launch_claude.ps1
    ```

This will open a new PowerShell window running the `claude_cli.py` script.

## Pre-requisites

- **Python**: Ensure Python is installed and `anthropic`, `python-dotenv`, and `rich` packages are installed (`pip install anthropic python-dotenv rich`).
- **Environment**: Your `ANTHROPIC_API_KEY` must be set in a `.env` file in the project root or in your system environment variables.
