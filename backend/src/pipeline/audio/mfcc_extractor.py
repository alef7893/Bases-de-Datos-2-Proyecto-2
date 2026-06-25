"""MFCC descriptor extraction with per-audio checkpoint files."""

from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np

from .preprocessing import load_audio


class MFCCExtractor:
    def __init__(
        self,
        sample_rate: int = 22050,
        n_mfcc: int = 20,
        n_fft: int = 2048,
        hop_length: int = 512,
        max_duration: float | None = None,
    ) -> None:
        if min(sample_rate, n_mfcc, n_fft, hop_length) <= 0:
            raise ValueError("MFCC extraction parameters must be positive")

        self.sample_rate = sample_rate
        self.n_mfcc = n_mfcc
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.max_duration = max_duration

    def extract_path(self, path: str | Path) -> np.ndarray:
        """
        Extract MFCC descriptors from an audio file.

        Returns
        -------
        np.ndarray:
            Matrix with shape (n_frames, n_mfcc).
        """
        signal, sr = load_audio(
            path,
            sample_rate=self.sample_rate,
            mono=True,
            max_duration=self.max_duration,
        )

        mfcc = librosa.feature.mfcc(
            y=signal,
            sr=sr,
            n_mfcc=self.n_mfcc,
            n_fft=min(self.n_fft, len(signal)),
            hop_length=self.hop_length,
        )

        descriptors = mfcc.T

        if descriptors.size == 0:
            return np.empty((0, self.n_mfcc), dtype=np.float32)

        descriptors = np.nan_to_num(descriptors, nan=0.0, posinf=0.0, neginf=0.0)

        return descriptors.astype(np.float32, copy=False)

    def extract_with_checkpoint(
        self,
        audio_id: int | str,
        audio_path: str | Path,
        checkpoint_dir: str | Path,
    ) -> np.ndarray:
        """
        Extract MFCC descriptors and cache them as .npy files.
        """
        output = Path(checkpoint_dir)
        output.mkdir(parents=True, exist_ok=True)

        safe_audio_id = str(audio_id).replace("/", "_").replace("\\", "_")
        checkpoint = output / f"{safe_audio_id}.npy"

        if checkpoint.is_file():
            return np.load(checkpoint, allow_pickle=False)

        descriptors = self.extract_path(audio_path)
        np.save(checkpoint, descriptors, allow_pickle=False)

        return descriptors