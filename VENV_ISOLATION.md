# Virtual Environment Isolation Guide

## Why Isolated Virtual Environments?

By using a virtual environment, **ALL** LangChain dependencies are installed **ONLY** in the project's `./venv/` folder. Nothing touches your global Python installation.

## Current Status

✅ **All LangChain libraries are isolated to `./venv/`**
- langchain
- langchain-openai
- langchain-community
- pydantic
- python-dotenv
- All dependencies

## Verify Isolation

### Check what's in the venv (should have everything):
```powershell
# Windows
.\venv\Scripts\python -m pip list | findstr langchain
```

```bash
# Linux/macOS
./venv/bin/python -m pip list | grep langchain
```

### Check global Python (should be clean):
```powershell
# Windows
python -m pip list | findstr langchain
```

```bash
# Linux/macOS
python -m pip list | grep langchain
```

Should return NOTHING if properly isolated.

## Clean Up Global Python

If you accidentally installed packages globally:

**Windows:**
```powershell
.\cleanup-global.ps1
```

**Linux/macOS:**
```bash
chmod +x cleanup-global.sh
./cleanup-global.sh
```

This removes all LangChain packages from global Python, ensuring they're ONLY in venv.

## Running the Project

Always use the venv's Python:

**Correct (uses venv isolation):**
```powershell
.\venv\Scripts\python main.py    # Windows
./venv/bin/python main.py        # Linux/macOS
```

Or activate venv first:
```powershell
.\venv\Scripts\Activate.ps1      # Windows
source venv/bin/activate         # Linux/macOS
python main.py
```

**Wrong (would use global Python if installed there):**
```powershell
python main.py  # Don't do this - might use global Python
```

## Directory Structure

```
LangRover/
├── venv/                    # ISOLATED virtual environment
│   ├── lib/
│   │   └── site-packages/
│   │       ├── langchain/
│   │       ├── pydantic/
│   │       └── ... all packages ONLY here
│   └── Scripts/
│       ├── python.exe
│       ├── pip.exe
│       └── Activate.ps1
│
├── main.py
├── requirements.txt
└── ...
```

**Everything in `venv/` is project-isolated. Global Python stays clean!**

## Best Practices

1. ✅ Always activate venv before working on project
2. ✅ Run `pip install` only inside activated venv
3. ✅ Use `./venv/Scripts/python` for explicit isolation
4. ✅ Don't use global Python for this project
5. ✅ Use `cleanup-global.ps1` if you need to remove global packages

## Summary

| Location | Usage |
|----------|-------|
| `./venv/lib/site-packages/` | All project dependencies **ISOLATED** |
| Global Python site-packages | Clean, untouched |
| `python main.py` | Don't use - might use global |
| `./venv/Scripts/python main.py` | ✅ Correct - uses venv |
| `./run.ps1` | ✅ Correct - uses venv automatically |

**Your global Python environment stays completely clean!**
