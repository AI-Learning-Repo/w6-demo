"""Colab infrastructure helpers for the W6 A2A lab."""
import os
import sys
import time
import subprocess
from pathlib import Path
import requests
import pandas as pd
from IPython.display import Code, Markdown, display

AGENTS = {}
processes = {}
LOG_DIR = None
REQUEST_DELAY = 20

def configure(repo, delay=20, log_dir="/content/seller_logs"):
    global LOG_DIR, REQUEST_DELAY
    if any(p.poll() is None for p in processes.values()):
        raise RuntimeError("Stop existing sellers before reconfiguring.")
    repo = Path(repo).resolve()
    AGENTS.clear()
    for name, port in [("burger", 11001), ("pizza", 11000)]:
        AGENTS[name] = {"directory": repo / "remote_seller_agents" / (name + "_agent"),
                        "port": port, "url": f"http://127.0.0.1:{port}"}
        if not AGENTS[name]["directory"].is_dir():
            raise FileNotFoundError(AGENTS[name]["directory"])
    LOG_DIR = Path(log_dir)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    set_delay(delay)
    return AGENTS

def set_delay(seconds):
    global REQUEST_DELAY
    if seconds < 0:
        raise ValueError("Delay must be nonnegative")
    REQUEST_DELAY = seconds

def pause(seconds=None):
    seconds = REQUEST_DELAY if seconds is None else seconds
    print(f"Pausing for {seconds} seconds...")
    time.sleep(seconds)

def create_environments():
    for config in AGENTS.values():
        directory = config["directory"]
        if not (directory / ".venv/bin/python").exists():
            run_command(["uv", "venv", "--python", "3.12", directory / ".venv"])

def stop_all():
    for name in list(processes):
        stop_seller(name)


def run_command(command, cwd=None):

    command = list(map(str, command))

    print("Running:", " ".join(command))

    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print("STDERR:", result.stderr)

    result.check_returncode()

    return result.stdout


def install_requirements(directory):

    python_executable = directory / ".venv/bin/python"

    requirements = directory / "requirements-colab.txt"

    assert requirements.exists(), requirements

    run_command([
        "uv", "pip", "install",
        "--python", str(python_executable),
        "-r", str(requirements)
    ])


def start_seller(name):

    config = AGENTS[name]

    directory = config["directory"]
    port = config["port"]
    url = config["url"]

    existing = processes.get(name)

    if existing is not None and existing.poll() is None:
        print(f"{name} is already running.")
        return existing

    python_executable = directory / ".venv/bin/python"

    log_file = LOG_DIR / f"{name}.log"

    env = os.environ.copy()

    env["PYTHONUNBUFFERED"] = "1"
    env["HOST_OVERRIDE"] = url + "/"

    with log_file.open("w") as log:

        process = subprocess.Popen(
            [
                str(python_executable),
                "-u",
                "__main__.py",
                "--host", "127.0.0.1",
                "--port", str(port)
            ],
            cwd=directory,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT
        )

    processes[name] = process

    print(f"Started: {name}")
    print(f"PID: {process.pid}")
    print(f"URL: {url}")
    print(f"Log: {log_file}")

    return process


def wait_for_agent(name, timeout=120):

    url = AGENTS[name]["url"]

    card_url = url + "/.well-known/agent-card.json"

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:

        if processes[name].poll() is not None:

            print(f"{name} terminated.")

            print(
                (LOG_DIR / f"{name}.log")
                .read_text()[-5000:]
            )

            raise RuntimeError(f"{name} failed to start.")

        try:

            response = requests.get(
                card_url,
                timeout=2
            )

            if response.ok:

                card = response.json()

                print(f"{name} is ready.")
                print("Agent Card:", card_url)

                return card

        except requests.RequestException:
            pass

        time.sleep(2)

    raise TimeoutError(f"{name} did not become ready.")


def show_processes():

    rows = []

    for name, process in processes.items():

        rows.append({
            "Agent": name,
            "PID": process.pid,
            "Port": AGENTS[name]["port"],
            "URL": AGENTS[name]["url"],
            "Status": (
                "Running"
                if process.poll() is None
                else "Stopped"
            )
        })

    display(pd.DataFrame(rows))


def show_log(name, lines=30):

    path = LOG_DIR / f"{name}.log"

    content = "\n".join(
        path.read_text().splitlines()[-lines:]
    )

    display(Markdown(f"### {name} server log"))

    display(Code(
        data=content,
        language="text"
    ))


def show_source(path):

    path = Path(path)

    display(Markdown(f"### {path.parent.name}/{path.name}"))

    display(Code(
        filename=str(path),
        language="python"
    ))


def stop_seller(name):

    process = processes.get(name)

    if process is None:
        return

    if process.poll() is None:

        process.terminate()

        try:
            process.wait(timeout=10)

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    processes.pop(name, None)

    print(f"{name} stopped.")


def switch_provider(provider, model):

    if provider not in {"gemini", "groq"}:
        raise ValueError(f"Unsupported provider: {provider}")

    key_name = {
        "gemini": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY"
    }[provider]

    if not os.getenv(key_name):
        raise ValueError(f"{key_name} is missing.")
    if provider == "gemini":
        os.environ["GOOGLE_API_KEY"] = os.environ[key_name]
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "false"

    # Stop existing processes
    stop_seller("burger")
    stop_seller("pizza")

    # Configure new provider
    os.environ["SELLER_PROVIDER"] = provider
    os.environ["SELLER_MODEL"] = model

    print("Provider:", provider)
    print("Model:", model)

    # Restart services
    start_seller("burger")
    start_seller("pizza")

    cards = {
        "burger": wait_for_agent("burger"),
        "pizza": wait_for_agent("pizza")
    }

    show_processes()

    return cards
