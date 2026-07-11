# Demucs Separator

A CLI and API wrapper around [Facebook's Demucs](https://github.com/facebookresearch/demucs) model for audio source separation. Separate any audio track into vocals, drums, bass, and other instruments with a single command.

## Features

- **CLI tool** for quick local separation
- **FastAPI server** for programmatic access via HTTP
- **Docker support** for easy deployment (CPU inference, no GPU required)
- Supports any audio format that ffmpeg can read (WAV, MP3, FLAC, M4A, etc.)
- Choose between multiple Demucs models (`htdemucs`, `htdemucs_ft`, `mdx_extra`)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/demucs-separator.git
cd demucs-separator

# Install dependencies
pip install -r requirements.txt
```

### System Requirements

- Python 3.9+
- ffmpeg (for audio format conversion)

Install ffmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows (via chocolatey)
choco install ffmpeg
```

## Usage

### CLI

```bash
# Separate all stems
python separate.py input.wav --output ./output/

# Extract only vocals and accompaniment
python separate.py input.mp3 --vocals-only

# Select specific stems
python separate.py input.flac --stems vocals,drums,bass --output ./stems/

# Use a fine-tuned model for better quality
python separate.py input.wav --model htdemucs_ft
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

# Or with uvicorn directly
uvicorn server:app --host 0.0.0.0 --port 8000
```

Then send requests:

```bash
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

API docs are available at `http://localhost:8000/docs` when the server is running.

### Docker

```bash
# Build the image
docker build -t demucs-separator .

# Run the API server
docker run -p 8000:8000 demucs-separator

# Run CLI via Docker
docker run -v $(pwd):/data demucs-separator \
  python separate.py /data/song.wav --output /data/output/
```

## Models

| Model | Quality | Speed | Description |
|-------|---------|-------|-------------|
| `htdemucs` | Good | Fast | Default hybrid transformer model |
| `htdemucs_ft` | Better | Slower | Fine-tuned version with improved separation |
| `mdx_extra` | Good | Medium | MDX architecture, good for music |

## Testing

```bash
pip install pytest httpx
pytest tests/ -v
```

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
│   ├── conftest.py     ← Test fixtures
│   ├── test_cli.py     ← CLI tests
│   └── test_api.py     ← API tests
└── examples/
    └── README.md       ← Usage examples
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

- [Demucs](https://github.com/facebookresearch/demucs) by Facebook Research
- [FastAPI](https://fastapi.tiangolo.com/) by Sebastian Ramirez
