# app.py
import pygame
from settings import *
from graphic_sys import sys_graphics
from scene_sys import sys_scenes
from game_object import sys_objects


class GameInstance:
    def __init__(self):
        pygame.init()
        # OpenGL 모드 윈도우 생성
        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.OPENGL | pygame.DOUBLEBUF
        )
        self.clock = pygame.time.Clock()
        self.running = True

        # 그래픽스 시스템 초기화 (이때 Context가 생성됨)
        sys_graphics.initialize()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            # 1. 입력 처리
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # 2. 업데이트
            sys_scenes.update(dt)
            sys_objects.update_all(dt)

            # 3. 렌더링
            sys_graphics.clear()
            sys_scenes.render()
            sys_objects.render_all()

            pygame.display.flip()

        pygame.quit()