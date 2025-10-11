import asyncio
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv


def load_env():
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    load_dotenv(env_path)


def with_env(func):
    """
    Decorator that automatically loads environment variables before
    running the function. Use this to decorate your main()
    functions to avoid manually calling load_env().
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        load_env()
        return await func(*args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        load_env()
        return func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
