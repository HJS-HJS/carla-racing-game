import pygame
import os

class RecordManager:
    def __init__(self, screen, get_scaled_font, joystick, clock):
        self.screen = screen
        self.clock = clock
        self.get_scaled_font = get_scaled_font
        self.joystick = joystick
        self.font = get_scaled_font(0.04)
        self.name_chars = list("QWERTYUIOPASDFGHJKLZXCVBNM")
        self.input_index = 0
        self.name = [''] * 5
        self.last_hat = (0, 0)  # D-Pad 상태 저장용

        try:
            self.bg_image1 = pygame.image.load("assets/background/end_bg1.jpg")
        except:
            self.bg_image1 = None
        try:
            self.bg_image2 = pygame.image.load("assets/background/end_bg2.jpg")
        except:
            self.bg_image2 = None

        # QWERTY 키보드 설정 (+ 취소, 확인, 스페이스바)
        self.qwerty_layout = [
            ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "enter"],
            ["A", "S", "D", "F", "G", "H", "J", "K", "L", "back"],
            ["Z", "X", "C", "V", "B", "N", "M", "space"]
        ]
        self.cursor_x, self.cursor_y = 0, 0

    def _load_records(self):
        if not os.path.exists(self.file_path):
            return []
        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        records = []
        for line in lines:
            try:
                name, time_str = line.strip().split(",")
                records.append((name, float(time_str)))
            except:
                continue
        return records

    def _save_records(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            for name, t in self.records:
                f.write(f"{name},{t:.2f}\n")

    def input_name(self, play_time, map):
        done = False
        self.name = [''] * 5
        self.cursor_x, self.cursor_y = 0, 0
        self.input_index = 0
        
        self.file_path = "record/" + map + "/records.txt"
        self.records = self._load_records()

        while not done:
            if self.bg_image1:
                width, height = self.screen.get_size()
                bg_scaled = pygame.transform.scale(self.bg_image1, (width, height))
                self.screen.blit(bg_scaled, (0, 0))
            else:
                self.screen.fill((0, 0, 0))
            self._draw_input_ui(play_time)
            pygame.display.flip()

            dx, dy, select, cencel = self.joystick.simple_select_events()

            self.cursor_x = (self.cursor_x + dx) % self._get_row_length(self.cursor_y)
            self.cursor_y = (self.cursor_y - dy) % len(self.qwerty_layout)
            self.cursor_x = min(self.cursor_x, self._get_row_length(self.cursor_y) - 1)

            if select:  # O 버튼 → 글자 입력/기능
                if self.input_index < 5:
                    selected_char = self.qwerty_layout[self.cursor_y][self.cursor_x]
                    if selected_char == 'back':  # 취소
                        if self.input_index > 0:
                            self.input_index -= 1
                            self.name[self.input_index] = ''
                    elif selected_char == 'enter':  # 확인
                        if self.input_index > 0:
                            done = True
                    elif selected_char == 'space':  # 스페이스바
                        self.name[self.input_index] = ' '
                        self.input_index += 1
                    else:
                        self.name[self.input_index] = selected_char
                        self.input_index += 1
                    if self.input_index >= 5:
                        done = True
            elif cencel:  # X 버튼 → 글자 삭제
                if self.input_index > 0:
                    self.input_index -= 1
                    self.name[self.input_index] = ''

            self.clock.tick(30)

        name_str = ''.join(self.name)
        self.records.append((name_str, play_time))
        self.records.sort(key=lambda x: x[1])
        self.records = self.records[:10]
        self._save_records()

    def _get_row_length(self, row):
        return len(self.qwerty_layout[row])

    def _draw_input_ui(self, play_time):
        width, height = self.screen.get_size()

        title_font = self.get_scaled_font(0.05)
        title = title_font.render("Enter the name", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(width // 2, height // 6)))

        minutes = int(play_time) // 60
        seconds = int(play_time) % 60
        milliseconds = int((play_time - int(play_time)) * 1000)
        time_str = f"Time: {minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        time_text = title_font.render(time_str, True, (255, 215, 0))
        self.screen.blit(time_text, time_text.get_rect(center=(width // 2, height // 6 + height // 10)))

        name_text = ''.join(self.name)
        try:
            current_char = self.qwerty_layout[self.cursor_y][self.cursor_x]
        except:
            current_char = '_'

        placeholder = ' _' * (5 - len(name_text) - 1)

        preview_font = self.get_scaled_font(0.055)
        preview = preview_font.render(
            f"{name_text[:self.input_index]}[{current_char}]{''.join(self.name[self.input_index+1:])}{placeholder}",
            True, (0, 255, 0)
        )
        self.screen.blit(preview, preview.get_rect(center=(width // 2, height // 2)))

        self._draw_keyboard_ui(width, height)

    def _draw_keyboard_ui(self, width, height):
        key_font = self.get_scaled_font(0.05)
        start_y = int(height * 0.8)
        key_spacing = width // 30
        extra_padding = {"enter": int(key_spacing), "back": int(key_spacing), "space": int(key_spacing)}

        for row_idx, row in enumerate(self.qwerty_layout):
            total_width = sum([key_spacing + extra_padding.get(k, 0) for k in row])
            offset_x = (width - total_width) // 2
            x_pos = offset_x

            for col_idx, key in enumerate(row):
                color = (255, 255, 255)
                if self.cursor_y == row_idx and self.cursor_x == col_idx:
                    color = (0, 255, 0)

                key_render = key_font.render(key.upper(), True, color)
                if col_idx == len(row) - 1:
                    key_rect = key_render.get_rect(center=(x_pos + 5 * key_spacing // 2, start_y + row_idx * key_spacing))
                else:
                    key_rect = key_render.get_rect(center=(x_pos + key_spacing // 2, start_y + row_idx * key_spacing))
                self.screen.blit(key_render, key_rect)
                x_pos += key_spacing + extra_padding.get(key, 0)

    def display_leaderboard(self):
        width, height = self.screen.get_size()
        title_font = self.get_scaled_font(0.04)
        if self.bg_image2:
            bg_scaled = pygame.transform.scale(self.bg_image2, (width, height))
            self.screen.blit(bg_scaled, (0, 0))
        else:
            self.screen.fill((0, 0, 0))
        title = title_font.render("Best Record TOP 10", True, (255, 255, 0))
        self.screen.blit(title, title.get_rect(center=(width // 2, height * 0.1)))

        # 테이블 헤더
        header_font = self.get_scaled_font(0.035)
        row_font = self.get_scaled_font(0.03)
        headers = ["Rank", "Time", "Name"]
        column_widths = [width * 0.2, width * 0.4, width * 0.4]
        start_y = height * 0.2
        row_height = int(height * 0.06)

        # 헤더 배경
        header_bg = pygame.Surface((width, row_height), pygame.SRCALPHA)
        header_bg.fill((200, 200, 200, 130))  # 밝은 회색, 반투명
        self.screen.blit(header_bg, (0, start_y - row_height // 2))

        # 헤더 출력
        for idx, header in enumerate(headers):
            header_text = header_font.render(header, True, (0, 0, 0))
            x = sum(column_widths[:idx]) + column_widths[idx] // 2
            self.screen.blit(header_text, header_text.get_rect(center=(x, start_y)))

        # 레코드 출력
        for i, (name, t) in enumerate(self.records):
            minutes = int(t) // 60
            seconds = int(t) % 60
            milliseconds = int((t - int(t)) * 1000)
            time_str = f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
            values = [f"{i+1:2d}", time_str, name]

            self.screen.blit(header_bg, (0, start_y + (i + 1) * row_height - row_height // 2))
            for idx, value in enumerate(values):
                text_surface = row_font.render(value, True, (50, 50, 50))
                x = sum(column_widths[:idx]) + column_widths[idx] // 2
                y = start_y + (i + 1) * row_height
                self.screen.blit(text_surface, text_surface.get_rect(center=(x, y)))

        pygame.display.flip()
        self.clock.tick(30)
