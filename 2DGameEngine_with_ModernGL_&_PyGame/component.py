# --- Components ---
class Component:
    def __init__(self, game_object):
        self.game_object = game_object
        self.name = None
        self.active = True

    def update(self, dt): pass

    def render(self): pass