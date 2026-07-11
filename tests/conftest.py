"""Shared test fixtures for demucs-separator tests."""

import os
import struct
import tempfile
import wave

import pytest


@pytest.fixture
def test_audio_path():
    """Generate a short sine wave WAV file for testing.

    Creates a 1-second mono 44100Hz 16-bit WAV file with a 440Hz sine wave.
    """
    import math

    sample_rate = 44100
    duration = 1.0  # seconds
    frequency = 440.0  # Hz
    amplitude = 16000

    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        value = int(amplitude * math.sin(2 * math.pi * frequency * t))
        samples.append(value)

    # Write WAV file
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "w") as wf:
        wf.setnchannels(2)  # stereo (demucs expects stereo)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        # Duplicate mono to stereo
        for sample in samples:
            packed = struct.pack("<h", sample)
            wf.writeframes(packed + packed)

    yield tmp.name

    # Cleanup
    os.unlink(tmp.name)


@pytest.fixture
def output_dir():
    """Provide a temporary output directory."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    # Cleanup is handled by the OS for temp dirs
    import shutil

    shutil.rmtree(tmp_dir, ignore_errors=True)
