# Python Project Structure: src/ Layout vs Flat Layout

**Date**: 2025-08-09  
**Topic**: Python Project Architecture

## What I Learned

### What does "src" stand for?

**"src"** stands for **"source"** - it's a conventional name for the directory containing project source code. Not Python-specific; used across many languages (C, C++, Java, etc.).

## Two Common Python Project Structures

### Src Layout (Professional/Enterprise)
```
project/
├── src/
│   └── mypackage/          # Package root
│       ├── __init__.py
│       ├── core/
│       └── models/
├── tests/                  # Tests outside src/
├── main.py                 # Entry point
└── pyproject.toml
```

### Flat Layout (Simple/Development)
```
project/
├── mypackage/              # Package root at project root
│   ├── __init__.py
│   ├── core/
│   └── models/
├── tests/                  # Tests at project root
├── main.py                 # Entry point
└── pyproject.toml
```

## Key Benefits of src/ Layout

### 1. Import System Safety
**Problem with flat layout:**
```python
# Python might import from local directory instead of installed package
import mypackage.models  # Could be ./mypackage/ or installed package
```

**Solution with src/ layout:**
```python
# Python can't accidentally import from src/
import mypackage.models  # Always imports from installed package
```

### 2. Testing Isolation
- **src/ layout**: Tests run against the **installed** version
- **Flat layout**: Tests might run against **development** version

This catches packaging issues early!

### 3. Clean Package Distribution
- Build tools automatically find packages in src/
- No need to explicitly specify what to package
- Better for CI/CD pipelines

## When to Use Each

### Use **Flat Layout** when:
- Simple scripts or applications
- Rapid prototyping
- Internal tools not distributed
- Small web applications
- Learning/educational projects

### Use **src/ Layout** when:
- Creating reusable packages
- Professional/enterprise applications
- Libraries others will import
- Multiple deployment scenarios
- Team development requiring import consistency

## Why Professionals Prefer src/

1. **Deployment Safety**: Production runs the same tested code
2. **CI/CD Reliability**: Build pipelines test actual packages  
3. **Developer Onboarding**: Prevents accidental wrong imports
4. **Package Distribution**: Easy wheel/egg creation
5. **Import Discipline**: Forces proper import practices

## Real Example

- **cellophanemail** (this project): Uses src/ layout - appropriate for SaaS application needing robust packaging and deployment
- **garasade** (my other project): Uses flat layout - appropriate for Flask web app deployed as complete project

## Key Takeaway

Choice isn't about "better" vs "worse" - it's about **matching structure to purpose**:
- **src/ layout**: For packages, libraries, and applications needing robust packaging
- **Flat layout**: For applications and scripts where simplicity trumps packaging

Both structures have their place in different contexts!