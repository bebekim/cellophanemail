"""Main entry point for running SMTP server standalone."""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())