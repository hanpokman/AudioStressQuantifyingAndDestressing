# Audio Stress Quantifier

A Django-based web platform that objectively quantifies stress in audio using psychoacoustic signal processing. No human labeling required — just upload an audio file and get a stress score backed by 60+ years of psychoacoustic research.

**📄 Full paper:** https://drive.google.com/file/d/16IVtfj0gBnjWnH8v6wKwTSPTXEjz6C9q/view?usp=sharing

---

## 🧠 What it does

This system analyzes any audio file using nine research-backed features derived from established psychoacoustic literature. It then outputs a normalized stress score (0–1) indicating how stressful the audio is likely to be for a listener — no subjective ratings, no physiological sensors, no black-box AI.

**Key features:**
- Fully automated, human-independent stress scoring
- Based on tempo, dissonance, RMS variation, spectral centroid, zero-crossing rate, and more
- Transparent, explainable output
- Built with Django — web-ready from the start

---

## 🚀 Quick start

```bash
# Clone the repo
git clone https://github.com/yourusername/audio-stress-quantifier.git
cd audio-stress-quantifier

# Install dependencies
pip install -r requirements.txt

# Run the server
python3 manage.py runserver
```

Then open `http://127.0.0.1:8000` in your browser.

---

## 🧪 Example

Upload a classical piece → lower stress score (~0.2–0.4)  
Upload a rock or grunge track → higher stress score (~0.6–0.8)

The system correlates tempo with stress — consistent with Bernardi et al. (2006) and McCraty et al. (1998).

---

## 📦 Dependencies

- Python 3.9+
- Django 4+
- NumPy, SciPy
- Librosa (for audio feature extraction)

---

## 📚 Research foundation

This implementation is based on the paper **"Audio Stress Quantification System based on Psychoacoustic Signal Processing"** , which synthesizes findings from:

- Bernardi et al. (2006) — tempo & physiological stress
- Koelsch (2014) — dissonance & amygdala activation
- Plomp & Levelt (1965) — critical bandwidth & roughness
- Bedoya et al. (2021) — vocal distress & spectral features
- Arjmand et al. (2017) — musical change & emotional response

> 👉 **Full paper:** https://drive.google.com/file/d/16IVtfj0gBnjWnH8v6wKwTSPTXEjz6C9q/view?usp=sharing

---

## ✨ Why not deep learning?

Unlike black-box models, this system is:
- **Explainable** — you see which features drove the score
- **Data-efficient** — no training required
- **Lightweight** — runs on modest hardware
- **Fidelity-preserving** — doesn't mangle original audio characteristics

---

## 📬 Contact

For questions or collaboration, reach out at nathan.han@ucsb.edu

---

## 🕵️ Findings

Stress Score Calculated against Tempo for specific genres

<img width="1078" height="369" alt="Screenshot 2026-05-14 at 1 22 59 AM" src="https://github.com/user-attachments/assets/13a23ff2-1dc0-4d55-979b-f238f806f2a4" />

Stress Score for ALL genres

<img width="761" height="504" alt="Screenshot 2026-05-14 at 1 23 39 AM" src="https://github.com/user-attachments/assets/eef09e95-0a12-453e-ab00-b95e5227c21e" />

This suggests that an increase in tempo relates to increase in stress, aligning with research found by Kuppilli (2024) and McCraty et al (1998).

*Built as part of a research project on psychoacoustic stress quantification.*
