import pygame

def show_loading_screen(screen, get_scaled_font, clock, message="Loading...", background=None):
    screen.fill((0, 0, 0))  # 배경 비우기

    if background:
        bg_scaled = pygame.transform.scale(background, screen.get_size())
        screen.blit(bg_scaled, (0, 0))

    font = get_scaled_font(0.07)
    text = font.render(message, True, (255, 255, 255))
    text_rect = text.get_rect(center=(int(screen.get_width() * 0.80), int(screen.get_height() * 0.93)))
    screen.blit(text, text_rect)

    pygame.display.flip()
    clock.tick(1)  # 살짝 대기 (렌더링 시간 확보용)