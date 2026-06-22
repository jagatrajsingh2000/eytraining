"""Launch AutoGen Studio with an ngrok public URL.

This script is a .py version of the Colab steps from class:

1. Install AutoGen Studio and pyngrok.
2. Verify the AutoGen Studio installation.
3. Ask for GROQ_API_KEY and ngrok auth token.
4. Start AutoGen Studio on port 8081.
5. Open an ngrok tunnel to the Studio UI.

Run:
    python run_autogen_studio.py
"""

from __future__ import annotations

import getpass
import os
import shutil
import subprocess
import sys
import time
from multiprocessing import Process
from pathlib import Path


PORT = 8081
HOST = "0.0.0.0"


def run_command(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a shell command without using notebook-only ! syntax."""
    print(f"\n$ {' '.join(command)}")
    return subprocess.run(command, check=check, text=True)


def autogenstudio_command(*args: str) -> list[str]:
    """Find the AutoGen Studio CLI installed for the current Python."""
    executable = shutil.which("autogenstudio")
    if executable:
        return [executable, *args]

    local_executable = Path(sys.executable).parent / "autogenstudio"
    if local_executable.exists():
        return [str(local_executable), *args]

    return ["autogenstudio", *args]


def install_dependencies() -> None:
    print("\n# Install AutoGen Studio, AutoGen Python package, and pyngrok")
    run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "autogenstudio",
            "pyautogen",
            "pyngrok",
        ]
    )


def verify_installation() -> None:
    print("\n# Verify the installation")
    run_command(autogenstudio_command("version"))


def setup_groq_api_key() -> None:
    print("\n# 1. Set up Groq API Key")
    if "GROQ_API_KEY" not in os.environ:
        os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your Groq API Key: ")
    else:
        print("GROQ_API_KEY is already set.")


def setup_ngrok_token() -> None:
    print("\n# 2. Set up ngrok Auth Token")
    ngrok_token = getpass.getpass("Enter your ngrok Auth Token: ")
    from pyngrok import ngrok

    ngrok.set_auth_token(ngrok_token)
    print("ngrok auth token configured.")


def run_autogen_studio() -> None:
    print(f"\n# Launch AutoGen Studio on port {PORT}")
    run_command(autogenstudio_command("ui", "--port", str(PORT), "--host", HOST))


def start_autogen_studio_background() -> Process:
    print("\n# Start AutoGen Studio in a background process")
    process = Process(target=run_autogen_studio)
    process.start()
    return process


def open_ngrok_tunnel():
    print(f"\n# Open the ngrok tunnel to port {PORT}")
    from pyngrok import ngrok

    public_url = ngrok.connect(PORT)
    print("\n" + "=" * 60)
    print("[SUCCESS] AutoGen Studio is running!")
    print("Click the link below to open the UI:")
    print(public_url)
    print("=" * 60 + "\n")
    return public_url


def main() -> None:
    install_dependencies()
    verify_installation()
    setup_groq_api_key()
    setup_ngrok_token()

    process = start_autogen_studio_background()

    print("\n# Wait a moment for the server to spin up")
    time.sleep(5)

    try:
        open_ngrok_tunnel()
        print("Press Ctrl+C to stop AutoGen Studio.")
        while process.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping AutoGen Studio...")
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)


if __name__ == "__main__":
    main()
