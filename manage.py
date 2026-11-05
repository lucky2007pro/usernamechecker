#!/usr/bin/env python3
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def load_dotenv_fallback() -> None:
    """python-dotenv o'rnatilmagan bo'lsa ham .env faylni o'qiydigan himoya funksiyasi."""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
    except ImportError:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)


def main() -> None:
    """Run administrative tasks."""
    load_dotenv_fallback()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django topilmadi! Terminalda 'pip install django telethon python-dotenv' buyrug'ini ishga tushiring."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
