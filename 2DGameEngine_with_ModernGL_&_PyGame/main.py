# main.py
import pygame
from app import GameInstance
from scene_sys import Scene, sys_scenes
from player import Player
from camera import Camera  # Camera 클래스 import


class MyGameScene(Scene):
    def enter(self):
        print("Scene Entered: MyGameScene")

        # 1. 플레이어 생성 (400, 300 위치)
        self.player = Player(400, 300)

        # 2. 카메라 생성 (초기 위치는 플레이어와 동일하게)
        # GameObject를 상속받았으므로 ObjectManager에 자동 등록됩니다.
        self.camera = Camera(400, 300)

        # (선택 사항) 줌을 당겨서 보고 싶다면?
        # self.camera.zoom = 1.5

    def update(self, dt):
        # 3. [요청하신 기능] 매 프레임 카메라가 플레이어를 따라다님
        # 카메라도 GameObject이므로 .position 속성을 가집니다.

        # 단순히 값만 대입하면 Hard Follow (딱딱하게 따라붙음)
        self.camera.position[0] = self.player.position[0]
        self.camera.position[1] = self.player.position[1]

        # [참고] 부드럽게 따라가게 하려면(Lerp) 나중에 이렇게 바꾸세요:
        # lerp_speed = 5.0 * dt
        # self.camera.position[0] += (self.player.position[0] - self.camera.position[0]) * lerp_speed
        # self.camera.position[1] += (self.player.position[1] - self.camera.position[1]) * lerp_speed


if __name__ == "__main__":
    game = GameInstance()
    sys_scenes.change_scene(MyGameScene())
    game.run()