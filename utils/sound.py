import pygame
import math
import time
import threading


class EngineSoundPlayer:
    def __init__(self, sound_path: str):
        pygame.mixer.init(frequency=44100, channels=2)
        self.sound = pygame.mixer.Sound(sound_path)
        self.channel = pygame.mixer.Channel(0)

        self.throttle = 0.0
        self.position = (0.0, 0.0)
        self.facing_angle = 0.0  # 내 시야각 (라디안)
        self.listener_position = (0.0, 0.0)

        # 기본 볼륨
        self.base_volume = 0.6

        # 루프 재생
        self.channel.play(self.sound, loops=-1)
        self.running = True

        # 별도 스레드로 음향 갱신
        self.thread = threading.Thread(target=self._update_loop)
        self.thread.daemon = True
        self.thread.start()

    def set_throttle(self, value: float):
        self.throttle = max(0.0, min(1.0, value))

    def set_relative_position(self, sound_pos: tuple, listener_pos: tuple, facing_angle_rad: float):
        self.position = sound_pos
        self.listener_position = listener_pos
        self.facing_angle = facing_angle_rad

    def _update_loop(self):
        while self.running:
            self._update_volume_and_stereo()
            time.sleep(0.05)  # 20Hz 정도

    def _update_volume_and_stereo(self):
        dx = self.position[0] - self.listener_position[0]
        dy = self.position[1] - self.listener_position[1]
        distance = math.hypot(dx, dy)

        # 거리 기반 감쇠
        volume = self.base_volume * (1.0 / (1.0 + 0.3 * distance))

        # 방향 벡터 계산
        angle_to_sound = math.atan2(dy, dx)
        relative_angle = angle_to_sound - self.facing_angle
        relative_angle = (relative_angle + math.pi) % (2 * math.pi) - math.pi  # -π ~ π

        # 스테레오 처리
        left = volume * (1.0 - 0.5 * max(0.0, math.sin(relative_angle)))
        right = volume * (1.0 + 0.5 * max(0.0, math.sin(relative_angle)))

        # 볼륨 설정 (좌우 분리)
        self.channel.set_volume(left, right)

    def stop(self):
        self.running = False
        self.channel.stop()
        pygame.mixer.quit()
