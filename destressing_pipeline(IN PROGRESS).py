import librosa
import numpy as np
import soundfile as sf
from scipy.signal import lfilter
from scorer import AudioStressScorer

class ImprovedAudioDestresser:
    def __init__(self):
        self.params = {
            'tempo_reduction': 0.15,
            'hf_boost_db': 2.0,
            'mid_boost_db': 1.0,
            'compression_ratio': 3.0,
            'compression_threshold_db': -20,
            'attack_ms': 10,
            'release_ms': 100,
            'transient_blend_amount': 0.3,
            'stereo_width_base': 0.7,
            'stereo_width_dynamic_factor': 0.3,
        }
        self.sr = 44100
        self.scorer = AudioStressScorer()

    def process_audio(self, input_path, output_path):
        y, sr = librosa.load(input_path, sr=self.sr, mono=False)
        if y.ndim == 1:
            y = np.array([y, y])

        y_stretched = self._time_stretch(y, 1 - self.params['tempo_reduction'])
        y_eq = self._multi_band_eq(y_stretched)
        y_compressed = self._compressor(y_eq)
        y_transient_preserved = self._preserve_transients(y, y_compressed, self.params['transient_blend_amount'])
        y_stereo_adjusted = self._dynamic_stereo_width(y_transient_preserved)

        sf.write(output_path, y_stereo_adjusted.T, sr)
        return y_stereo_adjusted

    def _time_stretch(self, y, rate):
        if y.ndim == 2:
            stretched = []
            for ch in y:
                ch_stretched = librosa.effects.time_stretch(ch, rate=rate)
                min_len = min(len(ch), len(ch_stretched))
                stretched.append(ch_stretched[:min_len])
            return np.array(stretched)
        else:
            return librosa.effects.time_stretch(y, rate=rate)

    def _multi_band_eq(self, y):
        def peaking_eq(x, center_freq, Q, gain_db, sr):
            A = 10**(gain_db/40)
            w0 = 2 * np.pi * center_freq / sr
            alpha = np.sin(w0)/(2*Q)
            cos_w0 = np.cos(w0)

            b0 = 1 + alpha*A
            b1 = -2*cos_w0
            b2 = 1 - alpha*A
            a0 = 1 + alpha/A
            a1 = -2*cos_w0
            a2 = 1 - alpha/A

            b = np.array([b0, b1, b2]) / a0
            a = np.array([1, a1/a0, a2/a0])

            return lfilter(b, a, x)

        Q = 1.0
        y_eq = []
        for ch in y:
            ch_eq = peaking_eq(ch, 500, Q, self.params['mid_boost_db'], self.sr)
            ch_eq = peaking_eq(ch_eq, 5000, Q, self.params['hf_boost_db'], self.sr)
            y_eq.append(ch_eq)
        return np.array(y_eq)

    def _compressor(self, y):
        def db_to_amp(db):
            return 10.0 ** (db / 20.0)
        def amp_to_db(amp):
            return 20.0 * np.log10(np.maximum(amp, 1e-9))

        threshold = db_to_amp(self.params['compression_threshold_db'])
        ratio = self.params['compression_ratio']
        attack_samples = int(self.sr * self.params['attack_ms'] / 1000)
        release_samples = int(self.sr * self.params['release_ms'] / 1000)

        y_comp = []
        for ch in y:
            env = np.zeros_like(ch)
            gain = np.ones_like(ch)
            comp_out = np.zeros_like(ch)
            for i in range(1, len(ch)):
                x_abs = abs(ch[i])
                if x_abs > env[i-1]:
                    env[i] = (1 - 1/attack_samples) * env[i-1] + (1/attack_samples) * x_abs
                else:
                    env[i] = (1 - 1/release_samples) * env[i-1] + (1/release_samples) * x_abs
            for i in range(len(ch)):
                if env[i] > threshold:
                    over_db = amp_to_db(env[i]) - self.params['compression_threshold_db']
                    gain_db = -over_db * (1 - 1/ratio)
                    gain[i] = db_to_amp(gain_db)
                else:
                    gain[i] = 1.0
            comp_out = ch * gain
            y_comp.append(comp_out)
        return np.array(y_comp)

    def _preserve_transients(self, original, processed, blend_amount):
        def spectral_flux(x, frame_length=2048, hop_length=512):
            stft = np.abs(librosa.stft(x, n_fft=frame_length, hop_length=hop_length))
            flux = np.sqrt(np.sum(np.diff(stft, axis=1)**2, axis=0))
            flux = np.concatenate(([0], flux))
            return librosa.util.fix_length(flux, size=len(x))

        result = []
        for orig_chan, proc_chan in zip(original, processed):
            flux = spectral_flux(orig_chan)
            flux_mean = np.mean(flux)
            transient_mask = np.clip((flux - flux_mean) / flux_mean, 0, 1)
            transient_mask = np.convolve(transient_mask, np.ones(512)/512, mode='same')
            transient_mask = np.clip(transient_mask, 0, 1)
            blend_mask = 1 - blend_amount * transient_mask
            blended = blend_mask * proc_chan + (1 - blend_mask) * orig_chan
            result.append(blended)
        return np.array(result)

    def _dynamic_stereo_width(self, y):
        if y.shape[0] != 2:
            return y
        left, right = y
        mid = (left + right) / 2
        side = (left - right) / 2

        side_env = np.convolve(np.abs(side), np.ones(1024)/1024, mode='same')
        transient_activity = (side_env - np.mean(side_env)) / np.mean(side_env)
        transient_activity = np.clip(transient_activity, 0, 1)

        width = self.params['stereo_width_base'] + self.params['stereo_width_dynamic_factor'] * transient_activity

        side *= width
        left_adj = mid + side
        right_adj = mid - side

        return np.array([left_adj, right_adj])

    def estimate_stress_reduction(self, original_path, processed_path):
        try:
            orig_score = self.scorer.predict_stress(original_path)
            proc_score = self.scorer.predict_stress(processed_path)

            reduction = (orig_score - proc_score) / orig_score if orig_score > 0 else 0

            print(f"Original stress score: {orig_score:.3f}")
            print(f"Processed stress score: {proc_score:.3f}")
            print(f"Stress reduction: {reduction:.1%}")

            print("\nTop contributing factors to stress reduction:")
            contributions = self.scorer.explain_stress_score(processed_path)
            for feature, contribution in contributions[:3]:
                print(f"  {feature}: {contribution:.1%}")

            return reduction
        except Exception as e:
            print(f"Error estimating stress reduction: {e}")
            return 0.0

if __name__ == "__main__":
    destresser = ImprovedAudioDestresser()

    input_file = "HoliznaCC0 - Mutant Club.mp3"
    output_file = "edited_version.mp3"

    processed_audio = destresser.process_audio(input_file, output_file)
    orig_score = destresser.scorer.predict_stress(input_file)
    proc_score = destresser.scorer.predict_stress(output_file)

    print("Original stress score: {:.3f}".format(orig_score))
    print("Processed stress score: {:.3f}".format(proc_score))


    # reduction = destresser.estimate_stress_reduction(input_file, output_file)
    # print(f"Overall stress reduction achieved: {reduction:.1%}")
