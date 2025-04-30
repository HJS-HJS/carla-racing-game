import math
import pygame
from utils.panels.dashboard import Dashboard
from utils.color import *

class PlayerPanel:
    def __init__(self, screen):
        self.screen = screen
        self.dashboard = Dashboard()
        self.state = {'throttle': 0.0, 'brake': 0.0, 'steering': 0.0, 'speed': 0.0, 'gear': 0}
        self.camera_image = None

    def update(self, throttle, brake, steering, speed, gear):
        self.state.update({'throttle': throttle, 'brake': brake, 'steering': steering, 'speed': speed, 'gear': gear})
        self.dashboard.update(**self.state)

    def set_camera_image(self, surface):
        self.camera_image = surface

    def draw(self):
        width, height = self.screen.get_size()
        left_rect = pygame.Rect(0, 0, width, height // 2)

        # 1. 카메라 이미지 전체에 표시
        if self.camera_image:
            image = pygame.transform.scale(self.camera_image, (left_rect.width, left_rect.height))
            self.screen.blit(image, left_rect.topleft)

        # 2. 그 위에 계기판 그리기 (겹쳐지게)
        self.dashboard.draw(self.screen, left_rect)

    def start_clock(self):
        self.dashboard.start_clock()
    
    def stop_clock(self):
        self.dashboard.stop_clock()

    def get_time_spent(self):
        return self.dashboard.get_time_spent()
    
    def initialize_time(self):
        self.dashboard.initialize_time()
    