# graphics.py
import moderngl
import numpy as np
from settings import *


class GraphicsEngine:
    def __init__(self):
        self.ctx = None
        self.prog = None
        self.vbo = None
        self.vao = None

    def initialize(self):
        """Pygame이 만든 OpenGL 컨텍스트를 ModernGL에 연결"""
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # 기본 쿼드 (Quad) 생성
        vertices = np.array([
            -0.5, -0.5, 0.0, 1.0,
            0.5, -0.5, 1.0, 1.0,
            -0.5, 0.5, 0.0, 0.0,
            0.5, 0.5, 1.0, 0.0,
        ], dtype='f4')

        self.vbo = self.ctx.buffer(vertices.tobytes())
        self._load_shaders()

    def _load_shaders(self):
        # 셰이더: UV Offset/Scale을 이용한 텍스처 슬라이싱 지원
        self.prog = self.ctx.program(
            vertex_shader="""
            #version 330
            in vec2 in_vert;
            in vec2 in_uv;
            out vec2 v_uv;

            uniform vec2 u_pos;
            uniform vec2 u_scale;
            uniform vec2 u_resolution;
            uniform vec2 u_uv_offset;
            uniform vec2 u_uv_scale;

            void main() {
                v_uv = in_uv * u_uv_scale + u_uv_offset;
                vec2 pos = in_vert * u_scale + u_pos;
                vec2 ndc_pos = (pos / u_resolution) * 2.0 - 1.0;
                gl_Position = vec4(ndc_pos, 0.0, 1.0);
            }
            """,
            fragment_shader="""
            #version 330
            in vec2 v_uv;
            out vec4 f_color;
            uniform sampler2D u_texture;
            uniform float u_alpha_threshold;

            void main() {
                vec4 tex_color = texture(u_texture, v_uv);
                if (tex_color.a < u_alpha_threshold) discard;
                f_color = tex_color;
            }
            """
        )
        self.vao = self.ctx.vertex_array(self.prog, [
            (self.vbo, '2f 2f', 'in_vert', 'in_uv')
        ])

    def render_sprite(self, texture, pos, size, uv_offset=(0, 0), uv_scale=(1, 1)):
        texture.use(location=0)
        self.prog['u_resolution'].value = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.prog['u_pos'].value = pos
        self.prog['u_scale'].value = size
        self.prog['u_texture'].value = 0
        self.prog['u_alpha_threshold'].value = 0.1
        self.prog['u_uv_offset'].value = uv_offset
        self.prog['u_uv_scale'].value = uv_scale
        self.vao.render(moderngl.TRIANGLE_STRIP)

    def clear(self):
        self.ctx.clear(*CLEAR_COLOR)


# 모듈 레벨 싱글톤 인스턴스
sys_graphics = GraphicsEngine()