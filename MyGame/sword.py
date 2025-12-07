import math
from pico2d import load_image, draw_rectangle, SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT
import game_framework
from state_machine import StateMachine
from sword_bullet import SwordBullet # 💖 [추가] 임포트

def attack_down(e):
    """ 마우스 왼쪽 버튼이 눌렸는지 확인하는 이벤트 핸들러 """
    if e[0] != 'INPUT': return False
    if e[1].type != SDL_MOUSEBUTTONDOWN: return False
    if e[1].button != SDL_BUTTON_LEFT: return False
    return True

def timeout(e):
    """ 'TIMEOUT' 이벤트인지 확인하는 핸들러 """
    return e[0] == 'TIMEOUT'

# 💖 [추가] 칼의 'Idle' 상태 (마우스 따라다니기)
class Idle:
    def __init__(self, sword):
        self.sword = sword

    def enter(self, e):
        pass  # 특별히 할 것 없음

    def exit(self, e):
        # 💖 공격이 시작될 때(exit) 현재 각도를 '공격 시작 각도'로 저장
        if attack_down(e):
            self.sword.attack_start_angle = self.sword.angle
            self.fire_sword_bullet(self.sword.attack_start_angle)  # 중간 각도(목표점)로 발사

    def do(self):
        # 💖 기존 update 함수의 '마우스 따라다니기' 로직
        # 1. 각도 업데이트
        px, py = self.sword.player.x, self.sword.player.y
        mx, my = self.sword.player.mouse_world_x, self.sword.player.mouse_world_y
        self.sword.angle = math.atan2(my - py, mx - px)
        # 2. 위치 업데이트
        self.sword.update_pivot_and_position()

    def draw(self, camera):
        self.sword.draw_rotated_image(camera)

    def fire_sword_bullet(self, angle):
        import game_world
        # 발사 위치: 플레이어 중심에서 약간 앞
        spawn_dist = 30
        bx = self.sword.player.x + math.cos(angle) * spawn_dist
        by = self.sword.player.y + math.sin(angle) * spawn_dist

        bullet = SwordBullet(bx, by, angle)
        game_world.add_object(bullet, 2)  # 레이어 2 (플레이어와 적 사이)
        # 💖 [핵심] 충돌 그룹에 등록
        game_world.add_collision_pair('sword_bullet:enemy', bullet, None)


