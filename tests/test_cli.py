"""Tests for the CLI interface (argument parsing and validation)."""

import os
import sys
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from separate import parse_args, validate_args, separate, VALID_STEMS, VALID_MODELS


class TestParseArgs:
    """Test argument parsing."""

    def test_minimal_args(self):
        args = parse_args(["input.wav"])
        assert args.input == "input.wav"
        assert args.stems is None
        assert args.vocals_only is False
        assert args.output == "./output"
        assert args.model == "htdemucs"

    def test_stems_flag(self):
        args = parse_args(["input.wav", "--stems", "vocals,drums"])
        assert args.stems == "vocals,drums"

    def test_vocals_only_flag(self):
        args = parse_args(["input.wav", "--vocals-only"])
        assert args.vocals_only is True

    def test_output_flag(self):
        args = parse_args(["input.wav", "--output", "/tmp/out"])
        assert args.output == "/tmp/out"

    def test_model_flag(self):
        args = parse_args(["input.wav", "--model", "htdemucs_ft"])
        assert args.model == "htdemucs_ft"

    def test_model_mdx_extra(self):
        args = parse_args(["input.wav", "--model", "mdx_extra"])
        assert args.model == "mdx_extra"

    def test_invalid_model_rejected(self):
        with pytest.raises(SystemExit):
            parse_args(["input.wav", "--model", "invalid_model"])

    def test_stems_and_vocals_only_mutually_exclusive(self):
        with pytest.raises(SystemExit):
            parse_args(["input.wav", "--stems", "vocals", "--vocals-only"])


class TestValidateArgs:
    """Test argument validation."""

    def test_nonexistent_input_exits(self, tmp_path):
        args = parse_args(["nonexistent_file.wav"])
        with pytest.raises(SystemExit):
            validate_args(args)

    def test_valid_input_file(self, test_audio_path):
        args = parse_args([test_audio_path])
        validated = validate_args(args)
        assert validated.selected_stems == sorted(VALID_STEMS)

    def test_vocals_only_selects_correct_stems(self, test_audio_path):
        args = parse_args([test_audio_path, "--vocals-only"])
        validated = validate_args(args)
        assert set(validated.selected_stems) == {"vocals", "other"}

    def test_custom_stems_parsed(self, test_audio_path):
        args = parse_args([test_audio_path, "--stems", "vocals,bass"])
        validated = validate_args(args)
        assert set(validated.selected_stems) == {"vocals", "bass"}

    def test_invalid_stem_exits(self, test_audio_path):
        args = parse_args([test_audio_path, "--stems", "vocals,invalid"])
        with pytest.raises(SystemExit):
            validate_args(args)

    def test_stems_whitespace_handling(self, test_audio_path):
        args = parse_args([test_audio_path, "--stems", " vocals , drums "])
        validated = validate_args(args)
        assert set(validated.selected_stems) == {"vocals", "drums"}


class TestSeparateFunction:
    """Test the separate function with mocked subprocess."""

    @patch("separate.subprocess.run")
    @patch("separate.shutil.copy2")
    @patch("separate.os.path.isdir")
    @patch("separate.os.path.isfile")
    def test_separate_calls_demucs(
        self, mock_isfile, mock_isdir, mock_copy, mock_run, test_audio_path, output_dir
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        mock_isdir.return_value = True
        mock_isfile.side_effect = lambda p: p == test_audio_path or p.endswith(".wav")

        separate(test_audio_path, output_dir, "htdemucs", ["vocals"])

        # Verify demucs was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "-m" in call_args
        assert "demucs" in call_args
        assert "--name" in call_args
        assert "htdemucs" in call_args

    @patch("separate.subprocess.run")
    def test_separate_handles_demucs_error(self, mock_run, test_audio_path, output_dir):
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(
            1, "demucs", stderr="Model error"
        )

        with pytest.raises(SystemExit):
            separate(test_audio_path, output_dir, "htdemucs", ["vocals"])


class TestConstants:
    """Test module constants."""

    def test_valid_stems(self):
        assert VALID_STEMS == {"vocals", "drums", "bass", "other"}

    def test_valid_models(self):
        assert "htdemucs" in VALID_MODELS
        assert "htdemucs_ft" in VALID_MODELS
        assert "mdx_extra" in VALID_MODELS
