from pathlib import Path

from dotenv import load_dotenv


def load_env():
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    load_dotenv(env_path)
