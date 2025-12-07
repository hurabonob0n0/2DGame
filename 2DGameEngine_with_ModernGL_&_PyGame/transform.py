# transform.py
import numpy as np


def create_ortho_projection(left, right, bottom, top, near, far):
    """직교 투영 행렬 생성 (화면 좌표 -> NDC)"""
    rml = right - left
    tmb = top - bottom
    fmn = far - near

    # 열 우선(Column Major) 순서 주의 (OpenGL 호환)
    # 하지만 Numpy는 기본적으로 행 우선이므로, 전치(Transpose)해서 보내거나
    # 데이터를 만들 때 Transpose된 형태로 만들어야 합니다.
    # 여기서는 보기 편하게 만들고 tobytes(order='F')를 쓰거나 전치해서 보냅니다.

    M = np.identity(4, dtype='f4')
    M[0, 0] = 2.0 / rml
    M[1, 1] = 2.0 / tmb
    M[2, 2] = -2.0 / fmn
    M[3, 0] = -(right + left) / rml
    M[3, 1] = -(top + bottom) / tmb
    M[3, 2] = -(far + near) / fmn

    return M


def create_transformation_matrix(x, y, scale_x, scale_y, rotation_rad=0):
    """모델 행렬 생성 (크기 -> 회전 -> 이동)"""
    # 1. 이동 (Translation)
    T = np.identity(4, dtype='f4')
    T[3, 0] = x
    T[3, 1] = y

    # 2. 회전 (Rotation - Z축 기준)
    R = np.identity(4, dtype='f4')
    cos_t = np.cos(rotation_rad)
    sin_t = np.sin(rotation_rad)
    R[0, 0] = cos_t
    R[0, 1] = sin_t
    R[1, 0] = -sin_t
    R[1, 1] = cos_t

    # 3. 크기 (Scale)
    S = np.identity(4, dtype='f4')
    S[0, 0] = scale_x
    S[1, 1] = scale_y

    # 순서: Scale -> Rotate -> Translate
    # 행렬 곱셈: T * R * S
    return S @ R @ T