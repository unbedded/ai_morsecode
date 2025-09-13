"""Entry point for running morsecode as a module via 'python -m morsecode'."""

from .cli import main

if __name__ == "__main__":
    exit(main())
