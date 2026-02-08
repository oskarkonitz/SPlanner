import wave
import struct
import math
import random
import tempfile
import subprocess
import sys
import os


class SoundGenerator:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.raw_data = bytearray()
        self.amplitude = 32767 * 0.5  # Baza: 50% głośności

    def add_note(self, freq, duration, wave_type="Square", master_volume=1.0):
        """Generuje falę dla pojedynczej nuty i dodaje do bufora."""
        num_samples = int(self.sample_rate * duration)

        fade_out_samples = int(num_samples * 0.1)

        # Efektywna amplituda
        effective_amplitude = self.amplitude * master_volume

        for i in range(num_samples):
            t = float(i) / self.sample_rate
            val = 0.0

            if wave_type == "Sine":
                val = math.sin(2 * math.pi * freq * t)
            elif wave_type == "Square":
                val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
            elif wave_type == "Sawtooth":
                val = 2.0 * (t * freq - math.floor(0.5 + t * freq))
            elif wave_type == "Noise":
                val = random.uniform(-1, 1)

            # Obliczanie głośności
            current_volume = effective_amplitude
            if i > num_samples - fade_out_samples:
                remaining = num_samples - i
                current_volume *= (remaining / fade_out_samples)

            sample = int(val * current_volume)
            sample = max(min(sample, 32767), -32767)

            self.raw_data += struct.pack('<h', sample)

    def clear(self):
        self.raw_data = bytearray()

    def play(self):
        if not self.raw_data: return

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                tmp_name = tf.name
                with wave.open(tmp_name, 'w') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(self.raw_data)

            if sys.platform == "darwin":
                subprocess.Popen(["afplay", tmp_name])
            elif sys.platform == "win32":
                import winsound
                winsound.PlaySound(tmp_name, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                subprocess.Popen(["aplay", tmp_name])

        except Exception as e:
            print(f"[SoundGenerator] Error: {e}")


def play_event_sound(storage, setting_key):
    """
    Odtwarza dźwięk, uwzględniając ustawienia głośności i wyciszenia.
    """
    if not storage: return

    settings = storage.get_settings()

    # 1. Sprawdź czy dźwięk jest włączony
    if not settings.get("sound_enabled", True):
        return

    # 2. Pobierz głośność
    volume = settings.get("sound_volume", 0.5)

    sound_id = settings.get(setting_key)
    if not sound_id or sound_id == "None": return

    sound_data = storage.get_custom_sound(sound_id)
    if not sound_data or not sound_data.get("steps"): return

    gen = SoundGenerator()
    for step in sound_data["steps"]:
        try:
            freq = float(step.get("freq", 440))
            dur = float(step.get("dur", 0.2))
            w_type = str(step.get("type", "Square"))

            # Przekazujemy głośność do każdej nuty
            gen.add_note(freq, dur, w_type, master_volume=volume)
        except:
            continue

    gen.play()