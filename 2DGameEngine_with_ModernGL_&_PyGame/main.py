import pygame
from app import GameInstance
from scene_sys import Scene, sys_scenes
# 새로 만든 Player 클래스 import
from player import Player

class MyGameScene(Scene):
    def enter(self):
        print("Scene Entered: MyGameScene")

        # Player 클래스 인스턴스 생성
        # 내부적으로 GameObject.__init__이 호출되어 ObjectManager에 자동 등록됨
        self.player = Player(400, 300)

    def update(self, dt):
        # 씬 레벨에서 별도로 처리할 로직이 없다면 비워둬도 됩니다.
        # Player의 움직임은 Player.update()에서 처리되고,
        # object_sys.update_all()에 의해 자동으로 호출됩니다.
        pass

if __name__ == "__main__":
    game = GameInstance()

    # 첫 씬 로드
    sys_scenes.change_scene(MyGameScene())

    game.run()