import librosa
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler
import soundfile as sf
from tqdm import tqdm
import os
import joblib
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

class AudioStressScorer:
    def __init__(self):
        self.feature_weights = np.array([
            0.15,  # rms_variation
            0.15,  # tempo  
            0.18,  # spectral_centroid
            -0.08, # spectral_flatness
            0.10,  # spectral_contrast
            0.16,  # onset_strength
            -0.12, # harmonic_ratio
            0.12,  # zero_crossing
            0.13   # dissonance
        ])
        self.feature_names = [
            'rms_variation', 'tempo', 'spectral_centroid', 
            'spectral_flatness', 'spectral_contrast', 'onset_strength',
            'harmonic_ratio', 'zero_crossing', 'dissonance'
        ]
        
        self.scaler = None
        self._is_fitted = False
        
        self._load_or_initialize_scaler()

    def _load_or_initialize_scaler(self):
        """Load existing scaler or create with defaults"""
        scaler_path = os.path.join(os.path.dirname(__file__), 'fitted_scaler.save')
        
        if os.path.exists(scaler_path):
            try:
                self.scaler = joblib.load(scaler_path)
                self._is_fitted = True
                print("✓ Loaded pre-fitted scaler from fitted_scaler.save")
                return
            except Exception as e:
                print(f"Error loading scaler: {e}. Initializing with defaults.")
        
        print("No fitted_scaler.save found or loading failed. Initializing with defaults.")
        self._initialize_with_defaults()

    def _initialize_with_defaults(self):
        """Initialize scaler with reasonable defaults"""
        self.scaler = RobustScaler()
        
        dummy_features = np.array([
            [0.1, 120, 1000, 0.5, 10, 0.5, 0.8, 0.1, 0.1],
            [0.3, 140, 2000, 0.3, 20, 1.0, 0.6, 0.2, 0.3],
            [0.5, 160, 3000, 0.1, 30, 1.5, 0.4, 0.3, 0.5]
        ])
        self.scaler.fit(dummy_features)
        self._is_fitted = True
        
        scaler_path = os.path.join(os.path.dirname(__file__), 'fitted_scaler.save')
        try:
            joblib.dump(self.scaler, scaler_path)
            print("✓ Default scaler initialized and saved")
        except Exception as e:
            print(f"Error saving default scaler: {e}")
        
    def extract_features(self, y, sr=44100):
        try:
            rms = librosa.feature.rms(y=y)[0]
            
            try:
                tempo = librosa.feature.rhythm.tempo(y=y, sr=sr)[0]
            except AttributeError:
                tempo = librosa.beat.tempo(y=y, sr=sr)[0]
            
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_flatness = librosa.feature.spectral_flatness(y=y)[0]
            spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
            
            spectral_contrast_mean = np.mean(spectral_contrast)
            
            onset_strength = librosa.onset.onset_strength(y=y, sr=sr)
            onset_strength_mean = np.mean(onset_strength)
            
            y_harm, y_perc = librosa.effects.hpss(y)
            harmonic_ratio = np.sum(y_harm**2) / (np.sum(y_harm**2) + np.sum(y_perc**2) + 1e-10)
            
            zero_crossing = librosa.feature.zero_crossing_rate(y)[0]
            zero_crossing_mean = np.mean(zero_crossing)
            
            dissonance = self._calculate_dissonance(y, sr)
            
            return np.array([
                float(np.std(rms)),         
                float(tempo),               
                float(np.mean(spectral_centroid)),  
                float(np.mean(spectral_flatness)), 
                float(spectral_contrast_mean),    
                float(onset_strength_mean),        
                float(harmonic_ratio),
                float(zero_crossing_mean),
                float(dissonance)
            ])
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            return np.zeros(len(self.feature_weights))
    
    def _calculate_dissonance(self, y, sr, n_fft=2048):
        try:
            S = np.abs(librosa.stft(y, n_fft=n_fft))
            freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
            dissonance = 0.0
            
            for i in range(1, min(100, len(freqs))):
                for j in range(i+1, min(100, len(freqs))):
                    if freqs[i] > 0 and freqs[j] > 0:
                        freq_ratio = freqs[j] / freqs[i]
                        if 0.1 < freq_ratio < 1.2:
                            x = 0.24 / (0.0207 * freq_ratio + 18.96)
                            dissonance += S[i, 0] * S[j, 0] * x
            
            return dissonance
            
        except Exception as e:
            print(f"Error calculating dissonance: {e}")
            return 0.0
    
    def fit(self, audio_files):
        features = []
        valid_files = []
        
        for file in tqdm(audio_files, desc="Fitting Scaler"):
            try:
                y, sr = librosa.load(file, sr=44100, duration=30)
                feature_vector = self.extract_features(y, sr)
                
                if not np.any(np.isnan(feature_vector)) and not np.any(np.isinf(feature_vector)):
                    features.append(feature_vector)
                    valid_files.append(file)
                    
            except Exception as e:
                print(f"Error processing {file}: {e}")
                continue
        
        if len(features) > 0:
            features_array = np.array(features)
            self.scaler.fit(features_array)
            print(f"Fitted on {len(valid_files)} files")
            
            self.feature_means = np.mean(features_array, axis=0)
            self.feature_stds = np.std(features_array, axis=0)
            print("Feature means:", [f"{x:.2f}" for x in self.feature_means])
            print("Feature stds: ", [f"{x:.2f}" for x in self.feature_stds])
            
        else:
            print("No valid files for fitting!")
    
    def predict_stress(self, audio_path):
        try:
            y, sr = librosa.load(audio_path, sr=44100, duration=30)
            features = self.extract_features(y, sr)
            
            if np.any(np.isnan(features)) or np.any(np.isinf(features)):
                return 0.5
            
            scaled = self.scaler.transform(features.reshape(1, -1))[0]
            
            linear_score = np.dot(scaled, self.feature_weights)
            
            stress_score = 1 / (1 + np.exp(-linear_score))
            
            
            return float(stress_score)
            
        except Exception as e:
            print(f"Error predicting stress for {audio_path}: {e}")
            return 0.5

    def _cleanup_file(self, file_path):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up file: {file_path}")
        except Exception as e:
            print(f"Error cleaning up file {file_path}: {e}")
    
    def explain_stress_score(self, audio_path):
        try:
            y, sr = librosa.load(audio_path, sr=44100, duration=30)
            features = self.extract_features(y, sr)
            scaled = self.scaler.transform(features.reshape(1, -1))[0]
            
            contributions = {}
            for i, name in enumerate(self.feature_names):
                contributions[name] = scaled[i] * self.feature_weights[i]
            
            total_contribution = sum(abs(c) for c in contributions.values())
            if total_contribution > 0:
                normalized = {k: abs(v)/total_contribution for k, v in contributions.items()}
            else:
                normalized = {k: 0 for k in contributions.keys()}
            self._cleanup_file(audio_path)
            return sorted(normalized.items(), key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            print(f"Error explaining score: {e}")
            self._cleanup_file(audio_path)
            return []
    