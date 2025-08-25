"""
Audio Enhancement System for TTS Live2D Integration

Provides audio quality optimization including noise reduction, vowel enhancement,
and volume normalization for improved lip-sync accuracy. Based on todo specifications Phase 8.5.
"""

import numpy as np
import librosa
import scipy.signal
import scipy.ndimage
from typing import Optional, Dict, Any, Tuple, Union
import logging
import io
import tempfile
import os
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AudioFormat(Enum):
    """Supported audio formats"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"


class EnhancementLevel(Enum):
    """Audio enhancement intensity levels"""
    LIGHT = 0.3
    MODERATE = 0.6
    STRONG = 0.9
    MAXIMUM = 1.2


@dataclass
class AudioEnhancementConfig:
    """Configuration for audio enhancement"""
    # Noise reduction
    noise_reduction_level: float = 0.7
    spectral_floor: float = 0.1
    
    # Vowel enhancement
    vowel_enhancement_level: float = 0.6
    formant_boost_db: float = 3.0
    vowel_frequency_ranges: Dict[str, Tuple[int, int]] = None
    
    # Volume normalization
    target_lufs: float = -23.0  # EBU R128 standard
    peak_ceiling_db: float = -3.0
    dynamic_range_compression: float = 0.3
    
    # General processing
    sample_rate: int = 44100
    preserve_dynamics: bool = True
    enhance_clarity: bool = True
    
    def __post_init__(self):
        if self.vowel_frequency_ranges is None:
            # Korean vowel formant ranges for enhancement
            self.vowel_frequency_ranges = {
                "vowel_low": (200, 800),      # F1 range
                "vowel_mid": (800, 1800),     # F1-F2 transition
                "vowel_high": (1800, 3500),   # F2 range
                "consonant": (3500, 8000)     # Consonant clarity
            }


class NoiseReducer:
    """
    Advanced noise reduction for TTS audio.
    Uses spectral subtraction and Wiener filtering.
    """
    
    def __init__(self, config: AudioEnhancementConfig):
        self.config = config
        self.noise_profile = None
        
    def reduce_noise(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Apply noise reduction to audio signal.
        
        Args:
            audio: Input audio signal
            sample_rate: Audio sample rate
            
        Returns:
            np.ndarray: Noise-reduced audio
        """
        if len(audio) == 0:
            return audio
            
        # Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        # STFT for spectral processing
        stft = librosa.stft(audio, n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise spectrum from quiet portions
        noise_spectrum = self._estimate_noise_spectrum(magnitude)
        
        # Apply spectral subtraction
        enhanced_magnitude = self._spectral_subtraction(magnitude, noise_spectrum)
        
        # Wiener filtering for additional cleanup
        enhanced_magnitude = self._wiener_filter(enhanced_magnitude, noise_spectrum)
        
        # Reconstruct audio
        enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
        enhanced_audio = librosa.istft(enhanced_stft, hop_length=512)
        
        return enhanced_audio
    
    def _estimate_noise_spectrum(self, magnitude: np.ndarray) -> np.ndarray:
        """Estimate noise spectrum from quiet portions of audio"""
        # Find quiet frames (bottom 10% of energy)
        frame_energy = np.sum(magnitude**2, axis=0)
        quiet_threshold = np.percentile(frame_energy, 10)
        quiet_frames = magnitude[:, frame_energy <= quiet_threshold]
        
        if quiet_frames.shape[1] > 0:
            noise_spectrum = np.mean(quiet_frames, axis=1, keepdims=True)
        else:
            # Fallback: use overall minimum
            noise_spectrum = np.min(magnitude, axis=1, keepdims=True)
        
        # Smooth noise spectrum
        noise_spectrum = scipy.ndimage.gaussian_filter1d(noise_spectrum.flatten(), sigma=2)
        return noise_spectrum.reshape(-1, 1)
    
    def _spectral_subtraction(self, magnitude: np.ndarray, 
                            noise_spectrum: np.ndarray) -> np.ndarray:
        """Apply spectral subtraction for noise reduction"""
        alpha = self.config.noise_reduction_level
        beta = self.config.spectral_floor
        
        # Spectral subtraction formula
        enhanced_magnitude = magnitude - alpha * noise_spectrum
        
        # Apply spectral floor to prevent over-subtraction
        spectral_floor = beta * magnitude
        enhanced_magnitude = np.maximum(enhanced_magnitude, spectral_floor)
        
        return enhanced_magnitude
    
    def _wiener_filter(self, magnitude: np.ndarray, 
                      noise_spectrum: np.ndarray) -> np.ndarray:
        """Apply Wiener filtering for additional noise reduction"""
        # Estimate SNR
        signal_power = magnitude**2
        noise_power = noise_spectrum**2
        
        # Wiener filter
        wiener_gain = signal_power / (signal_power + noise_power + 1e-10)
        
        # Smooth gain to prevent artifacts
        wiener_gain = scipy.ndimage.gaussian_filter(wiener_gain, sigma=1.0)
        
        return magnitude * wiener_gain


class VowelEnhancer:
    """
    Vowel enhancement for improved lip-sync accuracy.
    Boosts formant frequencies and enhances vowel clarity.
    """
    
    def __init__(self, config: AudioEnhancementConfig):
        self.config = config
        
    def enhance_vowels(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Enhance vowel clarity in audio signal.
        
        Args:
            audio: Input audio signal
            sample_rate: Audio sample rate
            
        Returns:
            np.ndarray: Vowel-enhanced audio
        """
        if len(audio) == 0:
            return audio
        
        # Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        # STFT for frequency domain processing
        stft = librosa.stft(audio, n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Enhance formant regions
        enhanced_magnitude = self._enhance_formants(magnitude, sample_rate)
        
        # Apply selective emphasis
        enhanced_magnitude = self._apply_vowel_emphasis(enhanced_magnitude, sample_rate)
        
        # Reconstruct audio
        enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
        enhanced_audio = librosa.istft(enhanced_stft, hop_length=512)
        
        return enhanced_audio
    
    def _enhance_formants(self, magnitude: np.ndarray, sample_rate: int) -> np.ndarray:
        """Enhance formant frequencies for better vowel recognition"""
        freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=2048)
        enhanced_magnitude = magnitude.copy()
        
        boost_factor = 10**(self.config.formant_boost_db / 20.0)
        
        for freq_range_name, (f_low, f_high) in self.config.vowel_frequency_ranges.items():
            # Find frequency bins in range
            freq_mask = (freqs >= f_low) & (freqs <= f_high)
            
            if np.any(freq_mask):
                # Apply frequency-dependent boost
                frequency_weight = self._get_frequency_weight(freqs[freq_mask], f_low, f_high)
                boost = 1.0 + (boost_factor - 1.0) * self.config.vowel_enhancement_level * frequency_weight
                
                enhanced_magnitude[freq_mask, :] *= boost.reshape(-1, 1)
        
        return enhanced_magnitude
    
    def _get_frequency_weight(self, freqs: np.ndarray, f_low: float, f_high: float) -> np.ndarray:
        """Get frequency-dependent weighting for smooth enhancement"""
        # Gaussian weighting centered in the frequency range
        f_center = (f_low + f_high) / 2
        f_width = (f_high - f_low) / 4
        
        weight = np.exp(-((freqs - f_center) / f_width)**2)
        return weight
    
    def _apply_vowel_emphasis(self, magnitude: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply selective emphasis to vowel-dominant regions"""
        # Detect vowel-rich frames using spectral characteristics
        vowel_frames = self._detect_vowel_frames(magnitude, sample_rate)
        
        # Apply enhancement only to vowel frames
        enhanced_magnitude = magnitude.copy()
        enhancement_factor = 1.0 + self.config.vowel_enhancement_level * 0.5
        
        for frame_idx in range(magnitude.shape[1]):
            if vowel_frames[frame_idx]:
                enhanced_magnitude[:, frame_idx] *= enhancement_factor
        
        return enhanced_magnitude
    
    def _detect_vowel_frames(self, magnitude: np.ndarray, sample_rate: int) -> np.ndarray:
        """Detect frames containing strong vowel content"""
        freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=2048)
        
        # Calculate formant energy ratios
        f1_range = (200, 800)
        f2_range = (800, 1800)
        
        f1_mask = (freqs >= f1_range[0]) & (freqs <= f1_range[1])
        f2_mask = (freqs >= f2_range[0]) & (freqs <= f2_range[1])
        
        f1_energy = np.sum(magnitude[f1_mask, :], axis=0)
        f2_energy = np.sum(magnitude[f2_mask, :], axis=0)
        total_energy = np.sum(magnitude, axis=0)
        
        # Vowel detection based on formant energy concentration
        formant_ratio = (f1_energy + f2_energy) / (total_energy + 1e-10)
        vowel_threshold = np.percentile(formant_ratio, 60)  # Top 40% frames
        
        return formant_ratio > vowel_threshold


class VolumeNormalizer:
    """
    Intelligent volume normalization with dynamic range preservation.
    Implements EBU R128 loudness standards with lip-sync optimization.
    """
    
    def __init__(self, config: AudioEnhancementConfig):
        self.config = config
        
    def normalize_volume(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Normalize audio volume with dynamic range preservation.
        
        Args:
            audio: Input audio signal
            sample_rate: Audio sample rate
            
        Returns:
            np.ndarray: Volume-normalized audio
        """
        if len(audio) == 0:
            return audio
        
        # Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        # Calculate current loudness
        current_lufs = self._calculate_lufs(audio, sample_rate)
        
        # Calculate normalization gain
        target_lufs = self.config.target_lufs
        gain_db = target_lufs - current_lufs
        gain_linear = 10**(gain_db / 20.0)
        
        # Apply gain
        normalized_audio = audio * gain_linear
        
        # Apply peak limiting to prevent clipping
        normalized_audio = self._apply_peak_limiter(normalized_audio)
        
        # Apply gentle compression if enabled
        if self.config.dynamic_range_compression > 0:
            normalized_audio = self._apply_compression(normalized_audio)
        
        return normalized_audio
    
    def _calculate_lufs(self, audio: np.ndarray, sample_rate: int) -> float:
        """Calculate LUFS (Loudness Units Full Scale) using EBU R128"""
        # Simple LUFS approximation using RMS with K-weighting
        # This is a simplified version; full EBU R128 is more complex
        
        # Apply pre-filter (simplified K-weighting)
        filtered_audio = self._apply_k_weighting(audio, sample_rate)
        
        # Calculate gated loudness
        block_size = int(sample_rate * 0.4)  # 400ms blocks
        hop_size = int(sample_rate * 0.1)    # 100ms hop
        
        loudness_blocks = []
        for i in range(0, len(filtered_audio) - block_size, hop_size):
            block = filtered_audio[i:i + block_size]
            mean_square = np.mean(block**2)
            if mean_square > 0:
                loudness_blocks.append(mean_square)
        
        if not loudness_blocks:
            return -70.0  # Very quiet
        
        # Gating thresholds
        mean_loudness = np.mean(loudness_blocks)
        relative_gate = mean_loudness * 0.1  # -10 dB relative gate
        
        gated_blocks = [block for block in loudness_blocks if block > relative_gate]
        
        if gated_blocks:
            gated_mean = np.mean(gated_blocks)
            lufs = -0.691 + 10 * np.log10(gated_mean + 1e-10)
        else:
            lufs = -70.0
        
        return lufs
    
    def _apply_k_weighting(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply simplified K-weighting filter"""
        # Simplified K-weighting using high-shelf filter
        # Full K-weighting requires more complex filtering
        
        nyquist = sample_rate / 2
        high_shelf_freq = 1500 / nyquist
        
        # High-shelf filter coefficients (simplified)
        b, a = scipy.signal.iirfilter(2, high_shelf_freq, btype='highpass', 
                                    ftype='butter', output='ba')
        
        filtered = scipy.signal.filtfilt(b, a, audio)
        return filtered
    
    def _apply_peak_limiter(self, audio: np.ndarray) -> np.ndarray:
        """Apply peak limiter to prevent clipping"""
        peak_ceiling = 10**(self.config.peak_ceiling_db / 20.0)
        
        # Find peaks that exceed ceiling
        peak_indices = np.abs(audio) > peak_ceiling
        
        if np.any(peak_indices):
            # Apply soft limiting
            limited_audio = audio.copy()
            over_peak = limited_audio[peak_indices]
            
            # Soft clipping function
            sign = np.sign(over_peak)
            abs_over = np.abs(over_peak)
            limited_values = sign * (peak_ceiling * np.tanh(abs_over / peak_ceiling))
            
            limited_audio[peak_indices] = limited_values
            return limited_audio
        
        return audio
    
    def _apply_compression(self, audio: np.ndarray) -> np.ndarray:
        """Apply gentle dynamic range compression"""
        compression_ratio = self.config.dynamic_range_compression
        
        if compression_ratio <= 0:
            return audio
        
        # Simple RMS-based compression
        window_size = 1024
        hop_size = 512
        
        compressed_audio = audio.copy()
        
        for i in range(0, len(audio) - window_size, hop_size):
            window = audio[i:i + window_size]
            rms = np.sqrt(np.mean(window**2))
            
            if rms > 0.1:  # Only compress if signal is strong enough
                target_rms = rms * (1.0 - compression_ratio)
                gain = target_rms / (rms + 1e-10)
                compressed_audio[i:i + window_size] *= gain
        
        return compressed_audio


class AudioEnhancer:
    """
    Main audio enhancement system for TTS Live2D integration.
    
    Combines noise reduction, vowel enhancement, and volume normalization
    for optimal lip-sync performance and audio quality.
    """
    
    def __init__(self, config: AudioEnhancementConfig = None):
        """
        Initialize audio enhancer.
        
        Args:
            config: Enhancement configuration
        """
        self.config = config or AudioEnhancementConfig()
        self.noise_reducer = NoiseReducer(self.config)
        self.vowel_enhancer = VowelEnhancer(self.config)
        self.volume_normalizer = VolumeNormalizer(self.config)
        
        logger.info("AudioEnhancer initialized")
    
    def enhance_for_lipsync(self, audio_data: Union[np.ndarray, bytes], 
                           sample_rate: Optional[int] = None,
                           audio_format: str = "wav",
                           enhancement_level: EnhancementLevel = EnhancementLevel.MODERATE) -> bytes:
        """
        Enhance audio specifically for lip-sync optimization.
        
        Args:
            audio_data: Input audio (numpy array or bytes)
            sample_rate: Audio sample rate (if audio_data is numpy array)
            audio_format: Input audio format (if audio_data is bytes)
            enhancement_level: Enhancement intensity level
            
        Returns:
            bytes: Enhanced audio data
        """
        try:
            # Convert input to numpy array
            if isinstance(audio_data, bytes):
                audio, sr = self._load_audio_from_bytes(audio_data, audio_format)
            else:
                audio = audio_data
                sr = sample_rate or self.config.sample_rate
            
            # Scale enhancement based on level
            original_config = self.config
            self.config = self._scale_config_by_level(self.config, enhancement_level)
            
            # Enhancement pipeline optimized for lip-sync
            enhanced_audio = audio.copy()
            
            # 1. Noise reduction (essential for clean analysis)
            if self.config.noise_reduction_level > 0:
                enhanced_audio = self.noise_reducer.reduce_noise(enhanced_audio, sr)
            
            # 2. Vowel enhancement (critical for lip-sync accuracy)
            if self.config.vowel_enhancement_level > 0:
                enhanced_audio = self.vowel_enhancer.enhance_vowels(enhanced_audio, sr)
            
            # 3. Volume normalization (for consistent results)
            enhanced_audio = self.volume_normalizer.normalize_volume(enhanced_audio, sr)
            
            # Restore original config
            self.config = original_config
            
            # Convert back to bytes
            enhanced_bytes = self._audio_to_bytes(enhanced_audio, sr, "wav")
            
            logger.info(f"Audio enhanced for lip-sync: {len(audio)} -> {len(enhanced_audio)} samples")
            return enhanced_bytes
            
        except Exception as e:
            logger.error(f"Audio enhancement failed: {e}")
            # Return original audio if enhancement fails
            if isinstance(audio_data, bytes):
                return audio_data
            else:
                return self._audio_to_bytes(audio_data, sample_rate or self.config.sample_rate, "wav")
    
    def enhance_general_quality(self, audio_data: Union[np.ndarray, bytes],
                              sample_rate: Optional[int] = None,
                              audio_format: str = "wav") -> bytes:
        """
        General audio quality enhancement.
        
        Args:
            audio_data: Input audio
            sample_rate: Audio sample rate
            audio_format: Input audio format
            
        Returns:
            bytes: Enhanced audio data
        """
        return self.enhance_for_lipsync(audio_data, sample_rate, audio_format, 
                                      EnhancementLevel.LIGHT)
    
    def _load_audio_from_bytes(self, audio_bytes: bytes, format: str) -> Tuple[np.ndarray, int]:
        """Load audio from bytes data"""
        with tempfile.NamedTemporaryFile(suffix=f".{format}") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file.flush()
            
            audio, sr = librosa.load(tmp_file.name, sr=self.config.sample_rate)
            return audio, sr
    
    def _audio_to_bytes(self, audio: np.ndarray, sample_rate: int, format: str) -> bytes:
        """Convert numpy audio to bytes"""
        import soundfile as sf
        
        with tempfile.NamedTemporaryFile(suffix=f".{format}") as tmp_file:
            sf.write(tmp_file.name, audio, sample_rate)
            tmp_file.seek(0)
            return tmp_file.read()
    
    def _scale_config_by_level(self, config: AudioEnhancementConfig, 
                              level: EnhancementLevel) -> AudioEnhancementConfig:
        """Scale configuration parameters by enhancement level"""
        scale_factor = level.value
        
        # Create scaled config
        scaled_config = AudioEnhancementConfig(
            noise_reduction_level=config.noise_reduction_level * scale_factor,
            spectral_floor=config.spectral_floor,
            vowel_enhancement_level=config.vowel_enhancement_level * scale_factor,
            formant_boost_db=config.formant_boost_db * scale_factor,
            vowel_frequency_ranges=config.vowel_frequency_ranges,
            target_lufs=config.target_lufs,
            peak_ceiling_db=config.peak_ceiling_db,
            dynamic_range_compression=config.dynamic_range_compression * scale_factor,
            sample_rate=config.sample_rate,
            preserve_dynamics=config.preserve_dynamics,
            enhance_clarity=config.enhance_clarity
        )
        
        return scaled_config
    
    def analyze_audio_quality(self, audio_data: Union[np.ndarray, bytes],
                            sample_rate: Optional[int] = None,
                            audio_format: str = "wav") -> Dict[str, Any]:
        """
        Analyze audio quality metrics.
        
        Args:
            audio_data: Input audio
            sample_rate: Audio sample rate
            audio_format: Audio format
            
        Returns:
            Dict[str, Any]: Quality analysis results
        """
        try:
            # Convert to numpy array
            if isinstance(audio_data, bytes):
                audio, sr = self._load_audio_from_bytes(audio_data, audio_format)
            else:
                audio = audio_data
                sr = sample_rate or self.config.sample_rate
            
            # Calculate quality metrics
            metrics = {}
            
            # Basic metrics
            metrics["duration"] = len(audio) / sr
            metrics["sample_rate"] = sr
            metrics["samples"] = len(audio)
            
            # Level metrics
            metrics["rms_level"] = float(np.sqrt(np.mean(audio**2)))
            metrics["peak_level"] = float(np.max(np.abs(audio)))
            metrics["dynamic_range"] = float(metrics["peak_level"] / (metrics["rms_level"] + 1e-10))
            
            # Frequency analysis
            stft = librosa.stft(audio)
            magnitude = np.abs(stft)
            freqs = librosa.fft_frequencies(sr=sr)
            
            # Spectral metrics
            spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(S=magnitude)[0]))
            spectral_rolloff = float(np.mean(librosa.feature.spectral_rolloff(S=magnitude)[0]))
            
            metrics["spectral_centroid"] = spectral_centroid
            metrics["spectral_rolloff"] = spectral_rolloff
            
            # Vowel-relevant frequency analysis
            f1_range = (200, 800)
            f2_range = (800, 1800)
            
            f1_mask = (freqs >= f1_range[0]) & (freqs <= f1_range[1])
            f2_mask = (freqs >= f2_range[0]) & (freqs <= f2_range[1])
            
            f1_energy = float(np.mean(np.sum(magnitude[f1_mask, :], axis=0)))
            f2_energy = float(np.mean(np.sum(magnitude[f2_mask, :], axis=0)))
            
            metrics["f1_energy"] = f1_energy
            metrics["f2_energy"] = f2_energy
            metrics["formant_ratio"] = f2_energy / (f1_energy + 1e-10)
            
            # LUFS estimation
            metrics["estimated_lufs"] = self.volume_normalizer._calculate_lufs(audio, sr)
            
            # Quality score (0-100)
            quality_score = self._calculate_quality_score(metrics)
            metrics["quality_score"] = quality_score
            
            return metrics
            
        except Exception as e:
            logger.error(f"Audio quality analysis failed: {e}")
            return {"error": str(e)}
    
    def _calculate_quality_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score based on metrics"""
        score = 100.0
        
        # Penalize clipping
        if metrics["peak_level"] > 0.95:
            score -= 20
        
        # Penalize too quiet audio
        if metrics["rms_level"] < 0.01:
            score -= 15
        
        # Reward good dynamic range
        if 2 < metrics["dynamic_range"] < 10:
            score += 10
        elif metrics["dynamic_range"] > 20:
            score -= 10
        
        # Check spectral balance
        if 1000 < metrics["spectral_centroid"] < 3000:
            score += 5
        
        # Check formant clarity
        if 1.5 < metrics["formant_ratio"] < 4.0:
            score += 5
        
        return max(0.0, min(100.0, score))