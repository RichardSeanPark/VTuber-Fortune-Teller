"""
Lip-sync Analysis System for TTS Live2D Integration

Provides audio frequency analysis and Live2D mouth parameter mapping
for real-time lip-sync animation based on todo specifications Phase 8.2.
"""

import asyncio
import numpy as np
import librosa
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import scipy.signal
import tempfile
import os

logger = logging.getLogger(__name__)


class VowelType(Enum):
    """Korean vowel types for mouth shape mapping"""
    A = "A"  # 아
    I = "I"  # 이
    U = "U"  # 우
    E = "E"  # 에
    O = "O"  # 오
    SILENCE = "SILENCE"
    CONSONANT = "CONSONANT"


@dataclass
class LipSyncFrame:
    """Single frame of lip-sync data"""
    timestamp: float
    vowel_type: VowelType
    intensity: float
    mouth_params: Dict[str, float]
    confidence: float


@dataclass
class LipSyncData:
    """Complete lip-sync data for audio clip"""
    frames: List[LipSyncFrame]
    duration: float
    sample_rate: int
    frame_rate: float
    analysis_method: str


class VowelClassifier:
    """
    Audio frequency analysis for vowel classification.
    Uses formant analysis for Korean vowel identification.
    """
    
    def __init__(self):
        # Korean vowel formant patterns (F1, F2 in Hz)
        self.vowel_formants = {
            VowelType.A: {"f1_range": (600, 900), "f2_range": (1100, 1400)},    # 아
            VowelType.I: {"f1_range": (200, 400), "f2_range": (2000, 2500)},    # 이
            VowelType.U: {"f1_range": (250, 450), "f2_range": (600, 1000)},     # 우
            VowelType.E: {"f1_range": (350, 600), "f2_range": (1400, 1800)},    # 에
            VowelType.O: {"f1_range": (350, 600), "f2_range": (700, 1100)},     # 오
        }
        
        # Analysis parameters
        self.sample_rate = 44100
        self.fft_size = 2048
        self.hop_length = 512
        self.window_size = 1024
        self.silence_threshold = 0.01
        
    def analyze_formants(self, audio_frame: np.ndarray) -> Tuple[float, float]:
        """
        Extract F1 and F2 formants from audio frame.
        
        Args:
            audio_frame: Audio data array
            
        Returns:
            Tuple[float, float]: F1 and F2 frequencies in Hz
        """
        # Apply pre-emphasis filter
        pre_emphasized = scipy.signal.lfilter([1, -0.97], [1], audio_frame)
        
        # Window the frame
        windowed = pre_emphasized * np.hanning(len(pre_emphasized))
        
        # LPC analysis for formant extraction
        try:
            # LPC coefficients (order 12 for good formant resolution)
            lpc_order = 12
            lpc_coeffs = librosa.lpc(windowed, order=lpc_order)
            
            # Find roots and convert to frequencies
            roots = np.roots(lpc_coeffs)
            
            # Extract formants from stable roots
            formants = []
            for root in roots:
                if np.abs(root) > 0.9:  # Stable pole
                    freq = np.angle(root) * self.sample_rate / (2 * np.pi)
                    if 50 < freq < 4000:  # Human speech range
                        formants.append(freq)
            
            formants.sort()
            
            # Return first two formants
            f1 = formants[0] if len(formants) > 0 else 500
            f2 = formants[1] if len(formants) > 1 else 1500
            
            return float(abs(f1)), float(abs(f2))  # numpy.float32 방지
            
        except Exception as e:
            logger.debug(f"Formant analysis failed: {e}")
            # Fallback to FFT peak finding
            return self._fallback_formant_analysis(windowed)
    
    def _fallback_formant_analysis(self, audio_frame: np.ndarray) -> Tuple[float, float]:
        """Fallback formant analysis using FFT"""
        fft = np.fft.rfft(audio_frame)
        magnitude = np.abs(fft)
        freqs = np.fft.rfftfreq(len(audio_frame), 1/self.sample_rate)
        
        # Find peaks in low frequency range (F1)
        low_freq_mask = (freqs >= 200) & (freqs <= 1000)
        f1_candidates = freqs[low_freq_mask]
        f1_magnitudes = magnitude[low_freq_mask]
        
        if len(f1_magnitudes) > 0:
            f1_idx = np.argmax(f1_magnitudes)
            f1 = f1_candidates[f1_idx]
        else:
            f1 = 500
        
        # Find peaks in high frequency range (F2)
        high_freq_mask = (freqs >= 800) & (freqs <= 3000)
        f2_candidates = freqs[high_freq_mask]
        f2_magnitudes = magnitude[high_freq_mask]
        
        if len(f2_magnitudes) > 0:
            f2_idx = np.argmax(f2_magnitudes)
            f2 = f2_candidates[f2_idx]
        else:
            f2 = 1500
        
        return float(f1), float(f2)  # numpy.float32 방지
    
    def classify_vowel(self, f1: float, f2: float, intensity: float) -> Tuple[VowelType, float]:
        """
        Classify vowel based on formant frequencies.
        
        Args:
            f1: First formant frequency
            f2: Second formant frequency  
            intensity: Audio frame intensity
            
        Returns:
            Tuple[VowelType, float]: Vowel type and confidence score
        """
        if intensity < self.silence_threshold:
            return VowelType.SILENCE, 1.0
        
        best_vowel = VowelType.A
        best_score = 0.0
        
        for vowel, formant_ranges in self.vowel_formants.items():
            # Calculate distance from expected formant ranges
            f1_range = formant_ranges["f1_range"]
            f2_range = formant_ranges["f2_range"]
            
            # Normalized distances
            f1_dist = 0.0
            if f1 < f1_range[0]:
                f1_dist = (f1_range[0] - f1) / f1_range[0]
            elif f1 > f1_range[1]:
                f1_dist = (f1 - f1_range[1]) / f1_range[1]
            
            f2_dist = 0.0
            if f2 < f2_range[0]:
                f2_dist = (f2_range[0] - f2) / f2_range[0]
            elif f2 > f2_range[1]:
                f2_dist = (f2 - f2_range[1]) / f2_range[1]
            
            # Combined distance (lower is better)
            total_dist = np.sqrt(f1_dist**2 + f2_dist**2)
            score = max(0.0, 1.0 - total_dist)
            
            if score > best_score:
                best_score = score
                best_vowel = vowel
        
        # If no good match, classify as consonant
        if best_score < 0.3:
            return VowelType.CONSONANT, best_score
        
        return best_vowel, best_score


