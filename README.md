# Demucs Separator

A production-ready CLI and API wrapper around [Facebook's Demucs](https://github.com/facebookresearch/demucs) model for audio source separation. Separate any audio track into vocals, drums, bass, and other instruments with a single command.

## What is Demucs?

[Demucs](https://github.com/facebookresearch/demucs) is a state-of-the-art music source separation model developed by Meta (Facebook) AI Research. It uses a hybrid transformer architecture to decompose audio into individual stems:

- **Vocals** — singing voice, speech
- **Drums** — percussion, beats
- **Bass** — bass guitar, sub-bass
- **Other** — everything else (guitar, synths, strings, etc.)

### Where is Demucs used?

- **Music production** — isolate vocals for remixes, extract drum patterns
- **Karaoke** — remove vocals from any song
- **Podcasting** — separate speech from background music/noise
- **Video dubbing** — extract vocals for re-voicing in another language
- **DJ/mashups** — isolate acapellas and instrumentals
- **Transcription** — clean up speech by removing background music
- **Audio forensics** — isolate specific sound sources from recordings

### How Demucs is normally used

Without this repo, using Demucs requires:

```bash
# Install demucs and all dependencies (torch, torchaudio, etc.)
pip install demucs

# Run via command line (outputs to ./separated/htdemucs/trackname/)
python -m demucs input.wav

# Or use the demucs CLI
demucs input.wav --two-stems=vocals
```

**Problems with the default approach:**
1. Output goes to a deeply nested folder (`./separated/htdemucs/trackname/vocals.wav`)
2. No REST API for integration into web services
3. No Docker image for quick deployment
4. Stem selection requires knowing the exact CLI flags
5. No easy way to batch-process or integrate into pipelines
6. Model downloads are implicit (can fail silently)

### How this repo makes it easier

```bash
# Simple: just specify input, stems, and output directory
python separate.py song.mp3 --vocals-only --output ./output/
# → ./output/vocals.wav
# → ./output/other.wav

# Or run as a REST API
python server.py
curl -X POST http://localhost:8000/separate -F "file=@song.wav" -o stems.zip

# Or Docker — zero local setup
docker run -v $(pwd):/data demucs-separator /data/song.wav --vocals-only --output /data/output/
```

**What this repo provides:**
- Clean output paths (flat directory, named by stem)
- REST API with file upload → zip download
- Docker container (reproducible, no dependency hell)
- Stem selection via simple flags (`--vocals-only`, `--stems vocals,drums`)
- Model selection (`--model htdemucs_ft` for better quality)
- Proper error handling and progress reporting
- 25 unit tests for CI/CD integration

---

## Features

- **CLI tool** — one command to separate any audio file
- **FastAPI server** — programmatic access via HTTP (upload file → get stems)
- **Docker support** — zero-setup deployment (CPU inference, no GPU required)
- **Any audio format** — WAV, MP3, FLAC, M4A, OGG, and anything ffmpeg supports
- **Multiple models** — choose quality vs speed tradeoff
- **Tested** — 25 unit tests covering CLI, API, and edge cases

---

## Installation

### Option A: Conda (recommended)

```bash
# Clone the repository
git clone https://github.com/SciTechDude/demucs-separator.git
cd demucs-separator

# Create dedicated conda environment
conda create -n demucs python=3.11 -y
conda activate demucs

# Install dependencies
pip install -r requirements.txt
```

### Option B: pip (existing environment)

```bash
git clone https://github.com/SciTechDude/demucs-separator.git
cd demucs-separator
pip install -r requirements.txt
```

### Option C: Docker (no local setup needed)

```bash
docker build -t demucs-separator .
docker run -v $(pwd):/data demucs-separator /data/input.wav --vocals-only --output /data/output/
```

### System Requirements

- Python 3.9+
- ffmpeg (for audio format conversion)
- ~2GB disk for model weights (downloaded automatically on first run)
- 4GB+ RAM recommended (8GB+ for longer audio files)

Install ffmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows (via chocolatey)
choco install ffmpeg
```

---

## Usage

### CLI

```bash
# Separate all stems (vocals, drums, bass, other)
python separate.py input.wav --output ./output/

# Extract only vocals and accompaniment (most common use case)
python separate.py input.mp3 --vocals-only

# Select specific stems
python separate.py input.flac --stems vocals,drums,bass --output ./stems/

# Use fine-tuned model for better quality (slower)
python separate.py input.wav --model htdemucs_ft --output ./hq_output/

# Use MDX model (alternative architecture)
python separate.py input.wav --model mdx_extra
```

#### CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `input` | Path to input audio file | (required) |
| `--stems` | Comma-separated stems to extract | all (vocals,drums,bass,other) |
| `--vocals-only` | Shortcut for vocals + other only | false |
| `--output` | Output directory | `./output/` |
| `--model` | Model to use | `htdemucs` |

### API Server

```bash
# Start the server
python server.py

# Or with uvicorn directly (with custom host/port)
uvicorn server:app --host 0.0.0.0 --port 8000
```

Then send requests:

```bash
# Health check
curl http://localhost:8000/health

# Separate all stems, get back a zip file
curl -X POST http://localhost:8000/separate \
  -F "file=@song.wav" \
  -o stems.zip

# Vocals only
curl -X POST http://localhost:8000/separate \
  -F "file=@song.wav" \
  -F "vocals_only=true" \
  -o vocals.zip

# Custom stems and model
curl -X POST http://localhost:8000/separate \
  -F "file=@track.mp3" \
  -F "stems=vocals,bass" \
  -F "model=htdemucs_ft" \
  -o output.zip
```

Interactive API docs available at `http://localhost:8000/docs` when the server is running.

### Docker

```bash
# Build the image
docker build -t demucs-separator .

# Run the API server
docker run -p 8000:8000 demucs-separator

# Run CLI via Docker (mount local directory for I/O)
docker run -v $(pwd):/data demucs-separator \
  python separate.py /data/song.wav --output /data/output/
```

---

## Models

| Model | Quality | Speed | Best for |
|-------|---------|-------|----------|
| `htdemucs` | Good | Fast | General use, quick results |
| `htdemucs_ft` | Better | Slower | High-quality separation, final output |
| `mdx_extra` | Good | Medium | Alternative architecture, music-focused |

All models are downloaded automatically on first use (~800MB-1.5GB per model). Models are cached in `~/.cache/torch/hub/`.

---

## Testing

```bash
# Install test dependencies
pip install pytest httpx

# Run all tests
pytest tests/ -v

# Run only CLI tests
pytest tests/test_cli.py -v

# Run only API tests
pytest tests/test_api.py -v
```

All 25 tests use mocked audio (no real model inference needed) — tests run in ~3 seconds.

---

## Tested Environment

| Component | Version |
|-----------|---------|
| OS | macOS 15.5 (Darwin 25.5.0, Apple M4 Pro) |
| Python | 3.11 |
| Conda | miniconda3 |
| Demucs | 4.1+ |
| PyTorch | 2.13.0 |
| ffmpeg | 7.x |
| FastAPI | 0.100+ |

Also tested on:
- Ubuntu 22.04 (x86_64) with CPU-only inference
- Docker (python:3.11-slim base image)

---

## Project Structure

```
demucs-separator/
├── README.md           ← This file
├── LICENSE             ← MIT License
├── requirements.txt    ← Python dependencies
├── Dockerfile          ← Container build file
├── .gitignore
├── separate.py         ← CLI entry point
├── server.py           ← FastAPI server
├── tests/
│   ├── conftest.py     ← Test fixtures (generates synthetic audio)
│   ├── test_cli.py     ← CLI argument parsing + separation tests (18 tests)
│   └── test_api.py     ← API endpoint tests (7 tests)
└── examples/
    └── README.md       ← Additional usage examples
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [Demucs](https://github.com/facebookresearch/demucs) by Meta (Facebook) AI Research — the core separation model
- [FastAPI](https://fastapi.tiangolo.com/) by Sebastian Ramirez — the API framework
- [PyTorch](https://pytorch.org/) — the deep learning framework powering Demucs

---

## Contributing

Contributions welcome! Please open an issue first to discuss what you'd like to change.

```bash
# Setup development environment
conda create -n demucs python=3.11 -y
conda activate demucs
pip install -r requirements.txt
pip install pytest httpx

# Run tests before submitting PR
pytest tests/ -v
```
