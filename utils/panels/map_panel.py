import pygame
import carla
import math
from utils.color import *

class MapPanel:
    def __init__(self, screen):
        self.screen = screen
        self.text = "Map"

        # 위치 관련
        self.player_location = None
        self.ego_location = None
        self.obs_location = []

        # 지형/지도 관련
        self.topology_lines = []
        self._bbox = None  # (min_x, min_y, max_x, max_y)

        # 종료선
        self.finish_line_world = None

        # 캐시
        self.cached_surface = None

    def set_topology_lines(self, lines):
        self.topology_lines = lines
        self._bbox = self._calculate_bbox(lines)
        self.cached_surface = None  # 다시 그리도록

    def set_finish_line(self, point1, point2):
        self.finish_line_world = (point1, point2)
        self.cached_surface = None  # 다시 그리도록

    def set_player_location(self, location):
        self.player_location = location

    def set_ego_location(self, location):
        self.ego_location = location

    def set_obs_location(self, locations):
        self.obs_location = locations

    def draw(self):
        width, height = self.screen.get_size()
        rect = pygame.Rect(0, height // 2, width // 2, height // 2)

        # 배경
        pygame.draw.rect(self.screen, (180, 180, 180), rect)

        # 지도 Surface (화면 크기 바뀌면 다시 그림)
        if self.cached_surface is None or self.cached_surface.get_size() != rect.size:
            if self.topology_lines:
                self.cached_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
                self._draw_topology(self.cached_surface, rect.size)

        if self.cached_surface:
            self.screen.blit(self.cached_surface, rect.topleft)

        # 차량 위치들 찍기
        def draw_vehicle_icon(loc, color):
            if hasattr(loc, "location"):
                pos = loc.location
                yaw_rad = math.radians(loc.rotation.yaw)
            else:
                pos = loc
                yaw_rad = 0

            x, y = self._world_to_panel(pos, rect.size)
            x += rect.x
            y += rect.y

            size = width / 450
            tip = (x + math.cos(yaw_rad) * size, y + math.sin(yaw_rad) * size)
            left = (x + math.cos(yaw_rad + 2.5) * size * 2.5,
                    y + math.sin(yaw_rad + 2.5) * size * 2.5)
            right = (x + math.cos(yaw_rad - 2.5) * size * 2.5,
                     y + math.sin(yaw_rad - 2.5) * size * 2.5)

            pygame.draw.polygon(self.screen, color, [tip, left, right])

        if self.player_location and self._bbox:
            draw_vehicle_icon(self.player_location, (255, 0, 0))
        if self.ego_location and self._bbox:
            draw_vehicle_icon(self.ego_location, (0, 0, 255))
        for veh in self.obs_location:
            draw_vehicle_icon(veh, (0, 255, 0))

        # 텍스트
        if self.text:
            text_font = pygame.font.SysFont(None, height // 20)
            label = text_font.render(self.text, True, (0, 0, 0))
            self.screen.blit(label, (rect.x + 20, rect.y + 20))

    def _draw_topology(self, surface, panel_size):
        if not self._bbox:
            return

        for line in self.topology_lines:
            if len(line) < 2:
                continue

            left_side = []
            right_side = []

            for i, wp in enumerate(line):
                if i < len(line) - 1:
                    next_wp = line[i + 1]
                    dx = next_wp.transform.location.x - wp.transform.location.x
                    dy = next_wp.transform.location.y - wp.transform.location.y
                else:
                    prev_wp = line[i - 1]
                    dx = wp.transform.location.x - prev_wp.transform.location.x
                    dy = wp.transform.location.y - prev_wp.transform.location.y

                length = math.hypot(dx, dy)
                if length == 0:
                    continue
                nx = -dy / length
                ny = dx / length

                half_w = wp.lane_width / 2.0
                a = wp.transform.location
                left = carla.Location(x=a.x + nx * half_w, y=a.y + ny * half_w)
                right = carla.Location(x=a.x - nx * half_w, y=a.y - ny * half_w)

                left_side.append(self._world_to_panel(left, panel_size))
                right_side.append(self._world_to_panel(right, panel_size))

            points = left_side + right_side[::-1]
            pygame.draw.polygon(surface, (50, 50, 50), points)

        # === Finish Line (흰색 선) ===
        if self.finish_line_world:
            p1, p2 = self.finish_line_world
            sp1 = self._world_to_panel(carla.Location(x=p1[0], y=p1[1]), panel_size)
            sp2 = self._world_to_panel(carla.Location(x=p2[0], y=p2[1]), panel_size)
            pygame.draw.line(surface, (255, 255, 255), sp1, sp2, 3)

    def _calculate_bbox(self, lines):
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        for line in lines:
            for wp in line:
                loc = wp.transform.location
                min_x = min(min_x, loc.x)
                min_y = min(min_y, loc.y)
                max_x = max(max_x, loc.x)
                max_y = max(max_y, loc.y)
        _x_length = max_x - min_x
        _y_length = max_y - min_y
        return (min_x - _x_length * 0.1, min_y - _y_length * 0.1, max_x + _x_length * 0.1, max_y + _y_length * 0.1)

    def _world_to_panel(self, loc, panel_size):
        if hasattr(loc, "location"):
            loc = loc.location

        min_x, min_y, max_x, max_y = self._bbox
        padding = 20
        draw_w, draw_h = panel_size[0] - 2 * padding, panel_size[1] - 2 * padding

        scale_x = draw_w / (max_x - min_x)
        scale_y = draw_h / (max_y - min_y)
        scale = min(scale_x, scale_y)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        x = (loc.x - center_x) * scale + panel_size[0] // 2
        y = (loc.y - center_y) * scale + panel_size[1] // 2

        return x, y
