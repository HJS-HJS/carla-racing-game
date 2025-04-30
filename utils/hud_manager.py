import json
import time
import pygame

from utils.color import *
from utils.panels.player_panel import PlayerPanel
from utils.panels.map_panel import MapPanel
from utils.panels.ego_panel import EgoPanel

class HUDManager:
    def __init__(self, screen, config_path):
        self.screen = screen
        self.player_panel = PlayerPanel(screen)
        self.map_panel = MapPanel(screen)
        self.ego_panel = EgoPanel(screen)
        self.dim = screen.get_size()
        self.finish_line = None
        self.count = 0

        self._banner_active = False
        self._banner_text = ""
        self._banner_color = RED
        self._banner_duration = 0
        self._banner_start_time = 0

        self._load_finish_line(config_path)

    def _load_finish_line(self, config_path):
        with open(config_path, "r") as f:
            data = json.load(f)
            p1 = (data["point1"]["x"], data["point1"]["y"])
            p2 = (data["point2"]["x"], data["point2"]["y"])
            self.finish_line = (p1, p2)
            self.map_panel.set_finish_line(p1, p2)

    def set_topology_lines(self, lines):
        self.map_panel.set_topology_lines(lines)

    def set_player_location(self, location):
        self.map_panel.set_player_location(location)

    def set_ego_location(self, location):
        self.map_panel.set_ego_location(location)

    def set_obs_location(self, vehicle_transforms):
        self.map_panel.set_obs_location(vehicle_transforms)

    def update(self, throttle, brake, steering, speed, gear):
        self.player_panel.update(throttle, brake, steering, speed, gear)

    def set_player_camera_image(self, surface):
        self.player_panel.set_camera_image(surface)

    def set_ego_camera_image(self, surface):
        self.ego_camera_image = surface
        self.ego_panel.set_camera_image(surface)

    def draw(self):
        self.player_panel.draw()
        if self.count % 3 == 0: self.map_panel.draw()
        self.ego_panel.draw()
        if self._banner_active:
            self._draw_banner()

        self.count += 1

    def _draw_banner(self):
        now = time.time()
        elapsed = now - self._banner_start_time
        if elapsed > self._banner_duration:
            self._banner_active = False
            return

        # 깜빡이기 (0.5초 주기)
        blink = int(elapsed * 2) % 2 == 0
        if not blink:
            return

        _dim = self.screen.get_size()

        font = pygame.font.SysFont(None, int(_dim[0] * 0.05))
        text_surface = font.render(self._banner_text, True, self._banner_color)
        text_rect = text_surface.get_rect(center=(_dim[0] // 2, _dim[1] // 2))
        bg_rect = text_rect.inflate(_dim[0] // 3, _dim[1] // 10)
        pygame.draw.rect(self.screen, (0, 0, 0), bg_rect)
        self.screen.blit(text_surface, text_rect)

    def start_clock(self):
        self.player_panel.start_clock()

    def stop_clock(self):
        self.player_panel.stop_clock()

    def set_help_text(self, lines):
        self.right_bottom_msg = "\n".join(lines)

    def get_time_spent(self):
        return self.player_panel.get_time_spent()
    
    def initialize_time(self):
        self.player_panel.initialize_time()
        
    def is_crossing_finish_line(self, prev_pos, curr_pos):
        """
        prev_pos, curr_pos: carla.Transform 또는 carla.Location
        self.finish_line: ((x1, y1), (x2, y2)) 형태
        """
        def to_point(p):
            return (p.location.x, p.location.y) if hasattr(p, "location") else (p.x, p.y)

        def ccw(a, b, c):
            """세 점이 반시계 방향 순서인지"""
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

        def segments_intersect(p1, p2, q1, q2):
            """선분 p1-p2 와 q1-q2가 교차하는지"""
            return (ccw(p1, q1, q2) != ccw(p2, q1, q2)) and (ccw(p1, p2, q1) != ccw(p1, p2, q2))

        p1 = to_point(prev_pos)
        p2 = to_point(curr_pos)
        q1, q2 = self.finish_line  # finish_line은 (x, y), (x, y)

        return segments_intersect(p1, p2, q1, q2)
    
    def show_banner(self, text: str, color: tuple, duration: float = 5.0):
        if self._banner_active: return

        self._banner_text = text
        self._banner_color = color
        self._banner_duration = duration
        self._banner_start_time = time.time()
        self._banner_active = True