class MouthParameterMapper:
    """
    Maps vowel types to Live2D mouth parameters.
    Based on standard Live2D mouth parameter naming conventions.
    """
    
    def __init__(self):
        # Live2D mouth parameter mappings for Korean vowels
        self.vowel_params = {
            VowelType.A: {
                "ParamMouthOpenY": 0.8,    # Wide open mouth
                "ParamMouthForm": 0.0,     # Neutral form  
                "ParamMouthOpenX": 0.6,    # Slight horizontal opening
            },
            VowelType.I: {
                "ParamMouthOpenY": 0.2,    # Barely open
                "ParamMouthForm": 1.0,     # Smile form
                "ParamMouthOpenX": -0.3,   # Narrow opening
            },
            VowelType.U: {
                "ParamMouthOpenY": 0.4,    # Small opening
                "ParamMouthForm": -0.5,    # Puckered form
                "ParamMouthOpenX": -0.7,   # Very narrow opening
            },
            VowelType.E: {
                "ParamMouthOpenY": 0.5,    # Medium opening
                "ParamMouthForm": 0.3,     # Slight smile
                "ParamMouthOpenX": 0.2,    # Medium width
            },
            VowelType.O: {
                "ParamMouthOpenY": 0.6,    # Rounded opening
                "ParamMouthForm": -0.3,    # Rounded form
                "ParamMouthOpenX": -0.4,   # Narrow but rounded
            },
            VowelType.SILENCE: {
                "ParamMouthOpenY": 0.0,    # Closed mouth
                "ParamMouthForm": 0.0,     # Neutral
                "ParamMouthOpenX": 0.0,    # Closed
            },
            VowelType.CONSONANT: {
                "ParamMouthOpenY": 0.1,    # Slightly open
                "ParamMouthForm": 0.0,     # Neutral
                "ParamMouthOpenX": 0.1,    # Minimal opening
            }
        }
    
    def vowel_to_params(self, vowel: VowelType, intensity: float = 1.0, 
                       smoothing: float = 0.8) -> Dict[str, float]:
        """
        Convert vowel type to Live2D mouth parameters.
        
        Args:
            vowel: Vowel type to convert
            intensity: Speech intensity (0.0-1.0)
            smoothing: Smoothing factor for parameter values
            
        Returns:
            Dict[str, float]: Live2D mouth parameters
        """
        base_params = self.vowel_params.get(vowel, self.vowel_params[VowelType.SILENCE])
        
        # Apply intensity scaling
        scaled_params = {}
        for param_name, base_value in base_params.items():
            if param_name == "ParamMouthOpenY":
                # Scale opening by intensity
                scaled_value = base_value * intensity
            else:
                # Apply partial intensity to form parameters
                scaled_value = base_value * (0.3 + 0.7 * intensity)
            
            # Apply smoothing
            scaled_params[param_name] = float(scaled_value * smoothing)  # numpy.float32 방지
        
        return scaled_params
    
    def interpolate_params(self, params_a: Dict[str, float], params_b: Dict[str, float], 
                          t: float) -> Dict[str, float]:
        """
        Interpolate between two parameter sets for smooth transitions.
        
        Args:
            params_a: Starting parameters
            params_b: Target parameters
            t: Interpolation factor (0.0-1.0)
            
        Returns:
            Dict[str, float]: Interpolated parameters
        """
        result = {}
        all_keys = set(params_a.keys()) | set(params_b.keys())
        
        for key in all_keys:
            val_a = params_a.get(key, 0.0)
            val_b = params_b.get(key, 0.0)
            result[key] = float(val_a + (val_b - val_a) * t)  # numpy.float32 방지
        
        return result