# 💖 [추가] 칼의 'Swing' 상태 (휘두르기)
class Swing:
    def __init__(self, sword):
        self.sword = sword
        # 💖 [수정] 0.1초로 변경
        self.phase1_duration = 0.1  # 1단계 (휘두르기)
        # 💖 [수정] 0.1초로 변경
        self.phase2_duration = 0.1  # 2단계 (복귀)
        # 💖 [수정] 총 0.2초 (0.1 + 0.1)
        self.total_duration = self.phase1_duration + self.phase2_duration

    def enter(self, e):
        self.timer = 0.0
        # 💖 Idle 상태에서 저장해둔 '공격 시작 각도'를 가져옴
        start_angle = self.sword.attack_start_angle

        # 💖 [추가] 마우스 x좌표를 기준으로 스윙 방향 결정
        px = self.sword.player.x
        mx = self.sword.player.mouse_world_x

        if mx >= px:
            # 💖 마우스가 오른쪽에 있으면: +60도 -> -60도
            self.swing_start_angle = start_angle + math.radians(60)
            self.swing_mid_angle = start_angle - math.radians(60)
        else:
            # 💖 마우스가 왼쪽에 있으면: -60도 -> +60도
            self.swing_start_angle = start_angle - math.radians(60)
            self.swing_mid_angle = start_angle + math.radians(60)

    def exit(self, e):
        pass  # 0.2초가 지나면 Cooldown 상태로

    def do(self):
        self.timer += game_framework.frame_time

        # 1. 💖 [수정] 0.2초가 모두 지났으면 'SWING_FINISH' 이벤트를 보내 Cooldown 상태로
        if self.timer >= self.total_duration:
            self.sword.state_machine.handle_state_event(('SWING_FINISH', None))
            return

        # 2. 💖 [수정] 1단계: 0.1초 동안 -60도 -> +60도 휘두르기
        if self.timer <= self.phase1_duration:
            # (self.timer / 0.1) 0.0 ~ 1.0 사이의 진행률
            progress = self.timer / self.phase1_duration
            # 선형 보간(Lerp)으로 각도 계산
            self.sword.angle = (1 - progress) * self.swing_start_angle + progress * self.swing_mid_angle

        # 3. 💖 [수정] 2단계: 0.1초 동안 +60도 -> 현재 마우스 각도로 복귀
        else:
            # (self.timer - 0.1) / 0.1, 0.0 ~ 1.0 사이의 진행률
            progress = (self.timer - self.phase1_duration) / self.phase2_duration

            # 실시간 마우스 각도를 다시 계산 (복귀 목표)
            px, py = self.sword.player.x, self.sword.player.y
            mx, my = self.sword.player.mouse_world_x, self.sword.player.mouse_world_y
            target_mouse_angle = math.atan2(my - py, mx - px)

            # 선형 보간(Lerp)으로 각도 계산
            self.sword.angle = (1 - progress) * self.swing_mid_angle + progress * target_mouse_angle

        # 4. 💖 결정된 각도(self.sword.angle)로 칼의 실제 위치 업데이트
        self.sword.update_pivot_and_position()



    def draw(self, camera):
        # 1. 💖 칼을 먼저 그린다 (이것은 self.sword.angle을 사용)
        self.sword.draw_rotated_image(camera)

        # 2. 💖 [수정] 검기(Aura)를 그린다

        # 💖 고정된 각도(공격 시작 각도)를 사용
        fixed_angle = self.sword.attack_start_angle

        # 💖 고정된 각도를 기준으로 칼의 '손잡이' 위치 계산
        fixed_hilt_x = self.sword.pivot_x + self.sword.r * math.cos(fixed_angle)
        fixed_hilt_y = self.sword.pivot_y + self.sword.r * math.sin(fixed_angle)

        # 💖 고정된 '손잡이' 위치를 기준으로 '이미지 중심' 위치 계산
        draw_center_x = fixed_hilt_x + self.sword.center_offset * math.cos(fixed_angle)
        draw_center_y = fixed_hilt_y + self.sword.center_offset * math.sin(fixed_angle)

        self.sword.aura_image.clip_composite_draw(
            0, 0, self.sword.aura_image_w, self.sword.aura_image_h,  # 원본 이미지
            fixed_angle + math.pi * 0.2, '',  # 💖 [수정] 고정된 각도 사용
            draw_center_x - camera.world_l,  # 그릴 x
            draw_center_y - camera.world_b,  # 그릴 y
            self.sword.aura_draw_w,  # 그릴 너비
            self.sword.aura_draw_h  # 그릴 높이
        )


# 💖 [새로 추가] 쿨다운 상태 (마우스는 따라가지만 공격은 안 됨)
class Cooldown:
    def __init__(self, sword):
        self.sword = sword
        self.cooldown_duration = 0.5

    def enter(self, e):
        self.timer = 0.0

    def exit(self, e):
        pass  # 0.8초가 지나면 Idle로

    def do(self):
        self.timer += game_framework.frame_time

        # 1. 💖 0.8초가 지나면 'TIMEOUT' 이벤트를 보내 Idle 상태로 복귀
        if self.timer >= self.cooldown_duration:
            self.sword.state_machine.handle_state_event(('TIMEOUT', None))
            return

        # 2. 💖 'Idle' 상태와 동일하게 마우스를 따라다님
        px, py = self.sword.player.x, self.sword.player.y
        mx, my = self.sword.player.mouse_world_x, self.sword.player.mouse_world_y
        self.sword.angle = math.atan2(my - py, mx - px)
        self.sword.update_pivot_and_position()

    def draw(self, camera):
        self.sword.draw_rotated_image(camera)


