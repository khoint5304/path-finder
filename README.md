# path-finder

Google Maps wannabe

## Setup and run

- Install dependencies

```bash
pip install -r requirements.txt
```

- Compile C++ source files by running `scripts/build.sh` in Linux or `scripts/build.bat` in Windows.
- Start application server at `http://localhost:8000`:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Screenshots

![Screenshot](samples/screenshot.png)
