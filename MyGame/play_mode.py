import random
import math
from pico2d import *

import game_framework
import game_world

from player import Player
from camera import Camera
import enemy1
import boss
from map import Map
from bullet import Bullet  # 총알 생성용

from pico2d import hide_cursor, show_cursor
# ---------------------------------------------------------
# Global Variables
# ---------------------------------------------------------
player = None
camera = None
game_map = None
font = None

# 게임 진행 스테이지 (0 ~ 6)
stage = 0
stage_timer = 0.0  # 스테이지별 시간 체크용
stage_1_cleared_condition = False  # 제 1장 클리어 플래그
player_start_hp = 0  # 제 2장 HP 체크용

# 💖 [추가] 0장 전용: 움직인 시간 누적 변수
accumulated_move_time = 0.0

bgm = None
boss_bgm = None

def handle_events():
    events = get_events()
    for event in events:
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        else:
            if player:
                player.handle_event(event)


def init():
    global player, camera, game_map, font
    global stage, stage_timer, stage_1_cleared_condition
    global accumulated_move_time
    global bgm, boss_bgm  # 💖
    global crosshair_image  # 💖

    # 💖 [추가] 시스템 마우스 커서 숨기기
    hide_cursor()

    # 💖 [추가] 조준선 이미지 로드
    crosshair_image = load_image('./Assets/UI/Mouse.png')

    font = load_font('malgun.ttf', 40)

    # 💖 [추가] BGM 로드 및 재생
    bgm = load_music('./Assets/Sounds/BGM.mp3')  # 파일명 맞춰주세요
    bgm.set_volume(32)
    bgm.repeat_play()

    boss_bgm = load_music('./Assets/Sounds/BossBGM.mp3')  # 파일명 맞춰주세요
    boss_bgm.set_volume(40)

    # 1. 맵 생성
    game_map = Map()
    game_world.add_object(game_map, 0)

    # 2. 플레이어 생성
    player = Player()
    game_world.add_object(player, 3)

    # 3. 카메라 생성
    camera = Camera()

    # 4. 충돌 그룹 초기화
    game_world.add_collision_pair('sword:enemy', player.sword, None)
    game_world.add_collision_pair('player:enemy_bullet', player, None)
    game_world.add_collision_pair('sword:enemy_bullet', player.sword, None)

    # 미션 초기화
    stage = 0
    stage_timer = 0.0
    accumulated_move_time = 0.0  # 💖 초기화
    stage_1_cleared_condition = False


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
def get_random_offscreen_pos():
    l, b = camera.world_l, camera.world_b
    w, h = camera.canvas_width, camera.canvas_height

    side = random.randint(0, 3)
    margin = 100

    if side == 0:
        x = l - margin; y = random.randint(int(b), int(b + h))
    elif side == 1:
        x = l + w + margin; y = random.randint(int(b), int(b + h))
    elif side == 2:
        x = random.randint(int(l), int(l + w)); y = b - margin
    else:
        x = random.randint(int(l), int(l + w)); y = b + h + margin
    return x, y


def spawn_bullet_to_player(count=1):
    for _ in range(count):
        bx, by = get_random_offscreen_pos()
        angle = math.atan2(player.y - by, player.x - bx)
        bullet = Bullet(bx, by, angle)
        game_world.add_object(bullet, 2)
        game_world.add_collision_pair('player:enemy_bullet', None, bullet)
        game_world.add_collision_pair('sword:enemy_bullet', None, bullet)


def get_enemy_count():
    count = 0
    for o in game_world.world[1]:
        if isinstance(o, enemy1.Enemy1): count += 1
    return count


def get_boss_count():
    count = 0
    for o in game_world.world[1]:
        if isinstance(o, boss.Boss): count += 1
    return count


def get_bullet_count():
    count = 0
    for o in game_world.world[2]:
        if isinstance(o, Bullet): count += 1
    return count


