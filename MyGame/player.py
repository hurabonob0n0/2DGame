import math
# 💖 [수정] SDLK_a, SDLK_d, SDLK_w, SDLK_s 추가
from pico2d import load_image, draw_rectangle
from sdl2 import SDL_KEYDOWN, SDLK_RIGHT, SDL_KEYUP, SDLK_LEFT, SDLK_UP, SDLK_DOWN, SDL_MOUSEMOTION, SDLK_a, SDLK_d, \
    SDLK_w, SDLK_s

import game_world
import game_framework

from state_machine import StateMachine
from sword import Sword  # 💖 [추가] Sword 클래스를 임포트


# --------------------------------------------------------------------------------
# 상태 변경을 위한 이벤트 함수
# --------------------------------------------------------------------------------

def event_stop(e):
    return e[0] == 'STOP'


def event_run(e):
    return e[0] == 'RUN'


# --------------------------------------------------------------------------------
# 플레이어 속도 관련 상수 (boy.py와 동일)
# --------------------------------------------------------------------------------
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel 30 cm
RUN_SPEED_KMPH = 30.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
WALK_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)  # RUN -> WALK로 이름 변경

# 플레이어 액션 속도 관련 상수 (boy.py와 동일)
TIME_PER_ACTION = 0.75
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 8  # 이 값은 update_animation_frame에서 동적으로 사용됨


# --------------------------------------------------------------------------------
# 상태 클래스 (Idle, Walk)
# --------------------------------------------------------------------------------

class Idle:
    """ IDLE 상태: 멈춰있을 때 """

    def __init__(self, player):
        self.player = player

    def enter(self, e):
        pass

    def exit(self, e):
        pass

    def do(self):
        # 마우스 방향 추적
        self.player.update_mouse_direction()
        # 현재 방향에 맞는 Idle 애니메이션 프레임 업데이트
        self.player.update_animation_frame('Idle')

    def draw(self, camera):  # 💖 [수정] camera 매개변수 추가
        # 현재 방향에 맞는 Idle 스프라이트 그리기
        self.player.draw_sprite('Idle', camera)  # 💖 [수정] camera 전달


class Walk:
    """ WALK 상태: 이동 중일 때 """

    def __init__(self, player):
        self.player = player

    def enter(self, e):
        pass

    def exit(self, e):
        pass

    def do(self):
        # 마우스 방향 추적
        self.player.update_mouse_direction()
        # 현재 방향에 맞는 Walk 애니메이션 프레임 업데이트
        self.player.update_animation_frame('Walk')

        # 💖 [수정] 이동 벡터 정규화
        move_x = self.player.xdir
        move_y = self.player.ydir

        magnitude = math.sqrt(move_x ** 2 + move_y ** 2)

        if magnitude > 0:
            move_x /= magnitude
            move_y /= magnitude

        self.player.x += move_x * WALK_SPEED_PPS * game_framework.frame_time
        self.player.y += move_y * WALK_SPEED_PPS * game_framework.frame_time

        # 캔버스 밖으로 나가지 않도록 고정 (필요시 주석 해제)
        # self.player.x = clamp(50, self.player.x, 1920 - 50)
        # self.player.y = clamp(50, self.player.y, 1080 - 50)

    def draw(self, camera):  # 💖 [수정] camera 매개변수 추가
        # 현재 방향에 맞는 Walk 스프라이트 그리기
        self.player.draw_sprite('Walk', camera)  # 💖 [수정] camera 전달


# --------------------------------------------------------------------------------
# 플레이어 메인 클래스
# --------------------------------------------------------------------------------

