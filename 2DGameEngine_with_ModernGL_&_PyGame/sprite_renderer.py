# sprite_renderer.py
from component import Component
from graphic_sys import sys_graphics
from texture_sys import sys_textures

# 애니메이션 데이터를 저장할 간단한 클래스
class AnimationData:
    def __init__(self, texture, slice_x, slice_y, duration=0.15):
        self.texture = texture
        self.slice_x = slice_x
        self.slice_y = slice_y
        self.duration = duration
        self.total_frames = slice_x * slice_y
        # 프레임 크기 미리 계산
        self.frame_width = texture.width / slice_x
        self.frame_height = texture.height / slice_y


class SpriteRenderer(Component):
    def __init__(self, game_object):
        super().__init__(game_object)
        self.animations = {}
        self.current_anim = None
        self.current_anim_name = ""

        self.timer = 0
        self.current_frame_idx = 0

        self.flip_x = False

        self.render_scale = 1.0

    def add_animation(self, name, texture_path, slice_x=1, slice_y=1, duration=0.15):
        """애니메이션을 미리 로드하여 등록"""
        texture = sys_textures.load(texture_path)
        if texture:
            anim_data = AnimationData(texture, slice_x, slice_y, duration)
            self.animations[name] = anim_data

            # 첫 애니메이션이라면 바로 설정
            if self.current_anim is None:
                self.play(name)

    def set_scale(self, scale_factor):
        """외부에서 배율을 설정하는 함수"""
        self.render_scale = scale_factor

    def play(self, name):
        """해당 이름의 애니메이션으로 전환"""
        if name == self.current_anim_name:
            return  # 이미 재생 중이면 무시

        if name in self.animations:
            self.current_anim_name = name
            self.current_anim = self.animations[name]

            # 상태 초기화
            self.timer = 0
            self.current_frame_idx = 0

    def update(self, dt):
        """자체적으로 프레임 계산"""
        if self.current_anim:
            self.timer += dt
            if self.timer >= self.current_anim.duration:
                self.timer = 0
                # 다음 프레임 (Loop)
                self.current_frame_idx = (self.current_frame_idx + 1) % self.current_anim.total_frames

    def render(self):
        if not self.current_anim: return

        anim = self.current_anim

        # UV 계산
        uv_w = 1.0 / anim.slice_x
        uv_h = 1.0 / anim.slice_y

        col = self.current_frame_idx % anim.slice_x
        row = self.current_frame_idx // anim.slice_x

        uv_x = col * uv_w
        uv_y = row * uv_h

        if self.flip_x:
            uv_x = uv_x + uv_w  # 이미지의 오른쪽 끝에서 시작
            uv_w = -uv_w        # 너비를 음수로 주어 왼쪽으로 그리게 함

        final_width = anim.frame_width * self.render_scale
        final_height = anim.frame_height * self.render_scale

        sys_graphics.render_sprite(
            anim.texture,
            self.game_object.position,
            (final_width, final_height),
            uv_offset=(uv_x, uv_y),
            uv_scale=(uv_w , uv_h)
        )