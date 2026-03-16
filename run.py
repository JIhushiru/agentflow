"""Start both backend and frontend dev servers with a single command."""

import subprocess
import sys
import os
import signal
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT, "frontend")


def main():
    procs = []

    try:
        # Backend: uvicorn
        backend = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
            cwd=ROOT,
        )
        procs.append(backend)
        print("[agentflow] Backend started on http://localhost:8000")

        # Give backend a moment to start before frontend
        time.sleep(1)

        # Frontend: npm run dev
        frontend = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=FRONTEND_DIR,
            shell=True,
        )
        procs.append(frontend)
        print("[agentflow] Frontend started on http://localhost:5173")

        print("[agentflow] Press Ctrl+C to stop both servers\n")

        # Wait for either to exit
        while all(p.poll() is None for p in procs):
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[agentflow] Shutting down...")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            p.wait(timeout=5)
        print("[agentflow] Stopped.")


if __name__ == "__main__":
    main()