class LipSyncAnalyzer:
    """
    Main lip-sync analyzer for TTS Live2D integration.
    
    Analyzes audio files and generates Live2D mouth parameter sequences
    for real-time lip-sync animation following todo specifications.
    """
    
    def __init__(self, frame_rate: float = 30.0):
        """
        Initialize lip-sync analyzer.
        
        Args:
            frame_rate: Target animation frame rate (FPS)
        """
        self.frame_rate = frame_rate
        self.frame_duration = 1.0 / frame_rate
        
        self.vowel_classifier = VowelClassifier()
        self.parameter_mapper = MouthParameterMapper()
        
        # Analysis parameters
        self.sample_rate = 44100
        self.min_intensity_threshold = 0.005
        self.smoothing_window = 3  # frames for temporal smoothing
        
        logger.info(f"LipSyncAnalyzer initialized with {frame_rate} FPS")
    
    async def analyze_audio_file(self, audio_path: str) -> LipSyncData:
        """
        Analyze audio file and generate lip-sync data.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            LipSyncData: Complete lip-sync animation data
        """
        try:
            # Load audio file
            audio_data, sr = librosa.load(audio_path, sr=self.sample_rate)
            duration = len(audio_data) / sr
            
            logger.info(f"Analyzing audio: {audio_path}, duration: {duration:.2f}s")
            
            # Generate frame-based analysis
            frames = await self._analyze_audio_frames(audio_data, sr)
            
            # Apply temporal smoothing
            smoothed_frames = self._apply_temporal_smoothing(frames)
            
            return LipSyncData(
                frames=smoothed_frames,
                duration=duration,
                sample_rate=sr,
                frame_rate=self.frame_rate,
                analysis_method="formant_analysis_with_smoothing"
            )
            
        except Exception as e:
            logger.error(f"Audio analysis failed for {audio_path}: {e}")
            raise
    
    async def analyze_audio_data(self, audio_data: bytes, audio_format: str = "mp3") -> LipSyncData:
        """
        Analyze audio data from memory.
        
        Args:
            audio_data: Audio data bytes
            audio_format: Audio format (mp3, wav, etc.)
            
        Returns:
            LipSyncData: Complete lip-sync animation data
        """
        # Write to temporary file for librosa processing
        with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as tmp_file:
            tmp_file.write(audio_data)
            tmp_file_path = tmp_file.name
        
        try:
            result = await self.analyze_audio_file(tmp_file_path)
            return result
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
            except:
                pass
    
    async def _analyze_audio_frames(self, audio_data: np.ndarray, sr: int) -> List[LipSyncFrame]:
        """Generate lip-sync frames from audio data"""
        frames = []
        duration = len(audio_data) / sr
        num_frames = int(duration * self.frame_rate)
        
        # Calculate frame parameters
        samples_per_frame = int(sr / self.frame_rate)
        overlap = samples_per_frame // 4  # 25% overlap for smoother analysis
        
        for frame_idx in range(num_frames):
            timestamp = frame_idx * self.frame_duration
            
            # Extract audio frame with overlap
            start_sample = int(frame_idx * samples_per_frame - overlap)
            end_sample = start_sample + samples_per_frame + 2 * overlap
            
            # Ensure bounds
            start_sample = max(0, start_sample)
            end_sample = min(len(audio_data), end_sample)
            
            if start_sample >= end_sample:
                # No more audio data
                frames.append(self._create_silence_frame(timestamp))
                continue
            
            audio_frame = audio_data[start_sample:end_sample]
            
            # Calculate frame intensity
            intensity = np.sqrt(np.mean(audio_frame**2))
            
            if intensity < self.min_intensity_threshold:
                # Silent frame
                frames.append(self._create_silence_frame(timestamp))
                continue
            
            # Formant analysis
            f1, f2 = self.vowel_classifier.analyze_formants(audio_frame)
            
            # Vowel classification
            vowel_type, confidence = self.vowel_classifier.classify_vowel(f1, f2, intensity)
            
            # Generate mouth parameters
            mouth_params = self.parameter_mapper.vowel_to_params(
                vowel_type, intensity, smoothing=0.9
            )
            
            frame = LipSyncFrame(
                timestamp=timestamp,
                vowel_type=vowel_type,
                intensity=intensity,
                mouth_params=mouth_params,
                confidence=confidence
            )
            
            frames.append(frame)
        
        logger.info(f"Generated {len(frames)} lip-sync frames")
        return frames
    
    def _create_silence_frame(self, timestamp: float) -> LipSyncFrame:
        """Create a silence frame"""
        return LipSyncFrame(
            timestamp=timestamp,
            vowel_type=VowelType.SILENCE,
            intensity=0.0,
            mouth_params=self.parameter_mapper.vowel_to_params(VowelType.SILENCE),
            confidence=1.0
        )
    
    def _apply_temporal_smoothing(self, frames: List[LipSyncFrame]) -> List[LipSyncFrame]:
        """Apply temporal smoothing to reduce jitter"""
        if len(frames) <= self.smoothing_window:
            return frames
        
        smoothed_frames = []
        half_window = self.smoothing_window // 2
        
        for i, frame in enumerate(frames):
            if i < half_window or i >= len(frames) - half_window:
                # Keep edge frames as-is
                smoothed_frames.append(frame)
                continue
            
            # Collect window of parameters
            window_params = []
            for j in range(i - half_window, i + half_window + 1):
                window_params.append(frames[j].mouth_params)
            
            # Average parameters in window
            smoothed_params = {}
            for param_name in frame.mouth_params.keys():
                values = [params[param_name] for params in window_params]
                smoothed_params[param_name] = float(np.mean(values))  # numpy.float32 방지
            
            # Create smoothed frame
            smoothed_frame = LipSyncFrame(
                timestamp=frame.timestamp,
                vowel_type=frame.vowel_type,
                intensity=frame.intensity,
                mouth_params=smoothed_params,
                confidence=frame.confidence
            )
            
            smoothed_frames.append(smoothed_frame)
        
        return smoothed_frames
    
    def export_lipsync_for_live2d(self, lipsync_data: LipSyncData) -> Dict[str, Any]:
        """
        Export lip-sync data in Live2D compatible format.
        
        Args:
            lipsync_data: Generated lip-sync data
            
        Returns:
            Dict[str, Any]: Live2D compatible animation data
        """
        # Convert to Live2D animation timeline format
        parameter_curves = {}
        
        # Initialize parameter curves
        param_names = ["ParamMouthOpenY", "ParamMouthForm", "ParamMouthOpenX"]
        for param_name in param_names:
            parameter_curves[param_name] = {
                "keyframes": [],
                "interpolation": "linear"
            }
        
        # Add keyframes from lip-sync data
        for frame in lipsync_data.frames:
            for param_name in param_names:
                value = frame.mouth_params.get(param_name, 0.0)
                parameter_curves[param_name]["keyframes"].append({
                    "time": frame.timestamp,
                    "value": value,
                    "confidence": frame.confidence
                })
        
        return {
            "version": "1.0",
            "duration": lipsync_data.duration,
            "frame_rate": lipsync_data.frame_rate,
            "analysis_method": lipsync_data.analysis_method,
            "parameter_curves": parameter_curves,
            "metadata": {
                "total_frames": len(lipsync_data.frames),
                "sample_rate": lipsync_data.sample_rate,
                "vowel_distribution": self._calculate_vowel_distribution(lipsync_data.frames)
            }
        }
    
    def _calculate_vowel_distribution(self, frames: List[LipSyncFrame]) -> Dict[str, float]:
        """Calculate vowel type distribution for metadata"""
        vowel_counts = {}
        for frame in frames:
            vowel = frame.vowel_type.value
            vowel_counts[vowel] = vowel_counts.get(vowel, 0) + 1
        
        total_frames = len(frames)
        return {vowel: count/total_frames for vowel, count in vowel_counts.items()}