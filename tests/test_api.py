"""Tests for the FastAPI server endpoints."""

import io
import os
import sys
import zipfile
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def audio_bytes(test_audio_path):
    """Read the test audio fixture as bytes."""
    with open(test_audio_path, "rb") as f:
        return f.read()


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSeparateEndpoint:
    """Test the /separate endpoint."""

    @patch("server.separate")
    def test_separate_returns_zip(self, mock_separate, client, audio_bytes, tmp_path):
        # Create fake output files
        vocals_path = str(tmp_path / "vocals.wav")
        other_path = str(tmp_path / "other.wav")
        with open(vocals_path, "wb") as f:
            f.write(b"fake vocals wav data")
        with open(other_path, "wb") as f:
            f.write(b"fake other wav data")

        mock_separate.return_value = [vocals_path, other_path]

        response = client.post(
            "/separate",
            files={"file": ("test.wav", audio_bytes, "audio/wav")},
            data={"vocals_only": "true"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert "test_stems.zip" in response.headers["content-disposition"]

        # Verify it's a valid zip
        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            names = zf.namelist()
            assert "vocals.wav" in names
            assert "other.wav" in names

    @patch("server.separate")
    def test_separate_with_custom_stems(self, mock_separate, client, audio_bytes, tmp_path):
        drums_path = str(tmp_path / "drums.wav")
        with open(drums_path, "wb") as f:
            f.write(b"fake drums wav data")
        mock_separate.return_value = [drums_path]

        response = client.post(
            "/separate",
            files={"file": ("song.mp3", audio_bytes, "audio/mpeg")},
            data={"stems": "drums", "model": "htdemucs_ft"},
        )

        assert response.status_code == 200
        mock_separate.assert_called_once()
        call_kwargs = mock_separate.call_args
        # Check model was passed correctly
        assert call_kwargs[0][2] == "htdemucs_ft"
        assert call_kwargs[0][3] == ["drums"]

    def test_separate_invalid_model(self, client, audio_bytes):
        response = client.post(
            "/separate",
            files={"file": ("test.wav", audio_bytes, "audio/wav")},
            data={"model": "invalid_model"},
        )

        assert response.status_code == 400
        assert "Invalid model" in response.json()["detail"]

    def test_separate_invalid_stems(self, client, audio_bytes):
        response = client.post(
            "/separate",
            files={"file": ("test.wav", audio_bytes, "audio/wav")},
            data={"stems": "vocals,invalid_stem"},
        )

        assert response.status_code == 400
        assert "Invalid stem" in response.json()["detail"]

    @patch("server.separate")
    def test_separate_no_output_files(self, mock_separate, client, audio_bytes):
        mock_separate.return_value = []

        response = client.post(
            "/separate",
            files={"file": ("test.wav", audio_bytes, "audio/wav")},
        )

        assert response.status_code == 500
        assert "no output" in response.json()["detail"].lower()

    @patch("server.separate")
    def test_separate_default_all_stems(self, mock_separate, client, audio_bytes, tmp_path):
        # Create fake output files for all stems
        paths = []
        for stem in ["bass", "drums", "other", "vocals"]:
            p = str(tmp_path / f"{stem}.wav")
            with open(p, "wb") as f:
                f.write(b"fake data")
            paths.append(p)
        mock_separate.return_value = paths

        response = client.post(
            "/separate",
            files={"file": ("test.wav", audio_bytes, "audio/wav")},
        )

        assert response.status_code == 200
        # Default should request all stems
        call_args = mock_separate.call_args[0]
        assert set(call_args[3]) == {"bass", "drums", "other", "vocals"}
