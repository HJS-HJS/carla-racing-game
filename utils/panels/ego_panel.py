import pygame
from utils.color import *

class EgoPanel:
    def __init__(self, screen):
        self.screen = screen
        self.status_message = "Autonomous Vehicle"

    def set_camera_image(self, surface):
        self.camera_image = surface

    def draw(self):
        width, height = self.screen.get_size()
        rect = pygame.Rect(width // 2, height // 2, width // 2, height // 2)
        pygame.draw.rect(self.screen, LIGHT_BLUE, rect)

        if self.camera_image:
            image = pygame.transform.scale(self.camera_image, (rect.width, rect.height))
            self.screen.blit(image, rect)
            
        if self.status_message:
            message_font = pygame.font.SysFont(None, height // 20)
            text = message_font.render(self.status_message, True, (0, 0, 0))
            self.screen.blit(text, (rect.x + 20, rect.y + 20))