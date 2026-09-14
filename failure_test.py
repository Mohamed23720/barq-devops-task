#!/usr/bin/env python3
"""Stops one backend, proves the site keeps serving, restores it, verifies recovery."""
import json
import subprocess
import sys
import time
import urllib.request
import os
BASE = f"http://127.0.0.1:{os.getenv('PUBLIC_PORT', '8080')}"
PROJECT = "barq-assessment"


def run(*args):
    return subprocess.run(args, capture_output=True, text=True, check=False)


def get_instance():
    try:
        with urllib.request.urlopen(f"{BASE}/instance", timeout=2) as r:
            return r.status, json.loads(r.read()).get("instance_id")
    except Exception as e:
        return None, str(e)


print("Step 1: baseline traffic")
before = [get_instance() for _ in range(6)]
print(before)

print("Step 2: stopping app-01")
r = run("docker", "compose", "-p", PROJECT, "stop", "app-01")
if r.returncode != 0:
    print("FAIL: could not stop app-01", r.stderr)
    sys.exit(1)

print("Step 3: traffic during failure (expect some errors, app-02 still serving)")
during = [get_instance() for _ in range(10)]
print(during)
ok_during = sum(1 for s, _ in during if s == 200)
if ok_during == 0:
    print("FAIL: no successful responses while app-01 was down")
    sys.exit(1)
print(f"PASS: {ok_during}/10 requests succeeded during outage (served by remaining backend)")

print("Step 4: restoring app-01")
run("docker", "compose", "-p", PROJECT, "start", "app-01")

print("Step 5: waiting for app-01 to become healthy")
healthy = False
for _ in range(30):
    r = run("docker", "inspect", "--format", "{{.State.Health.Status}}", "app-01")
    if r.stdout.strip() == "healthy":
        healthy = True
        break
    time.sleep(2)

if not healthy:
    print("FAIL: app-01 did not become healthy again in time")
    sys.exit(1)
print("PASS: app-01 is healthy again")

print("Step 6: confirming app-01 serves requests again")
after = [get_instance() for _ in range(10)]
print(after)
seen = {i for _, i in after if i}
if "app-01" not in seen:
    print("FAIL: app-01 did not appear in responses after recovery")
    sys.exit(1)

print("\nPASS: failure and recovery test completed successfully.")
sys.exit(0)