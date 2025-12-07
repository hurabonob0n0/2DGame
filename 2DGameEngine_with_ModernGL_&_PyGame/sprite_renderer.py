# sprite_renderer.py
# [중요] 변수 직접 import 제거
# from camera import active_camera  <-- 이거 지우세요!
import camera  # 모듈 전체 import

from component import Component
from graphic_sys import sys_graphics
from texture_sys import sys_textures
from transform import create_transformation_matrix


# AnimationData 클래스는 그대로...
class AnimationData:
    def __init__(self, texture, slice_x, slice_y, duration=0.15):
        self.texture = texture
        self.slice_x = slice_x
        self.slice_y = slice_y
        self.duration = duration
        self.total_frames = slice_x * slice_y
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
        texture = sys_textures.load(texture_path)
        if texture:
            anim_data = AnimationData(texture, slice_x, slice_y, duration)
            self.animations[name] = anim_data
            if self.current_anim is None:
                self.play(name)
        else:
            # [디버깅 팁] 텍스처 로드 실패 시 경고 출력
            print(f"Warning: Failed to load animation '{name}' from {texture_path}")

    def set_scale(self, scale_factor):
        self.render_scale = scale_factor

    def play(self, name):
        if name == self.current_anim_name: return
        if name in self.animations:
            self.current_anim_name = name
            self.current_anim = self.animations[name]
            self.timer = 0
            self.current_frame_idx = 0

    def update(self, dt):
        if self.current_anim:
            self.timer += dt
            if self.timer >= self.current_anim.duration:
                self.timer = 0
                self.current_frame_idx = (self.current_frame_idx + 1) % self.current_anim.total_frames

    def render(self):
        if not self.current_anim: return

        anim = self.current_anim

        uv_w = 1.0 / anim.slice_x
        uv_h = 1.0 / anim.slice_y
        col = self.current_frame_idx % anim.slice_x
        row = self.current_frame_idx // anim.slice_x
        uv_x = col * uv_w
        uv_y = row * uv_h

        if self.flip_x:
            uv_x = uv_x + uv_w
            uv_w = -uv_w

        final_width = anim.frame_width * self.render_scale
        final_height = anim.frame_height * self.render_scale

        model_matrix = create_transformation_matrix(
            self.game_object.position[0],
            self.game_object.position[1],
            final_width,
            final_height,
            rotation_rad=0
        )

        # [수정] 뷰 행렬은 여기서 구하지 않고 graphic_sys에게 맡기거나,
        # graphic_sys가 인자를 받도록 통일해야 합니다.
        # 현재 graphic_sys는 인자를 받아도 무시하고 내부에서 active_camera를 쓰므로
        # 여기서는 None을 넘겨도 되지만, 명확성을 위해 모듈 접근 방식으로 넘깁니다.

        vp_matrix = None
        if camera.active_camera:  # camera 모듈을 통해 접근 (안전함)
            vp_matrix = camera.active_camera.get_view_projection_matrix()

        sys_graphics.render_sprite(
            anim.texture,
            model_matrix,
            vp_matrix,
            uv_offset=(uv_x, uv_y),
            uv_scale=(uv_w, uv_h)
        )