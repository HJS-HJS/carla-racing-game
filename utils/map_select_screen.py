import pygame
import time
from utils.color import RED, WHITE
from utils.utils import show_loading_screen  # 외부 함수로 분리된 로딩 화면

class MapSelectScreen:
    def __init__(self, screen, get_scaled_font, resize_screen, clock, map_list, joystick):
        self.screen = screen
        self.get_scaled_font = get_scaled_font
        self.resize_screen = resize_screen
        self.clock = clock
        self.joystick = joystick

        try:
            self.bg_image = pygame.image.load("assets/background/select_screen_bg.png")
        except:
            self.bg_image = None

        self.blink_timer = 0
        self.image_cache = {}
        self.valid_maps = []

        for map_name in map_list:
            path = f"assets/maps/{map_name}.png"
            try:
                image = pygame.image.load(path)
                self.image_cache[map_name] = image
                self.valid_maps.append(map_name)
            except:
                print(f"[INFO] 이미지 없음: {path} → 제외됨")

        self.selected_idx = 0 if self.valid_maps else -1

    def show(self):
        if not self.valid_maps:
            print("[ERROR] 유효한 맵이 없습니다.")
            return None

        if len(self.valid_maps) == 1:
            selected_map_name = self.valid_maps[0]
        else:
            selecting = True
            countdown_start = time.time()
            countdown_seconds = 60

            while selecting:
                width, height = self.screen.get_size()
                elapsed = int(time.time() - countdown_start)
                remaining = max(0, countdown_seconds - elapsed)

                self._draw_background(width, height)
                self._draw_map_gallery(width, height)
                self._draw_selected_map_large(width, height)
                self._draw_footer(width, height, remaining)
                pygame.display.flip()
                self.clock.tick(30)

                if remaining <= 0:
                    break

                selecting = self._handle_input()

        selected_map_name = self.valid_maps[self.selected_idx]
        selected_bg = self.image_cache.get(selected_map_name, None)

        show_loading_screen(
            screen=self.screen,
            get_scaled_font=self.get_scaled_font,
            clock=self.clock,
            message="Loading Map...",
            background=selected_bg
        )

        return selected_map_name

    def _draw_background(self, width, height):
        if self.bg_image:
            bg_scaled = pygame.transform.scale(self.bg_image, (width, height))
            self.screen.blit(bg_scaled, (0, 0))
        else:
            self.screen.fill((0, 0, 0))

    def _draw_map_gallery(self, width, height):
        center_x = width // 2
        center_y = height * 0.15
        spacing = width * 0.28
        base_thumb_height = height * 0.18

        indexes = [
            (self.selected_idx - 1) % len(self.valid_maps),
            self.selected_idx,
            (self.selected_idx + 1) % len(self.valid_maps)
        ]

        for i, idx in enumerate(indexes):
            map_name = self.valid_maps[idx]
            image = self.image_cache[map_name]

            thumb_height = base_thumb_height * (1.15 if idx == self.selected_idx else 1.0)
            aspect_ratio = image.get_width() / image.get_height()
            thumb_width = int(thumb_height * aspect_ratio)
            scaled = pygame.transform.smoothscale(image, (thumb_width, int(thumb_height)))

            offset_x = (i - 1) * spacing
            x = int(center_x - thumb_width // 2 + offset_x)
            y = int(center_y - thumb_height // 2)

            self.screen.blit(scaled, (x, y))

            if idx == self.selected_idx:
                pygame.draw.rect(self.screen, RED, (x, y, thumb_width, thumb_height), 5, border_radius=10)

    def _draw_selected_map_large(self, width, height):
        map_name = self.valid_maps[self.selected_idx]
        image = self.image_cache[map_name]

        card_width = width * 0.5
        card_height = height * 0.4
        card_rect = pygame.Rect((width - card_width) // 2, height * 0.35, card_width, card_height)

        if image:
            scaled = pygame.transform.smoothscale(image, (int(card_width), int(card_height)))
            self.screen.blit(scaled, card_rect.topleft)

        font = self.get_scaled_font(0.05)
        name_surface = font.render(map_name.upper(), True, WHITE)
        name_rect = name_surface.get_rect(center=(width // 2, card_rect.bottom + 30))
        self.screen.blit(name_surface, name_rect)

    def _draw_footer(self, width, height, remaining_seconds):
        self.blink_timer += 1
        font = self.get_scaled_font(0.03)

        if (self.blink_timer // 30) % 2 == 0:
            text = "Left / Right : Change Map    O Button : Select"
            surface = font.render(text, True, RED)
            rect = surface.get_rect(center=(width // 2, height * 0.95))
            self.screen.blit(surface, rect)

        timer_font = self.get_scaled_font(0.04)
        timer_text = timer_font.render(f"{remaining_seconds}s", True, WHITE)
        self.screen.blit(timer_text, timer_text.get_rect(topright=(width - 20, 20)))

    def _handle_input(self):
        dx, _, select, _ = self.joystick.simple_select_events()

        if select:
            return False
        elif dx != 0:
            next_idx = (self.selected_idx - dx) % len(self.valid_maps)
            self._animate_slide(dx)
            self.selected_idx = next_idx

        return True

    def _animate_slide(self, direction):
        width = self.screen.get_width()
        total_offset = int(width * 0.28 * direction)
        steps = 10

        for i in range(steps):
            t = i / (steps - 1)
            easing = 1 - (1 - t) ** 2
            offset = int(total_offset * easing)

            self._draw_background(width, self.screen.get_height())
            self._draw_map_gallery_with_offset(width, self.screen.get_height(), -offset)
            pygame.display.flip()
            self.clock.tick(60)

    def _draw_map_gallery_with_offset(self, width, height, offset):
        center_x = width // 2 + offset
        center_y = height * 0.15
        spacing = width * 0.28
        base_thumb_height = height * 0.18

        indexes = [
            (self.selected_idx - 1) % len(self.valid_maps),
            self.selected_idx,
            (self.selected_idx + 1) % len(self.valid_maps)
        ]

        for i, idx in enumerate(indexes):
            map_name = self.valid_maps[idx]
            image = self.image_cache[map_name]

            thumb_height = base_thumb_height * (1.15 if idx == self.selected_idx else 1.0)
            aspect_ratio = image.get_width() / image.get_height()
            thumb_width = int(thumb_height * aspect_ratio)
            scaled = pygame.transform.smoothscale(image, (thumb_width, int(thumb_height)))

            offset_x = (i - 1) * spacing
            x = int(center_x - thumb_width // 2 + offset_x)
            y = int(center_y - thumb_height // 2)

            self.screen.blit(scaled, (x, y))

            if idx == self.selected_idx:
                pygame.draw.rect(self.screen, RED, (x, y, thumb_width, thumb_height), 5, border_radius=10)
