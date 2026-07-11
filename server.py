"""FastAPI server for audio source separation using Demucs."""

import io
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from separate import VALID_MODELS, VALID_STEMS, separate

app = FastAPI(
    title="Demucs Audio Separator",
    description="Audio source separation API powered by Facebook's Demucs model.",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/separate")
async def separate_audio(
    file: UploadFile = File(..., description="Audio file to separate"),
    stems: Optional[str] = Form(
        default=None,
        description="Comma-separated list of stems (vocals, drums, bass, other). Default: all stems.",
    ),
    model: str = Form(
        default="htdemucs",
        description="Demucs model to use (htdemucs, htdemucs_ft, mdx_extra).",
    ),
    vocals_only: bool = Form(
        default=False,
        description="If true, extract only vocals and other (accompaniment).",
    ),
):
    """Separate an audio file into stems and return as a zip archive.

    Upload an audio file (wav, mp3, flac, m4a, etc.) and receive a zip file
    containing the separated stems as WAV files.
    """
    # Validate model
    if model not in VALID_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model: {model}. Valid models: {', '.join(sorted(VALID_MODELS))}",
        )

    # Determine selected stems
    if vocals_only:
        selected_stems = ["vocals", "other"]
    elif stems:
        selected_stems = [s.strip().lower() for s in stems.split(",")]
        invalid = set(selected_stems) - VALID_STEMS
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stem(s): {', '.join(invalid)}. Valid: {', '.join(sorted(VALID_STEMS))}",
            )
    else:
        selected_stems = sorted(VALID_STEMS)

    # Save uploaded file to temporary location
    tmp_dir = tempfile.mkdtemp()
    try:
        # Preserve original file extension for ffmpeg compatibility
        suffix = Path(file.filename).suffix if file.filename else ".wav"
        input_path = os.path.join(tmp_dir, f"input{suffix}")

        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Run separation
        output_dir = os.path.join(tmp_dir, "output")
        output_files = separate(input_path, output_dir, model, selected_stems)

        if not output_files:
            raise HTTPException(
                status_code=500,
                detail="Separation produced no output files.",
            )

        # Create zip archive in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filepath in output_files:
                arcname = os.path.basename(filepath)
                zf.write(filepath, arcname)

        zip_buffer.seek(0)

        # Determine output filename
        input_name = Path(file.filename).stem if file.filename else "separated"
        zip_filename = f"{input_name}_stems.zip"

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'},
        )

    finally:
        # Clean up temporary files
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
