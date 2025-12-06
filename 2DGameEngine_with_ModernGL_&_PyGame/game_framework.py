# game_framework.py

# 1. 핵심 시스템
from graphic_sys import sys_graphics
from texture_sys import sys_textures
from scene_sys import Scene, sys_scenes

# 2. 오브젝트 및 컴포넌트 시스템
from object_manager import sys_objects
from game_object import GameObject
from component import Component
from sprite_renderer import SpriteRenderer

# (선택 사항) 자주 쓰는 외부 라이브러리도 여기서 관리 가능
import pygame