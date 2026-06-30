import subprocess
import sys
from pathlib import Path


def main():
    app_path = Path(__file__).resolve().parent / "app" / "streamlit_app.py"
    sys.exit(
        subprocess.call(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(app_path),
                "--server.address=0.0.0.0",
                "--server.port=8501",
            ]
        )
    )


if __name__ == "__main__":
    main()