# ---------------------------------------------------------
# Update & Mission Logic
# ---------------------------------------------------------
def update():
    global stage, stage_timer, stage_1_cleared_condition, player_start_hp
    global accumulated_move_time

    game_world.update()

    camera.update(player, player.mouse_x, player.mouse_y)
    player.mouse_world_x = camera.world_l + player.mouse_x
    player.mouse_world_y = camera.world_b + player.mouse_y

    game_world.handle_collisions()

    # === 미션 진행 로직 ===

    # [제 0장] 움직이기 (5초 누적 이동)
    if stage == 0:
        # 💖 플레이어가 이동 중인지 확인 (벡터가 0이 아니면 이동 중)
        if player.xdir != 0 or player.ydir != 0:
            accumulated_move_time += game_framework.frame_time

        # 5초 이상 움직였으면 클리어
        if accumulated_move_time >= 5.0:
            stage = 1
            stage_timer = 0.0
            print("Stage 0 Cleared!")

    # [제 1장] 칼로 총알 베기
    elif stage == 1:
        stage_timer += game_framework.frame_time
        if stage_timer > 1.0:
            if int(stage_timer) > int(stage_timer - game_framework.frame_time):
                spawn_bullet_to_player(1)

        if stage_1_cleared_condition:
            for o in game_world.world[2]:
                if isinstance(o, Bullet): game_world.remove_object(o)
            stage = 2
            stage_timer = 0.0
            player_start_hp = player.hp
            print("Stage 1 Cleared!")

    # [제 2장] 구르기
    elif stage == 2:
        stage_timer += game_framework.frame_time
        if 1.0 < stage_timer < 1.0 + game_framework.frame_time:
            for i in range(16): spawn_bullet_to_player(1)

        if player.hp < player_start_hp:
            print("Hit! Retrying Stage 2...")
            player.hp = player_start_hp
            stage_timer = 0.0
            for o in game_world.world[2]:
                if isinstance(o, Bullet): game_world.remove_object(o)

        if stage_timer > 2.0 and get_bullet_count() == 0 and player.hp >= player_start_hp:
            stage = 3
            stage_timer = 0.0
            bx, by = get_random_offscreen_pos()
            mob = enemy1.Enemy1()
            mob.x, mob.y = bx, by
            game_world.add_object(mob, 1)
            game_world.add_collision_pair('sword:enemy', None, mob)
            game_world.add_collision_pair('sword_bullet:enemy', None, mob)
            print("Stage 2 Cleared!")

    # [제 3장] 1대1 맞짱
    elif stage == 3:
        if get_enemy_count() == 0:
            stage = 4
            stage_timer = 0.0
            for i in range(5):
                bx, by = get_random_offscreen_pos()
                mob = enemy1.Enemy1()
                mob.x, mob.y = bx, by
                game_world.add_object(mob, 1)
                game_world.add_collision_pair('sword:enemy', None, mob)
                game_world.add_collision_pair('sword_bullet:enemy', None, mob)
            print("Stage 3 Cleared!")

    # [제 4장] 다구리
    elif stage == 4:
        if get_enemy_count() == 0:
            stage = 5
            stage_timer = 0.0
            print("Stage 4 Cleared! BOSS TIME!")

            # 💖 [추가] 보스 스테이지 진입 시 BGM 교체
            bgm.stop()
            boss_bgm.repeat_play()

            for i in range(2):
                bx, by = get_random_offscreen_pos()
                boss_obj = boss.Boss()
                boss_obj.x, boss_obj.y = bx, by
                game_world.add_object(boss_obj, 1)
                game_world.add_collision_pair('sword:enemy', None, boss_obj)
                game_world.add_collision_pair('sword_bullet:enemy', None, boss_obj)
                game_world.add_collision_pair('player:boss', player, boss_obj)

        # [제 5장] 보스전
    elif stage == 5:
        # 클리어 조건: 보스 '모두' 사망
        # (get_boss_count는 현재 월드에 있는 모든 Boss 객체 수를 세므로,
        #  2마리 다 죽어야 0이 되어 클리어됩니다.)
        if get_boss_count() == 0:
            stage = 6  # CLEAR 화면
            print("Stage 5 Cleared! ALL CLEAR!")


def draw():
    clear_canvas()
    game_world.render(camera)

    cx = 1920 // 2
    cy = 1080 // 2 + 300

    if stage == 0:
        font.draw(cx - 150, cy, "제 0장 : 움직이기", (255, 255, 0))
        font.draw(cx - 150, cy - 50, "WASD로 움직이시오", (255, 255, 255))

        # 💖 [추가] 누적 시간 표시 (남은 시간)
        remain_time = max(0, 5.0 - accumulated_move_time)
        font.draw(cx - 150, cy - 100, f"남은 시간: {remain_time:.1f}초", (255, 100, 100))

    elif stage == 1:
        font.draw(cx - 200, cy, "제 1장 : 칼로 총알 베기", (255, 255, 0))
        font.draw(cx - 200, cy - 50, "좌클릭하여 칼로 총알을 베시오", (255, 255, 255))

    elif stage == 2:
        font.draw(cx - 150, cy, "제 2장 : 구르기", (255, 255, 0))
        font.draw(cx - 200, cy - 50, "우클릭하여 총알을 피하시오", (255, 255, 255))

    elif stage == 3:
        font.draw(cx - 200, cy, "제 3장 : 몬스터와 1 대 1 맞짱", (255, 255, 0))
        font.draw(cx - 200, cy - 50, "몬스터와 싸워 이기시오", (255, 255, 255))

    elif stage == 4:
        font.draw(cx - 200, cy, "제 4장 : 몬스터의 다구리", (255, 255, 0))
        font.draw(cx - 200, cy - 50, "몬스터 5마리를 죽이시오", (255, 255, 255))

    elif stage == 5:
        font.draw(cx - 150, cy, "제 5장 : 보스 등장", (255, 255, 0))
        font.draw(cx - 150, cy - 50, "보스를 죽이시오", (255, 255, 255))

    elif stage == 6:
        font.draw(1920 // 2 - 100, 1080 // 2, "CLEAR!!", (255, 50, 50))

    if crosshair_image and player:
        crosshair_image.draw(player.mouse_x, player.mouse_y,64,64)

    update_canvas()


def finish():
    game_world.clear()


def pause(): pass


def resume(): pass