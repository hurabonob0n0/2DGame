# graphic_sys.py
import moderngl
import numpy as np
from settings import *
import camera


class GraphicsEngine:
    def __init__(self):
        self.ctx = None
        self.prog = None
        self.vbo = None
        self.vao = None

    def initialize(self):
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # 기본 쿼드: 중심점(0,0) 기준, 크기 1x1 (-0.5 ~ 0.5)
        vertices = np.array([
            -0.5, -0.5, 0.0, 1.0,  # x, y, u, v
            0.5, -0.5, 1.0, 1.0,
            -0.5, 0.5, 0.0, 0.0,
            0.5, 0.5, 1.0, 0.0,
        ], dtype='f4')

        self.vbo = self.ctx.buffer(vertices.tobytes())
        self._load_shaders()

    def _load_shaders(self):
        self.prog = self.ctx.program(
            vertex_shader="""
            #version 330
            in vec2 in_vert;
            in vec2 in_uv;
            out vec2 v_uv;

            // [변경] 개별 위치값 대신 행렬을 받습니다.
            uniform mat4 u_view_projection; // 카메라 + 투영 행렬
            uniform mat4 u_model;           // 오브젝트 월드 행렬

            uniform vec2 u_uv_offset;
            uniform vec2 u_uv_scale;

            void main() {
                v_uv = in_uv * u_uv_scale + u_uv_offset;

                // P * V * M 순서로 곱합니다 (OpenGL은 열 우선이지만 GLSL 곱셈 순서는 수학과 동일)
                gl_Position = u_view_projection * u_model * vec4(in_vert, 0.0, 1.0);
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

    def render_sprite(self, texture, model_matrix, view_proj_matrix, uv_offset=(0, 0), uv_scale=(1, 1)):
        texture.use(location=0)

        vp_matrix = np.identity(4, dtype='f4')

        # 현재 활성화된 카메라가 있을 때만 행렬을 가져옴
        if camera.active_camera:
            vp_matrix = camera.active_camera.get_view_projection_matrix()
            # 셰이더에 전달
            self.prog['u_view_projection'].write(vp_matrix.tobytes())

        self.prog['u_model'].write(model_matrix.tobytes())

        self.prog['u_texture'].value = 0
        self.prog['u_alpha_threshold'].value = 0.1
        self.prog['u_uv_offset'].value = uv_offset
        self.prog['u_uv_scale'].value = uv_scale

        self.vao.render(moderngl.TRIANGLE_STRIP)

    def clear(self):
        self.ctx.clear(*CLEAR_COLOR)


sys_graphics = GraphicsEngine()