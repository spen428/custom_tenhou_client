from abc import ABCMeta, abstractmethod


class AbstractScreen(metaclass=ABCMeta):
    """Abstract Base Class for all Screen subclasses."""

    @abstractmethod
    def on_mouse_up(self):
        raise NotImplementedError()

    @abstractmethod
    def on_mouse_motion(self):
        raise NotImplementedError()

    @abstractmethod
    def on_window_resized(self):
        raise NotImplementedError()

    @abstractmethod
    def draw_to_canvas(self, canvas):
        raise NotImplementedError()
