"""Zero-dependency procedural sound synthesizer for Blink Sniper.

Generates high-impact tactical audio in-memory using pure math and Pygame's mixer.
No external sound files or internet connection required.
"""
import array
import math
import random
import pygame


class SoundEngine:
    _instance = None

    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
            self.enabled = True
            self._init_sounds()
        except Exception:
            self.enabled = False

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = SoundEngine()
        return cls._instance

    def _make_sound(self, generator, duration=0.25, sample_rate=44100):
        n = int(sample_rate * duration)
        buf = array.array('h')
        for i in range(n):
            t = i / sample_rate
            val = int(32767 * max(-1.0, min(1.0, generator(t, duration))))
            buf.append(val)
            buf.append(val)
        return pygame.mixer.Sound(buffer=buf)

    def _init_sounds(self):
        # 1. Sniper Rifle Shot
        def gen_shot(t, d):
            crack = math.sin(2 * math.pi * 1400 * t) * math.exp(-t * 70)
            boom = math.sin(2 * math.pi * 85 * (1 - t * 1.8) * t) * math.exp(-t * 14)
            noise = (random.random() * 2 - 1) * math.exp(-t * 22)
            return crack * 0.45 + boom * 0.75 + noise * 0.35

        # 2. Charged / Railgun Shot
        def gen_railgun(t, d):
            hum = math.sin(2 * math.pi * (200 + 1200 * t) * t) * math.exp(-t * 8)
            blast = math.sin(2 * math.pi * 55 * t) * math.exp(-t * 10)
            noise = (random.random() * 2 - 1) * math.exp(-t * 18)
            return hum * 0.3 + blast * 0.8 + noise * 0.4

        # 3. Hit Marker (crisp metallic click)
        def gen_hit(t, d):
            tone = math.sin(2 * math.pi * 1850 * t) * math.exp(-t * 45)
            click = math.sin(2 * math.pi * 3200 * t) * math.exp(-t * 90)
            return tone * 0.6 + click * 0.4

        # 4. Headshot / Critical Hit (harmonic chime)
        def gen_headshot(t, d):
            t1 = math.sin(2 * math.pi * 1760 * t) * math.exp(-t * 25)
            t2 = math.sin(2 * math.pi * 2640 * t) * math.exp(-t * 30)
            return t1 * 0.5 + t2 * 0.5

        # 5. Target Destroyed / Explosion (rumble crunch)
        def gen_kill(t, d):
            low = math.sin(2 * math.pi * 70 * (1 - t) * t) * math.exp(-t * 12)
            noise = (random.random() * 2 - 1) * math.exp(-t * 16)
            return low * 0.7 + noise * 0.5

        # 6. Blink Trigger / Charge Click
        def gen_blink(t, d):
            return math.sin(2 * math.pi * 950 * t) * math.exp(-t * 50) * 0.35

        # 7. Enemy Warning Alarm
        def gen_alarm(t, d):
            freq = 880 if (int(t * 20) % 2 == 0) else 1175
            return math.sin(2 * math.pi * freq * t) * math.exp(-t * 15) * 0.4

        # 8. UI Beep
        def gen_ui(t, d):
            return math.sin(2 * math.pi * 1320 * t) * math.exp(-t * 60) * 0.25

        try:
            self.sounds['shot'] = self._make_sound(gen_shot, 0.35)
            self.sounds['shot'].set_volume(0.85)
            self.sounds['railgun'] = self._make_sound(gen_railgun, 0.45)
            self.sounds['railgun'].set_volume(0.9)
            self.sounds['hit'] = self._make_sound(gen_hit, 0.09)
            self.sounds['hit'].set_volume(0.7)
            self.sounds['headshot'] = self._make_sound(gen_headshot, 0.16)
            self.sounds['headshot'].set_volume(0.8)
            self.sounds['kill'] = self._make_sound(gen_kill, 0.38)
            self.sounds['kill'].set_volume(0.85)
            self.sounds['blink'] = self._make_sound(gen_blink, 0.08)
            self.sounds['blink'].set_volume(0.5)
            self.sounds['alarm'] = self._make_sound(gen_alarm, 0.18)
            self.sounds['alarm'].set_volume(0.65)
            self.sounds['ui'] = self._make_sound(gen_ui, 0.07)
            self.sounds['ui'].set_volume(0.4)
        except Exception:
            self.enabled = False

    def play(self, name):
        if not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass


def play(name):
    SoundEngine.get().play(name)
