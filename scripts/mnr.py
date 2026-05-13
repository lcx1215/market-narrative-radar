#!/usr/bin/env python3
"""Local product loop for Market Narrative Radar.

This script keeps local development clean:
- starts the static app, data relay, and LLM relay as one unit
- writes logs and pid files under .mnr-runtime/
- stops only processes it started
- runs a real HTTP smoke test without creating repo artifacts
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".mnr-runtime"
STATIC_PORT = int(os.environ.get("MNR_STATIC_PORT", "8765"))
LLM_PORT = int(os.environ.get("MNR_RELAY_PORT", "8787"))
DATA_PORT = int(os.environ.get("MNR_DATA_PORT", "8790"))

SERVICES = {
    "app": {
        "port": STATIC_PORT,
        "cmd": [sys.executable, "-m", "http.server", str(STATIC_PORT)],
        "match": "http.server 8765",
    },
    "data": {
        "port": DATA_PORT,
        "cmd": [sys.executable, "server/data_relay.py"],
        "match": "server/data_relay.py",
    },
    "llm": {
        "port": LLM_PORT,
        "cmd": [sys.executable, "server/llm_relay.py"],
        "match": "server/llm_relay.py",
    },
}


def runtime_path(name: str, suffix: str) -> Path:
    return RUNTIME / f"{name}.{suffix}"


def print_line(message: str) -> None:
    print(message, flush=True)


def port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def port_owner_pids(port: int) -> list[int]:
    try:
        output = subprocess.check_output(
            ["lsof", "-tiTCP:%s" % port, "-sTCP:LISTEN"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    pids = []
    for line in output.splitlines():
        try:
            pids.append(int(line.strip()))
        except ValueError:
            continue
    return pids


def command_for_pid(pid: int) -> str:
    try:
        return subprocess.check_output(["ps", "-p", str(pid), "-o", "command="], text=True).strip()
    except subprocess.CalledProcessError:
        return ""


def read_pid(name: str) -> int | None:
    path = runtime_path(name, "pid")
    if not path.exists():
        return None
    try:
        return int(path.read_text().strip())
    except ValueError:
        return None


def pid_running(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def service_running(name: str) -> bool:
    return pid_running(read_pid(name))


def ensure_runtime() -> None:
    RUNTIME.mkdir(exist_ok=True)


def start_service(name: str) -> None:
    spec = SERVICES[name]
    pid = read_pid(name)
    if pid_running(pid):
        print_line(f"{name}: already running pid={pid}")
        return
    if port_open(spec["port"]):
        raise SystemExit(f"{name}: port {spec['port']} is already in use by an unmanaged process")
    ensure_runtime()
    log_path = runtime_path(name, "log")
    log_file = log_path.open("a", encoding="utf-8")
    process = subprocess.Popen(
        spec["cmd"],
        cwd=ROOT,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    runtime_path(name, "pid").write_text(str(process.pid))
    time.sleep(0.5)
    if not pid_running(process.pid):
        raise SystemExit(f"{name}: failed to start; see {log_path}")
    print_line(f"{name}: started pid={process.pid} port={spec['port']} log={log_path}")


def stop_service(name: str) -> None:
    pid = read_pid(name)
    if not pid_running(pid):
        runtime_path(name, "pid").unlink(missing_ok=True)
        stopped = stop_unmanaged_expected_service(name)
        if not stopped:
            print_line(f"{name}: not running")
        return
    assert pid is not None
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    for _ in range(20):
        if not pid_running(pid):
            break
        time.sleep(0.1)
    if pid_running(pid):
        os.killpg(pid, signal.SIGKILL)
    runtime_path(name, "pid").unlink(missing_ok=True)
    print_line(f"{name}: stopped pid={pid}")


def stop_unmanaged_expected_service(name: str) -> bool:
    spec = SERVICES[name]
    stopped = False
    for pid in port_owner_pids(spec["port"]):
        if pid == os.getpid():
            continue
        command = command_for_pid(pid)
        if spec["match"] not in command:
            continue
        try:
            os.kill(pid, signal.SIGTERM)
            stopped = True
            print_line(f"{name}: stopped unmanaged project process pid={pid}")
        except ProcessLookupError:
            continue
    if stopped:
        time.sleep(0.5)
    return stopped


def start_all(restart: bool) -> None:
    if restart:
        stop_all()
    for name in SERVICES:
        start_service(name)
    status()


def stop_all() -> None:
    for name in reversed(list(SERVICES)):
        stop_service(name)


def status() -> None:
    for name, spec in SERVICES.items():
        pid = read_pid(name)
        owned = pid_running(pid)
        listening = port_open(spec["port"])
        state = "running" if owned else "unmanaged-port" if listening else "stopped"
        print_line(f"{name}: {state} pid={pid or '-'} port={spec['port']}")


def request_json(url: str, timeout: int = 20) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict, timeout: int = 45) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def smoke_test(use_provider: bool) -> None:
    html = urllib.request.urlopen(f"http://127.0.0.1:{STATIC_PORT}", timeout=10).read().decode("utf-8")
    assert "Market Narrative Radar" in html
    assert "Generate brief" in html
    print_line("app: html ok")

    health = request_json(f"http://127.0.0.1:{DATA_PORT}/api/health", timeout=10)
    assert health.get("ok") is True
    print_line("data: health ok")

    query = urllib.parse.urlencode({"query": "AI infrastructure regulation demand", "limit": "2"})
    live = request_json(f"http://127.0.0.1:{DATA_PORT}/api/live-sources?{query}", timeout=45)
    docs = live.get("documents") or []
    assert docs, "live source relay returned no documents"
    ok_sources = [item["source"] for item in live.get("health", []) if item.get("ok")]
    print_line(f"data: live ok docs={len(docs)} sources={len(ok_sources)}")

    engine = "auto" if use_provider else "local"
    analysis = post_json(
        f"http://127.0.0.1:{LLM_PORT}/api/analyze",
        {
            "engine": engine,
            "analysis_mode": "analyst",
            "question": "What is the public text implying about AI infrastructure demand and regulation?",
            "analysis_plan": {
                "intent": "source_conflict_check",
                "focus_terms": ["ai", "infrastructure", "demand", "regulation"],
                "evidence_count": 3,
                "source_groups": ["Company filing", "Federal Register", "Executive transcript"],
            },
            "source_profiles": [
                {
                    "profile_key": "company_filing",
                    "source_type": "Company filing",
                    "cleaning_strategy": "Keep risk-factor and demand language.",
                    "signals_to_extract": ["risk factors", "demand language"],
                    "confidence_penalty": "low",
                },
                {
                    "profile_key": "regulator_text",
                    "source_type": "Federal Register",
                    "cleaning_strategy": "Keep compliance and agency-action language.",
                    "signals_to_extract": ["compliance cost", "legal uncertainty"],
                    "confidence_penalty": "low",
                },
            ],
            "source_conflicts": [
                {
                    "theme": "AI infrastructure",
                    "company_frame": "growth and demand",
                    "regulator_frame": "compliance and constraints",
                }
            ],
            "evidence": [
                {
                    "source_type": "Company filing",
                    "date": "2026-05-01",
                    "title": "AI supplier filing excerpt",
                    "source_url": "https://example.com/company",
                    "theme": "AI",
                    "sentence": "The company describes strong AI infrastructure demand while warning timing may be affected by supply and regulation.",
                },
                {
                    "source_type": "Federal Register",
                    "date": "2026-05-02",
                    "title": "Agency notice",
                    "source_url": "https://example.com/regulator",
                    "theme": "Regulation",
                    "sentence": "The notice emphasizes grid constraints and compliance review for infrastructure expansion.",
                },
                {
                    "source_type": "Executive transcript",
                    "date": "2026-05-03",
                    "title": "CEO interview",
                    "source_url": "https://example.com/interview",
                    "theme": "Demand",
                    "sentence": "Management says demand remains broad but deployment depends on customer readiness and permits.",
                },
            ],
        },
    )
    result = analysis.get("analysis") or {}
    for field in ["question_intent", "analysis_plan", "source_profiles", "executive_read", "confidence"]:
        assert field in result, f"missing analysis field: {field}"
    assert result["analysis_plan"].get("source_count") == 3
    print_line(f"llm: {engine} ok provider={analysis.get('provider', 'local')}")


def clean() -> None:
    for pattern in ["__pycache__", ".pytest_cache", ".DS_Store", "*.pyc", "playwright-report", "test-results"]:
        for path in ROOT.rglob(pattern):
            if ".git" in path.parts or path == RUNTIME:
                continue
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
    print_line("clean: removed transient Python/browser artifacts")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the local Market Narrative Radar app loop.")
    sub = parser.add_subparsers(dest="command", required=True)
    start_parser = sub.add_parser("start")
    start_parser.add_argument("--restart", action="store_true")
    sub.add_parser("stop")
    sub.add_parser("status")
    test_parser = sub.add_parser("test")
    test_parser.add_argument("--provider", action="store_true", help="exercise configured paid/provider LLM instead of local fallback")
    sub.add_parser("clean")
    args = parser.parse_args()

    if args.command == "start":
        start_all(args.restart)
    elif args.command == "stop":
        stop_all()
    elif args.command == "status":
        status()
    elif args.command == "test":
        smoke_test(args.provider)
    elif args.command == "clean":
        clean()


if __name__ == "__main__":
    main()