class Player:
    def __init__(self):
        self.x, self.y = 1920 // 2, 1080 // 2
        self.frame = 0.0
        self.xdir, self.ydir = 0, 0  # 키보드 입력에 따른 이동 방향

        # 💖 [수정] 마우스 스크린/월드 좌표 분리
        self.mouse_x, self.mouse_y = 0, 0  # 마우스 '스크린' 위치 (0~1920)
        self.mouse_world_x, self.mouse_world_y = 0, 0  # 마우스 '월드' 위치

        self.draw_scale = 2.5  # 캐릭터 크기 배율

        # 💖 애니메이션 방향 (문자열)과 좌우반전 (flip)
        self.anim_direction = 'F'  # 'F', 'B', 'RF', 'RB' 중 하나
        self.anim_flip = ''  # 'h' (좌우반전) 또는 '' (원본)

        self.images = {}
        self.sprite_data = {}
        self.load_resources()

        # 💖 상태 머신 정의
        self.IDLE = Idle(self)
        self.WALK = Walk(self)
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {event_run: self.WALK},
                self.WALK: {event_stop: self.IDLE}
            }
        )

        # 💖 [추가] Sword 객체 생성 (self를 넘겨줘서 player를 인식하게 함)
        self.sword = Sword(self)

    def load_resources(self):
        """ 모든 스프라이트 시트와 메타데이터(크기, 프레임 수)를 로드합니다. """
        self.images = {'Idle': {}, 'Walk': {}}
        self.sprite_data = {'Idle': {}, 'Walk': {}}

        # --- 💖 [수정] 경로를 './Assets/Player/...'로 변경 ---

        # --- IDLE 이미지 로드 ---
        self.images['Idle']['F'] = load_image('./Assets/Player/PLAYER_IDLE_F_16X23X4.png')
        self.sprite_data['Idle']['F'] = {'w': 16, 'h': 23, 'frames': 4}

        self.images['Idle']['B'] = load_image('./Assets/Player/PLAYER_IDLE_B_12X23X4.png')
        self.sprite_data['Idle']['B'] = {'w': 12, 'h': 23, 'frames': 4}

        self.images['Idle']['RF'] = load_image('./Assets/Player/PLAYER_IDLE_RF_18X23X4.png')
        self.sprite_data['Idle']['RF'] = {'w': 18, 'h': 23, 'frames': 4}

        self.images['Idle']['RB'] = load_image('./Assets/Player/PLAYER_IDLE_RB_15X23X4.png')
        self.sprite_data['Idle']['RB'] = {'w': 15, 'h': 23, 'frames': 4}

        # --- WALK 이미지 로드 ---
        self.images['Walk']['F'] = load_image('./Assets/Player/PLAYER_WALK_F_14X30X3.png')
        self.sprite_data['Walk']['F'] = {'w': 14, 'h': 30, 'frames': 3}

        self.images['Walk']['B'] = load_image('./Assets/Player/PLAYER_WALK_B_14X23X3.png')
        self.sprite_data['Walk']['B'] = {'w': 14, 'h': 23, 'frames': 3}

        self.images['Walk']['RF'] = load_image('./Assets/Player/PLAYER_WALK_RF_17X25X3.png')
        self.sprite_data['Walk']['RF'] = {'w': 17, 'h': 25, 'frames': 3}

        self.images['Walk']['RB'] = load_image('./Assets/Player/PLAYER_WALK_RB_17X26X3.png')
        self.sprite_data['Walk']['RB'] = {'w': 17, 'h': 26, 'frames': 3}

    # 💖💖💖 [수정된 부분] 💖💖💖
    def update_mouse_direction(self):
        """ 마우스 위치에 따라 self.anim_direction과 self.anim_flip을 설정합니다. (6방향) """

        # 💖 [수정] 'self.mouse_x' -> 'self.mouse_world_x'
        # 💖 [수정] 'self.mouse_y' -> 'self.mouse_world_y'

        # 플레이어 중심에서 '마우스의 월드 좌표'까지의 벡터 계산
        look_dir_x = self.mouse_world_x - self.x
        look_dir_y = self.mouse_world_y - self.y

        # 벡터를 각도로 변환 (atan2 사용)
        angle_rad = math.atan2(look_dir_y, look_dir_x)
        angle_deg = math.degrees(angle_rad)

        # 6방향으로 변환 (각 60도씩)
        if -120.0 <= angle_deg < -60.0:  # 남(South) - 'F'
            self.anim_direction = 'F'
            self.anim_flip = ''
        elif 60.0 <= angle_deg < 120.0:  # 북(North) - 'B'
            self.anim_direction = 'B'
            self.anim_flip = ''
        elif -60.0 <= angle_deg < 0.0:  # 남동(South-East) - 'RF'
            self.anim_direction = 'RF'
            self.anim_flip = ''
        elif 0.0 <= angle_deg < 60.0:  # 북동(North-East) - 'RB'
            self.anim_direction = 'RB'
            self.anim_flip = ''
        elif -180.0 <= angle_deg < -120.0:  # 남서(South-West) - 'LF' (RF + flip)
            self.anim_direction = 'RF'
            self.anim_flip = 'h'
        else:  # (120.0 <= angle_deg <= 180.0) # 북서(North-West) - 'LB' (RB + flip)
            self.anim_direction = 'RB'
            self.anim_flip = 'h'

    # 💖💖💖 [수정 완료] 💖💖💖

    def update_animation_frame(self, state_name):
        """ 현재 상태와 방향에 맞는 애니메이션 프레임을 업데이트합니다. """

        data = self.sprite_data[state_name][self.anim_direction]

        self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % data['frames']

    def draw_sprite(self, state_name, camera):  # 💖 [수정] camera 매개변수 추가
        """ 현재 상태와 방향에 맞는 스프라이트를 그립니다. """

        data = self.sprite_data[state_name][self.anim_direction]
        image = self.images[state_name][self.anim_direction]

        image.clip_composite_draw(
            int(self.frame) * data['w'], 0, data['w'], data['h'],
            0, self.anim_flip,
            # 💖 [수정] 카메라 좌표계 적용
            self.x - camera.world_l, self.y - camera.world_b,
            data['w'] * self.draw_scale, data['h'] * self.draw_scale
        )

    def update(self):
        self.state_machine.update()
        self.sword.update()  # 💖 [추가] 플레이어가 업데이트될 때 칼도 업데이트

    def handle_event(self, event):
        if event.type == SDL_MOUSEMOTION:
            # 여기서는 '스크린' 좌표를 저장하는 것이 맞습니다.
            self.mouse_x, self.mouse_y = event.x, 1080 - 1 - event.y

        # 💖 [수정] 키 입력과 마우스 입력을 별도로 처리

        # 1. 키보드 입력으로 플레이어 상태 변경 (movement)
        if event.key in (SDLK_a, SDLK_d, SDLK_w, SDLK_s):
            cur_xdir, cur_ydir = self.xdir, self.ydir
            if event.type == SDL_KEYDOWN:
                if event.key == SDLK_a:
                    self.xdir -= 1
                elif event.key == SDLK_d:
                    self.xdir += 1
                elif event.key == SDLK_w:
                    self.ydir += 1
                elif event.key == SDLK_s:
                    self.ydir -= 1
            elif event.type == SDL_KEYUP:
                if event.key == SDLK_a:
                    self.xdir += 1
                elif event.key == SDLK_d:
                    self.xdir -= 1
                elif event.key == SDLK_w:
                    self.ydir -= 1
                elif event.key == SDLK_s:
                    self.ydir += 1

            if cur_xdir != self.xdir or cur_ydir != self.ydir:
                if self.xdir == 0 and self.ydir == 0:
                    self.state_machine.handle_state_event(('STOP', None))
                else:
                    self.state_machine.handle_state_event(('RUN', None))

        # 2. 💖 [추가] 마우스 클릭 등 모든 이벤트를 칼의 상태 머신으로 전달
        #    (WASD 입력도 전달되지만, 칼의 IDLE 상태는 키보드 입력을 무시함)
        self.sword.handle_event(event)

    def draw(self, camera):  # 💖 [수정] camera 매개변수 추가
        self.state_machine.draw(camera)  # 💖 [수정] camera 전달
        self.sword.draw(camera)  # 💖 [추가] 플레이어를 그린 후 칼을 그림

        # 디버깅용 BBox 그리기 (필요시 주석 해제)
        l, b, r, t = self.get_bb()
        draw_rectangle(l - camera.world_l, b - camera.world_b, r - camera.world_l, t - camera.world_b)

    def get_bb(self):
        return self.x - 15, self.y - 25, self.x + 15, self.y + 25

    def handle_collision(self, group, other):
        pass