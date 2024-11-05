from pathlib import Path

# Get the directory containing config file
BASE_DIR = Path(__file__).resolve().parent

config = {
    "app": "src.main:app",
    "host": "0.0.0.0",
    "port": 5000,
    "reload": True,
    "log_level": "debug",
    "env_file": str(BASE_DIR / '.env')
} 