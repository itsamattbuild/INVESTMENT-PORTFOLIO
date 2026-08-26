"""Two real instances on one port -- the second must fail fast and loudly.

Reproduces the launch-twice measurement cited in spec/lifecycle.md section 3:
first instance binds and serves; second instance's bind fails; first keeps
serving throughout. The failure's errno is printed because it is
platform-specific -- compare against errno.EADDRINUSE symbolically, never
against a numeric literal or a message substring (98 on Linux, 48 on macOS).
"""

import errno
import socket
import subprocess
import sys
import time
import urllib.request

HOST = "127.0.0.1"

SERVER = r'''
import fastapi, uvicorn
app = fastapi.FastAPI()
@app.get("/health")
def health():
    return {"ok": True}
uvicorn.run(app, host=%(host)r, port=%(port)d, log_level="warning")
'''


def wait_ready(port, deadline=15.0):
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < deadline:
        try:
            with urllib.request.urlopen(
                    f"http://{HOST}:{port}/health", timeout=0.5) as r:
                if r.status == 200:
                    return time.perf_counter() - t0
        except Exception:
            time.sleep(0.05)
    return None


def main():
    probe = socket.socket()
    probe.bind((HOST, 0))
    port = probe.getsockname()[1]
    probe.close()

    code = SERVER % {"host": HOST, "port": port}
    first = subprocess.Popen([sys.executable, "-c", code],
                             stderr=subprocess.DEVNULL)
    try:
        run(port, second_code=code)
    finally:
        first.terminate()
        first.wait(timeout=10)


def run(port, second_code):
    ready = wait_ready(port)
    print(f"first instance: serving after {ready:.3f}s" if ready else
          "first instance: NEVER became ready")
    assert ready, "first instance failed to start"

    second = subprocess.Popen([sys.executable, "-c", second_code],
                              stderr=subprocess.PIPE, text=True)
    t0 = time.perf_counter()
    _, err = second.communicate(timeout=30)
    fail_time = time.perf_counter() - t0

    still_up = wait_ready(port, deadline=2.0) is not None
    print(f"second instance: exited rc={second.returncode} after {fail_time:.3f}s")
    for line in err.strip().splitlines():
        if "Error" in line or "error" in line:
            print("  stderr:", line.strip())
    print(f"errno.EADDRINUSE on this platform: {errno.EADDRINUSE}")
    print(f"first instance still serving: {still_up}")

    assert second.returncode != 0, "second instance did not fail"
    assert str(errno.EADDRINUSE) in err, \
        f"expected errno {errno.EADDRINUSE} in stderr, got: {err[-400:]}"
    assert still_up, "first instance stopped serving after the collision"
    print("PASS: fails fast, fails loudly, first instance unharmed")


if __name__ == "__main__":
    main()
