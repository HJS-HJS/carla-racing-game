import pygame
import math
import time
from utils.color import *

class Dashboard:
    def __init__(self):
        self.throttle = 0.0
        self.brake = 0.0
        self.steering = 0.0
        self.speed = 0.0
        self.gear = 0
        
        self.start_time = time.time()
        self.spent_time = time.time()
        self.time_checker = True

        self.small_gauge_cache = {}
        self.speedo_base = None

    def update(self, throttle, brake, steering, speed, gear=0):
        self.throttle = throttle
        self.brake = brake
        self.steering = steering
        self.speed = speed
        self.gear = gear
    
    def start_clock(self):
        self.start_time = time.time()
        self.spent_time = 0.0
        self.time_checker = True

    def stop_clock(self):
        self.time_checker = False

    def draw(self, surface, left_rect):
        width, height = left_rect.width, left_rect.height
        base_x = left_rect.left
        base_y = left_rect.top

        radius = int(height * 0.10)
        big_radius = int(height * 0.20)
        font = pygame.font.SysFont(None, max(14, height // 20))

        center_x = base_x + int(width * 0.90)
        center_y = base_y + int(height * 0.70)

        gauges = [
            ("Throttle", self.throttle),
            ("Brake", self.brake),
            ("Steering", self.steering),
        ]
        start_angle = math.radians(160)
        angle_step = math.radians(55)

        for i, (label, value) in enumerate(gauges):
            angle = start_angle + i * angle_step
            cx = int(center_x + math.cos(angle) * (big_radius + radius * 2.0))
            cy = int(center_y + math.sin(angle) * (big_radius + radius * 2.0))
            self._draw_small_gauge(surface, (cx, cy), radius, value, label, font, left_rect)

        self._draw_speedometer(surface, (center_x, center_y), big_radius, self.speed, font, left_rect)
        self._draw_info_panel(surface, left_rect)

    def _draw_small_gauge(self, surf, center, radius, value, label, font, left_rect):
        key = (label, radius)
        if key not in self.small_gauge_cache:
            base = pygame.Surface((radius * 2 + 10, radius * 2 + 30), pygame.SRCALPHA)
            local_center = (radius + 5, radius + 5)

            pygame.draw.circle(base, GRAY, local_center, radius)
            pygame.draw.circle(base, DARK, local_center, radius - 4)

            for i in range(0, 11):
                angle = 180 * (i / 10)
                rad = math.radians(angle)
                x1 = local_center[0] + (radius * 0.9) * math.cos(rad)
                y1 = local_center[1] - (radius * 0.9) * math.sin(rad)
                x2 = local_center[0] + (radius * 0.7) * math.cos(rad)
                y2 = local_center[1] - (radius * 0.7) * math.sin(rad)
                color = RED if i < 1 or i > 9 else WHITE
                pygame.draw.line(base, color, (x1, y1), (x2, y2), radius // 30)

            # text_surf = font.render(label, True, WHITE)
            text_surf = font.render(label, True, BLACK)
            text_rect = text_surf.get_rect(center=(local_center[0], local_center[1] + radius + 12))
            base.blit(text_surf, text_rect)

            self.small_gauge_cache[key] = base

        cached = self.small_gauge_cache[key]
        gauge_x = center[0] - cached.get_width() // 2
        gauge_y = center[1] - cached.get_height() // 2
        surf.blit(cached, (gauge_x, gauge_y))

        indicator_center = (gauge_x + radius + 5, gauge_y + radius + 5)

        if label in ("Throttle", "Brake"):
            angle = 180 - 180 * value
        elif label == "Steering":
            angle = 90 - 90 * value

        rad = math.radians(angle)
        end_x = indicator_center[0] + (radius - 6) * math.cos(rad)
        end_y = indicator_center[1] - (radius - 6) * math.sin(rad)
        pygame.draw.line(surf, RED, indicator_center, (end_x, end_y), radius // 15)

    def _draw_speedometer(self, surf, center, radius, speed, font, left_rect, max_speed=30):
        key = radius
        if self.speedo_base is None or self.speedo_base.get_width() != radius * 2 + 40:
            self.speedo_base = pygame.Surface((radius * 2 + 40, radius * 2 + 70), pygame.SRCALPHA)
            local_center = (self.speedo_base.get_width() // 2, self.speedo_base.get_height() // 2 - 10)

            pygame.draw.circle(self.speedo_base, GRAY, local_center, radius)
            pygame.draw.circle(self.speedo_base, DARK, local_center, radius - 10)

            for s in range(0, max_speed + 1):
                angle = 225 - (s / max_speed) * 270
                rad = math.radians(angle)
                x1 = local_center[0] + (radius * 0.9) * math.cos(rad)
                y1 = local_center[1] - (radius * 0.9) * math.sin(rad)
                x2 = local_center[0] + (radius * 0.7) * math.cos(rad)
                y2 = local_center[1] - (radius * 0.7) * math.sin(rad)
                color = RED if s >= max_speed * 0.8 else WHITE
                pygame.draw.line(self.speedo_base, color, (x1, y1), (x2, y2), radius // 30)

            # label_surf = font.render("Speed", True, WHITE)
            label_surf = font.render("Speed", True, BLACK)
            label_rect = label_surf.get_rect(center=(local_center[0], local_center[1] + radius + 25))
            self.speedo_base.blit(label_surf, label_rect)

        surf.blit(self.speedo_base, (center[0] - self.speedo_base.get_width() // 2, center[1] - self.speedo_base.get_height() // 2 + 10))

        angle = 225 - (speed / max_speed) * 270
        rad = math.radians(angle)
        start_x = center[0] + (radius / 4) * math.cos(rad)
        start_y = center[1] - (radius / 4) * math.sin(rad)
        end_x = center[0] + (radius - 25) * math.cos(rad)
        end_y = center[1] - (radius - 25) * math.sin(rad)
        pygame.draw.line(surf, RED, (start_x, start_y), (end_x, end_y), radius // 15)

        # 기어 표시
        gear_label = "N"
        gear_color = WHITE
        if self.gear == 1:
            gear_label = "R"
            gear_color = RED
        elif self.gear == -1:
            gear_label = "D"
            gear_color = WHITE

        gear_font = pygame.font.SysFont(None, radius - 10)
        gear_surf = gear_font.render(gear_label, True, gear_color)
        gear_rect = gear_surf.get_rect(center=center)
        surf.blit(gear_surf, gear_rect)

    def _draw_info_panel(self, surface, left_rect):
        # 텍스트 설정
        font_speed = pygame.font.SysFont(None, max(65, left_rect.height // 8))
        font_time = pygame.font.SysFont(None, max(24, left_rect.height // 15))

        speed_text = f"{self.speed:.1f} km/h"
        if self.time_checker: self.spent_time = time.time() - self.start_time
        minutes = int(self.spent_time) // 60
        seconds = int(self.spent_time) % 60
        milliseconds = int((self.spent_time - int(self.spent_time)) * 1000)
        time_text = f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

        surf_speed = font_speed.render(speed_text, True, BLACK)
        surf_time = font_time.render(time_text, True, BLACK)

        # 패딩 및 크기 계산
        padding_x = 20
        padding_top = 15
        padding_middle = 10
        padding_bottom = 15

        panel_width = max(surf_speed.get_width(), surf_time.get_width()) + padding_x * 2
        panel_height = surf_time.get_height() + padding_middle + surf_speed.get_height() + padding_top + padding_bottom

        # 패널 surface
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)

        # 배경 색
        bg_color = (100, 100, 100, 40)
        panel_surface.fill(bg_color)

        # 광택 효과
        gloss_height = panel_height // 3
        gloss = pygame.Surface((panel_width, gloss_height), pygame.SRCALPHA)
        for y in range(gloss_height):
            alpha = int(70 * (1 - y / gloss_height))
            pygame.draw.line(gloss, (255, 255, 255, alpha), (0, y), (panel_width, y))
        panel_surface.blit(gloss, (0, 0))

        # 테두리 (직각, 투명도 약간 있는 회색)
        border_color = (100, 100, 100, 100)
        pygame.draw.rect(panel_surface, border_color, panel_surface.get_rect(), width=1)

        # 텍스트 배치 (왼쪽 정렬)
        panel_surface.blit(surf_time, (padding_x, padding_top))
        panel_surface.blit(surf_speed, (padding_x, padding_top + surf_time.get_height() + padding_middle))

        # 화면에 표시
        surface.blit(panel_surface, (left_rect.left + 20, left_rect.top + 40))

    def get_time_spent(self):
        return self.spent_time
    
    def initialize_time(self):
        self.time_checker = False
        self.spent_time = 1e-9
