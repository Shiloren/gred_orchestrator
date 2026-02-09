# Launch Claude CLI in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..'; python scripts\claude_cli.py"
