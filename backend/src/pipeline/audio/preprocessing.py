"""Audio loading and preprocessing utilities."""

from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np


def load_audio(
    path: str | Path,
    sample_rate: int = 22050,
    mono: bool = True,
    max_duration: float | None = None,
) -> tuple[np.ndarray, int]:
    """
    Load an audio file as a float32 signal.

    Parameters
    ----------
    path:
        Audio file path.
    sample_rate:
        Target sampling rate.
    mono:
        Whether to convert the audio to mono.
    max_duration:
        Optional maximum duration in seconds.

    Returns
    -------
    signal, sr:
        Preprocessed audio signal and sampling rate.
    """
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")

    audio_path = Path(path)

    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    signal, sr = librosa.load(
        audio_path,
        sr=sample_rate,
        mono=mono,
        duration=max_duration,
    )

    if signal.size == 0:
        raise ValueError(f"Audio file is empty or could not be loaded: {audio_path}")

    return signal.astype(np.float32, copy=False), int(sr)