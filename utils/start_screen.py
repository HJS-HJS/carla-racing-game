import pygame
import sys
from utils.color import RED, WHITE

class StartScreen:
    def __init__(self, screen, get_scaled_font, resize_screen, clock):
        self.screen = screen
        self.get_scaled_font = get_scaled_font
        self.resize_screen = resize_screen
        self.clock = clock
        self.logo_size = max(80, int(screen.get_width() * 0.10))
        try:
            self.bg_image = pygame.image.load("assets/background/start_bg.png")
        except:
            self.bg_image = None
        try:
            self.logo1 = pygame.image.load("assets/logo/carla.png")
            self.logo2 = pygame.image.load("assets/logo/rise.png")
            self.logo1 = pygame.transform.scale(self.logo1, (self.logo_size, self.logo_size))
            self.logo2 = pygame.transform.scale(self.logo2, (self.logo_size, self.logo_size))
        except:
            self.logo1 = None
            self.logo2 = None
        self.blink = True
        self.blink_timer = 0

    def show(self):
        width, height = self.screen.get_size()
        self._draw_background(width, height)
        self._draw_center_text(width, height)
        self._draw_footer(width, height)
        pygame.display.flip()
        self.clock.tick(30)

    def _draw_background(self, width, height):
        if self.bg_image:
            bg_scaled = pygame.transform.scale(self.bg_image, (width, height))
            self.screen.blit(bg_scaled, (0, 0))
        else:
            self.screen.fill((0, 0, 0))

    def _draw_center_text(self, width, height):
        now = pygame.time.get_ticks()
        press_font = self.get_scaled_font(0.045)

        if self.blink:
            press_text = press_font.render("PRESS O TO START", True, RED)
            self.screen.blit(press_text, press_text.get_rect(center=(width // 2, height // 2 + 60)))

        if now - self.blink_timer > 500:
            self.blink = not self.blink
            self.blink_timer = now

    def _draw_footer(self, width, height):
        small_font = self.get_scaled_font(0.02)
        maker1 = small_font.render("Made by SJY", True, WHITE)
        maker2 = small_font.render("Made by HJS", True, WHITE)
        self.screen.blit(maker1, (width * 0.9, height - height * 0.08))
        self.screen.blit(maker2, (width * 0.9, height - height * 0.04))
        if self.logo1:
            self.screen.blit(self.logo1, (self.logo_size + 20, height - (self.logo_size + 10)))
        if self.logo2:
            self.screen.blit(self.logo2, (10, height - (self.logo_size + 10)))
