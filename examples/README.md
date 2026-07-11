# Examples

## CLI Usage

### Separate all stems (default)

```bash
python separate.py song.wav
```

This produces `output/vocals.wav`, `output/drums.wav`, `output/bass.wav`, and `output/other.wav`.

### Extract vocals only

```bash
python separate.py song.mp3 --vocals-only --output ./vocals_output/
```

### Specific stems

```bash
python separate.py track.flac --stems vocals,drums --output ./stems/
```

### Use a different model

```bash
python separate.py song.wav --model htdemucs_ft
```

`htdemucs_ft` is a fine-tuned version that may produce better results at the cost of longer processing time.

## API Usage

### Start the server

```bash
python server.py
# or
uvicorn server:app --host 0.0.0.0 --port 8000
```

### Separate audio via API

```bash
# All stems
curl -X POST http://localhost:8000/separate \
  -F "file=@song.wav" \
  -o stems.zip

# Vocals only
curl -X POST http://localhost:8000/separate \
  -F "file=@song.wav" \
  -F "vocals_only=true" \
  -o vocals.zip

# Specific stems with a different model
curl -X POST http://localhost:8000/separate \
  -F "file=@song.mp3" \
  -F "stems=vocals,bass" \
  -F "model=htdemucs_ft" \
  -o selected_stems.zip
```

### Health check

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

## Docker Usage

### Build and run

```bash
docker build -t demucs-separator .
docker run -p 8000:8000 demucs-separator
```

### CLI via Docker

```bash
docker run -v $(pwd):/data demucs-separator \
  python separate.py /data/song.wav --output /data/output/
```

## Supported Formats

Any audio format supported by ffmpeg works as input:
- WAV
- MP3
- FLAC
- M4A/AAC
- OGG/Vorbis
- And many more

Output is always WAV (uncompressed, highest quality).
