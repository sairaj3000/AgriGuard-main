import subprocess
import webbrowser
import time
import sys
import os

def run_project():
    try:
        # 1. Start backend
        backend = subprocess.Popen([sys.executable, "flask_backend.py"])
        print("✅ Flask backend started...")

        # 2. Start frontend (http.server)
        frontend = subprocess.Popen([sys.executable, "-m", "http.server", "8000"])
        print("✅ Frontend server started on port 8000...")

        # 3. Give servers some time to start
        time.sleep(3)

        # 4. Open browser automatically
        url = "http://localhost:8000/dashboard.html"
        webbrowser.open(url)
        print(f"🌐 Browser opened at {url}")

        print("\n🚀 Project is running. Press CTRL+C to stop.\n")

        # Keep script alive
        backend.wait()
        frontend.wait()
        #n

    except KeyboardInterrupt:
        print("\n🛑 Stopping project...")
        backend.terminate()
        frontend.terminate()
        print("✅ All processes stopped.")

if __name__ == "__main__":
    run_project()
