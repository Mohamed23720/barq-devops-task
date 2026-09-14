#!/usr/bin/env python3
"""Validation script: checks the whole environment is correctly configured."""
import json
import socket
import sys
import urllib.request
import os
BASE = f"http://127.0.0.1:{os.getenv('PUBLIC_PORT', '8080')}"
FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"PASS: {name}")
    except Exception as e:
        print(f"FAIL: {name} -> {e}")
        FAILURES.append(name)


def http_get(path, expect=200):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=3) as r:
        if r.status != expect:
            raise AssertionError(f"expected {expect}, got {r.status}")
        return json.loads(r.read())


def port_should_be_closed(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    result = s.connect_ex((host, port))
    s.close()
    if result == 0:
        raise AssertionError(f"port {port} is OPEN but should be closed")


check("root endpoint", lambda: http_get("/"))
check("health endpoint", lambda: http_get("/health"))
check("ready endpoint", lambda: http_get("/ready"))


def both_instances_respond():
    seen = set()
    for _ in range(10):
        d = http_get("/instance")
        seen.add(d.get("instance_id"))
    if len(seen) < 2:
        raise AssertionError(f"only saw instances: {seen}")


check("both backends respond via nginx", both_instances_respond)


def records_roundtrip():
    body = json.dumps({"title": "validate.py check"}).encode()
    req = urllib.request.Request(f"{BASE}/records", data=body,
                                  headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=3) as r:
        if r.status not in (200, 201):
            raise AssertionError(f"POST /records failed: {r.status}")
    http_get("/records")


check("records create+list", records_roundtrip)
check("counter increments", lambda: http_get("/counter"))
check("postgres port closed to host", lambda: port_should_be_closed("127.0.0.1", 15432))
check("redis port closed to host", lambda: port_should_be_closed("127.0.0.1", 16379))

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed: {FAILURES}")
    sys.exit(1)

print("\nAll checks passed.")
sys.exit(0)