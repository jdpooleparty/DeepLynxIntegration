import uvicorn
from pathlib import Path

if __name__ == "__main__":
    # Get the directory containing this file
    BASE_DIR = Path(__file__).resolve().parent
    ENV_FILE = BASE_DIR / '.env'

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="debug",
        env_file=str(ENV_FILE)
    ) 