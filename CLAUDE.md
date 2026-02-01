# Project Rules for Claude Code

## Environment Files

**NEVER automatically overwrite or modify `.env*` files** (`.env`, `.env.docker`, `.env.local`, etc.).

These files contain user-configured secrets and API keys. If environment changes are needed:
1. Inform the user what needs to be changed
2. Show them the exact line/value to update
3. Let them make the change manually

## Refactoring Safety Rules

**MANDATORY before any refactor that changes paths, names, or signatures:**

1. **Search for test impact FIRST:**
   ```bash
   grep -r "old_path_or_name" tests/
   ```

2. **Update tests BEFORE changing source code**
   - Tests should FAIL after update (proves they hit the code)
   - Make source change
   - Tests should PASS

3. **Verify after refactor:**
   ```bash
   uv run pytest tests/ -x
   ```

**Route Path Changes Checklist:**
- [ ] Searched `tests/` for old path
- [ ] Updated all test URLs
- [ ] Verified tests fail with new path (before source change)
- [ ] Made source change
- [ ] Verified tests pass

## Project Overview

CellophoneMail is an email protection service built with:
- Litestar (Python async web framework)
- PostgreSQL database
- Piccolo ORM for migrations
- Docker Compose for local development