class Sword:
    def __init__(self, player):
        self.image = load_image('./Assets/Weapon/SWORD.png')
        self.aura_image = load_image('./Assets/Weapon/SWORD_AURA.png')

        self.player = player
        self.r = 30  # 💖 r 값 (30)
        self.pivot_x, self.pivot_y = 0, 0
        self.angle = 0.0

        self.image_w = 893
        self.image_h = 310

        self.draw_w = 75  # 가로 100px
        self.draw_h = 25  # 세로 50px

        self.center_offset = self.draw_w / 2.0

        self.aura_image_w = 1000  # (SWORD_AURA.jpg의 원본 너비, 1000x1000 가정)
        self.aura_image_h = 1000  # (SWORD_AURA.jpg의 원본 높이, 1000x1000 가정)
        self.aura_draw_w = 150  # (칼보다 조금 더 크게)
        self.aura_draw_h = 150  # (칼보다 조금 더 크게)

        # 💖 [추가] 공격 시작 각도 저장 변수
        self.attack_start_angle = 0.0

        # 💖 [수정] 상태 머신 정의 (Cooldown 상태 추가)
        self.IDLE = Idle(self)
        self.SWING = Swing(self)
        self.COOLDOWN = Cooldown(self)  # 💖 [추가] 쿨다운 상태 생성

        self.state_machine = StateMachine(
            self.IDLE,
            {
                # IDLE 상태에서 attack_down 이벤트가 오면 SWING으로
                self.IDLE: {attack_down: self.SWING},

                # SWING 상태에서 'SWING_FINISH' 이벤트가 오면 COOLDOWN으로
                self.SWING: {
                    lambda e: e[0] == 'SWING_FINISH': self.COOLDOWN
                },

                # COOLDOWN 상태에서 'TIMEOUT' 이벤트가 오면 IDLE로
                # (COOLDOWN 상태는 attack_down 이벤트를 무시함)
                self.COOLDOWN: {timeout: self.IDLE}
            }
        )

    # 💖 [수정] update 함수는 상태 머신에 위임
    def update(self):
        self.state_machine.update()

    # 💖 [추가] draw 함수도 상태 머신에 위임
    def draw(self, camera):
        self.state_machine.draw(camera)

    # 💖 [추가] 이벤트를 상태 머신으로 전달하는 함수
    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))

    # 💖 [추가] 공용 헬퍼 함수: 각도(self.angle)에 따라 칼 위치(self.x, self.y) 계산
    def update_pivot_and_position(self):
        px, py = self.player.x, self.player.y
        mx, my = self.player.mouse_world_x, self.player.mouse_world_y

        x_offset = 0
        if mx < px:  # 마우스가 플레이어 왼쪽에 있으면
            x_offset = -5
        elif mx > px:  # 마우스가 플레이어 오른쪽에 있으면
            x_offset = 5

        # 💖 [수정] self.pivot_x/y에 저장
        self.pivot_x = px + x_offset
        self.pivot_y = py

        # 💖 [수정] self.pivot_x/y 사용
        self.x = self.pivot_x + self.r * math.cos(self.angle)
        self.y = self.pivot_y + self.r * math.sin(self.angle)

    # 💖 [추가] 공용 헬퍼 함수: 계산된 위치/각도로 칼 그리기
    def draw_rotated_image(self, camera):
        draw_center_x = self.x + self.center_offset * math.cos(self.angle)
        draw_center_y = self.y + self.center_offset * math.sin(self.angle)

        self.image.clip_composite_draw(
            0, 0, self.image_w, self.image_h,
            self.angle, '',
            draw_center_x - camera.world_l,
            draw_center_y - camera.world_b,
            self.draw_w, self.draw_h
        )

    def get_bb(self):
        """ 칼의 바운딩 박스를 반환합니다. """
        # 💖 Swing 상태가 아닐 때는 충돌하지 않도록 (0,0,0,0) 반환
        if self.state_machine.cur_state != self.SWING:
            return 0, 0, 0, 0

        # 💖 [수정] 충돌 범위를 Aura 크기(150)에 맞춰 75로 늘림
        # (기존: self.draw_w / 2.0  -> 37.5)
        half_size = self.aura_draw_w / 2.0  # 150 / 2.0 = 75.0
        return self.x - half_size, self.y - half_size, self.x + half_size, self.y + half_size

    def handle_collision(self, group, other):
        """ 칼은 충돌 당해도 아무것도 하지 않습니다. """
        pass