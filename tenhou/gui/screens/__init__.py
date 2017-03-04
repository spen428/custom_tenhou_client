from abc import ABCMeta, abstractmethod


class Screen:
    """Abstract Base Class for all Screen subclasses."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_mouse_up(self):
        pass

    @abstractmethod
    def on_mouse_motion(self):
        pass

    @abstractmethod
    def on_window_resized(self):
        pass

    @abstractmethod
    def draw_to_canvas(self, canvas):
        pass
