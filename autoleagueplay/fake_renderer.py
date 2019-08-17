from rlbot.utils.rendering.rendering_manager import RenderingManager


class FakeRenderer(RenderingManager):

    def end_rendering(self):
        self.render_state = False
