# Project Rules for Claude Code

## Environment Files

**NEVER automatically overwrite or modify `.env*` files** (`.env`, `.env.docker`, `.env.local`, etc.).

These files contain user-configured secrets and API keys. If environment changes are needed:
1. Inform the user what needs to be changed
2. Show them the exact line/value to update
3. Let them make the change manually

## Project Overview

CellophoneMail is an email protection service built with:
- Litestar (Python async web framework)
- PostgreSQL database
- Piccolo ORM for migrations
- Docker Compose for local development
