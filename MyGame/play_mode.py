import random
# 💖 [수정] pico2d의 grab_cursor, hide_cursor 등을 사용하기 위해 import * 로 변경합니다.
from pico2d import *

import game_framework
import game_world

# from arrow import Arrow # (현재 사용 안 함)
from player import Player
# from ground import Ground # (현재 사용 안 함)
# from ball import Ball # (현재 사용 안 함)
from zombie import Zombie # 💖 [수정] 주석 해제
from camera import Camera
import enemy1

player = None
zombie = None # 💖 [수정] 주석 해제
camera = None


def handle_events():
    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        else:
            player.handle_event(event)


def init():
    global player
    global camera
    global zombie # 💖 [추가] zombie 전역 변수

    # ground = Ground() # (현재 사용 안 함)
    # game_world.add_object(ground, 0) # (현재 사용 안 함)

    player = Player()
    game_world.add_object(player, 1)

    # 💖💖💖 [아래 블록 수정] 💖💖💖

    # 💖 1. Enemy1 10마리 생성 및 추가
    # (충돌 그룹에 player.sword는 한 번만 등록)
    game_world.add_collision_pair('sword:enemy', player.sword, None)

    # 💖 [삭제] 2. [추가] 검기(Bullet) vs Enemy 충돌 그룹 등록
    # 💖 [삭제] game_world.add_collision_pair('player_bullet:enemy', None, None)

    for i in range(10):
        # 💖 2-1. Enemy1 생성
        enemy = enemy1.Enemy1()

        # 💖 2-2. 게임 월드에 추가
        game_world.add_object(enemy, 1)

        # 💖 2-3. [수정] Enemy를 두 충돌 그룹 모두에 추가
        game_world.add_collision_pair('sword:enemy', None, enemy)

    camera = Camera()


def update():
    game_world.update()

    # 1. 카메라가 먼저 플레이어와 마우스(스크린) 위치를 기준으로 업데이트됨
    camera.update(player, player.mouse_x, player.mouse_y)

    # 💖 [추가] 2. 변환된 마우스 '월드' 좌표를 플레이어 객체에 저장
    player.mouse_world_x = camera.world_l + player.mouse_x
    player.mouse_world_y = camera.world_b + player.mouse_y

    game_world.handle_collisions()


def draw():
    clear_canvas()
    game_world.render(camera)
    update_canvas()


def finish():
    game_world.clear()


def pause(): pass


def resume(): pass