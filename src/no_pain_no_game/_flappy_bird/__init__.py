from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import random

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

_HERE = os.path.dirname(__file__)

_SCENE_SIZE = QtCore.QSize(800, 600)
_SCENE_RECT = QtCore.QRect(
    _SCENE_SIZE.width() / -2,
    _SCENE_SIZE.height() / -2,
    _SCENE_SIZE.width(),
    _SCENE_SIZE.height(),
)

_PILLAR_X_RAND = 200
_PILLAR_Y_RAND = 150
_PILLAR_GAP = 120
_PILLAR_SPEED = 300
_PILLAR_INTERVAL = 1000

_KONAMI_SEQ = [
    QtCore.Qt.Key_Up,
    QtCore.Qt.Key_Up,
    QtCore.Qt.Key_Down,
    QtCore.Qt.Key_Down,
    QtCore.Qt.Key_Left,
    QtCore.Qt.Key_Right,
    QtCore.Qt.Key_Left,
    QtCore.Qt.Key_Right,
    QtCore.Qt.Key_B,
    QtCore.Qt.Key_A,
]


def _get_resource(f):
    # type: (str) -> str
    path = os.path.join(_HERE, "resources", f)
    if not os.path.exists(path):
        msg = "resource file not found: {!r}".format(f)
        raise RuntimeError(msg)
    return path


class _Button(QtWidgets.QPushButton):
    def __init__(self, pixmap, parent=None):
        # type: (QtGui.QPixmap, QtWidgets.QWidget | None) -> None
        super(_Button, self).__init__(parent)


class _Pillar(QtWidgets.QGraphicsItemGroup, QtCore.QObject):
    collided_with_bird = QtCore.Signal()

    def __init__(self, parent=None):
        # type: (QtCore.QObject | None) -> None
        QtCore.QObject.__init__(self, parent=parent)
        QtWidgets.QGraphicsItemGroup.__init__(self)

        pix = QtGui.QPixmap(_get_resource("pillar_top.png"))
        self.__top = QtWidgets.QGraphicsPixmapItem(pix)
        self.__top.setPos(
            -(self.__top.boundingRect().width() / 2),
            -self.__top.boundingRect().height() - _PILLAR_GAP / 2,
        )

        pix = QtGui.QPixmap(_get_resource("pillar_bottom.png"))
        self.__bottom = QtWidgets.QGraphicsPixmapItem(pix)
        self.__bottom.setPos(
            -(self.__bottom.boundingRect().width() / 2),
            _PILLAR_GAP / 2,
        )

        self.addToGroup(self.__top)
        self.addToGroup(self.__bottom)

        x = _SCENE_RECT.width() / 2 + self.__top.boundingRect().width() / 2
        x_rand = random.randint(0, _PILLAR_X_RAND)
        y_rand = random.randint(0, _PILLAR_Y_RAND)
        self.setPos(x + x_rand, y_rand)

        self.__animation = QtCore.QPropertyAnimation(self, b"_x", self)
        self.__animation.setStartValue(x + x_rand)
        self.__animation.setEndValue(-x)
        self.__animation.setEasingCurve(QtCore.QEasingCurve.Linear)
        self.__animation.setDuration((x + x_rand + x) / _PILLAR_SPEED * 1000)
        self.__animation.finished.connect(
            lambda: self.scene().removeItem(self),
        )

    @QtCore.Property(int)
    def _x(self):
        # type: () -> int
        return self.x()

    @_x.setter  # type: ignore[no-redef]
    def _x(self, value):
        # type: (int) -> None
        self.setPos(value, self.y())

        for item in self.__top.collidingItems():
            if isinstance(item, _Bird):
                self.collided_with_bird.emit()
                return

        for item in self.__bottom.collidingItems():
            if isinstance(item, _Bird):
                self.collided_with_bird.emit()
                return

    def play(self):
        # type: () -> None
        """Play the animation."""
        self.__animation.start()

    def freeze(self):
        # type: () -> None
        """Freeze the animation."""
        self.__animation.stop()


class _WingPosition:
    UP = 1
    MIDDLE = 2
    DOWN = 3


class _WingDirection:
    UP = 1
    DOWN = 2


class _Bird(QtWidgets.QGraphicsPixmapItem, QtCore.QObject):
    def __init__(self, parent=None):
        # type: (QtCore.QObject | None) -> None

        QtCore.QObject.__init__(self, parent=parent)
        QtWidgets.QGraphicsPixmapItem.__init__(self)

        self.__rotation_value = 0

        self.setPixmap(QtGui.QPixmap(_get_resource("bird_middle.png")))

        self.__wing_position = _WingPosition.MIDDLE
        self.__wing_direction = _WingDirection.UP
        self.__ground_position = _SCENE_RECT.bottom()

        self.__timer = QtCore.QTimer(self)
        self.__timer.timeout.connect(self.__update_pixmap)

        self.__r_animation = QtCore.QPropertyAnimation(self, b"_r", self)
        self.__t_animation = QtCore.QPropertyAnimation(self, b"_t", self)
        self.__t_animation.finished.connect(self.__fall)

    @QtCore.Property(int)
    def _t(self):
        # type: () -> int
        return self.y()

    @_t.setter  # type: ignore[no-redef]
    def _t(self, value):
        # type: (int) -> None
        self.moveBy(0, value - self.y())

    @QtCore.Property(int)
    def _r(self):
        # type: () -> int
        return self.__rotation_value

    @_r.setter  # type: ignore[no-redef]
    def _r(self, value):
        # type: (int) -> None
        self.__rotation_value = value
        c = self.boundingRect().center()
        t = QtGui.QTransform()
        t.translate(c.x(), c.y())
        t.rotate(value)
        t.translate(-c.x(), -c.y())
        self.setTransform(t)

    def __update_pixmap(self):
        # type: () -> None
        if self.__wing_position == _WingPosition.MIDDLE:
            if self.__wing_direction == _WingDirection.UP:
                f = "bird_up.png"
                self.__wing_position = _WingPosition.UP
                self.__wing_direction = _WingPosition.DOWN
            else:
                f = "bird_down.png"
                self.__wing_position = _WingPosition.DOWN
                self.__wing_direction = _WingPosition.UP
        else:
            f = "bird_middle.png"
            self.__wing_position = _WingPosition.MIDDLE

        self.setPixmap(QtGui.QPixmap(_get_resource(f)))

    def __fall(self):
        # type: () -> None
        if self.y() < self.__ground_position:
            self.__r_animation.stop()

            end = self.__ground_position - (self.boundingRect().height())
            self.__t_animation.setStartValue(self.y())
            self.__t_animation.setEndValue(end)
            self.__t_animation.setEasingCurve(QtCore.QEasingCurve.InQuad)
            self.__t_animation.setDuration(1000)
            self.__t_animation.start()

            self.__r_animation.setStartValue(self.__rotation_value)
            self.__r_animation.setEndValue(90)
            self.__r_animation.setEasingCurve(QtCore.QEasingCurve.InQuad)
            self.__r_animation.setDuration(1000)
            self.__r_animation.start()

    def jump(self):
        # type: () -> None
        self.__t_animation.stop()
        self.__r_animation.stop()

        y = self.y()
        end = y - self.scene().sceneRect().height() / 8
        self.__t_animation.setStartValue(y)
        self.__t_animation.setEndValue(end)
        self.__t_animation.setEasingCurve(QtCore.QEasingCurve.OutQuad)
        self.__t_animation.setDuration(285)
        self.__t_animation.start()

        self.__r_animation.setStartValue(self.__rotation_value)
        self.__r_animation.setEndValue(-20)
        self.__r_animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self.__r_animation.setDuration(200)
        self.__r_animation.start()

    def play(self):
        # type: () -> None
        self.__timer.start(80)
        self.__fall()

    def freeze(self):
        # type: () -> None
        self.__timer.stop()
        self.__t_animation.stop()
        self.__r_animation.stop()


class _KonamiView(QtWidgets.QGraphicsView):
    konami_emitted = QtCore.Signal()

    def __init__(self, parent=None):
        # type: (QtWidgets.QWidget | None) -> None
        super(_KonamiView, self).__init__(parent)

        self.__konami_index = 0

    def keyPressEvent(self, event):  # noqa: N802
        # type: (QtGui.QKeyEvent) -> None
        if event.key() == _KONAMI_SEQ[self.__konami_index]:
            self.__konami_index += 1
            if self.__konami_index == len(_KONAMI_SEQ):
                self.__konami_index = 0
                self.konami_emitted.emit()
        else:
            self.__konami_index = 0
            super(_KonamiView, self).keyPressEvent(event)


class FlappyBird(QtWidgets.QWidget):
    """Flappy Bird game widget."""

    game_started = QtCore.Signal()
    game_stopped = QtCore.Signal()
    game_finished = QtCore.Signal()
    bird_jumped = QtCore.Signal()
    god_mode_activated = QtCore.Signal()

    def __init__(self, parent=None):
        # type: (QtWidgets.QWidget | None) -> None
        super(FlappyBird, self).__init__(parent)

        self.__is_running = False
        self.__god_mode = False

        self.__pillar_timer = QtCore.QTimer(self)
        self.__pillar_timer.setInterval(_PILLAR_INTERVAL)
        self.__pillar_timer.timeout.connect(self.__add_new_pillar)

        self.setFixedSize(_SCENE_SIZE)

        self.__scene = QtWidgets.QGraphicsScene()
        self.__scene.setSceneRect(_SCENE_RECT)
        item = QtWidgets.QGraphicsTextItem("Press space to start")
        item.setFont(QtGui.QFont("Arial", 20))
        item.setPos(
            -item.boundingRect().width() / 2,
            -item.boundingRect().height() / 2,
        )
        self.__scene.addItem(item)

        view = _KonamiView(self)
        view.konami_emitted.connect(self.__enable_god_mode)
        view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        view.setScene(self.__scene)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(view)

    def __enable_god_mode(self):
        # type: () -> None
        self.__god_mode = True
        self.god_mode_activated.emit()

    def __clear_scene(self):
        # type: () -> None
        for item in self.__scene.items():
            self.__scene.removeItem(item)

    def __add_new_pillar(self):
        # type: () -> None
        pillar = _Pillar(self)
        if not self.__god_mode:
            pillar.collided_with_bird.connect(self.stop_game)
        self.__scene.addItem(pillar)
        pillar.play()

    def is_running(self):
        # type: () -> bool
        """Return whether the game is running."""
        return self.__is_running

    def start_game(self):
        # type: () -> None
        """Start the game."""
        self.__clear_scene()

        bird = _Bird(self)
        bird.setPos(
            -(_SCENE_RECT.width() / 3),
            -(bird.boundingRect().height() / 2),
        )
        self.bird_jumped.connect(bird.jump)

        self.__scene.addItem(bird)
        self.__scene.addRect(_SCENE_RECT, QtGui.QPen(QtCore.Qt.white))

        bird.play()
        self.__pillar_timer.start()

        self.game_started.emit()
        self.__is_running = True

    def stop_game(self):
        # type: () -> None
        """Stop the game."""
        self.__pillar_timer.stop()

        item = QtWidgets.QGraphicsTextItem("Press space to restart")
        item.setFont(QtGui.QFont("Arial", 20))
        item.setPos(
            -item.boundingRect().width() / 2,
            -item.boundingRect().height() / 2,
        )
        self.__scene.addItem(item)

        self.__is_running = False
        self.__god_mode = False
        self.game_stopped.emit()

        for item in self.__scene.items():
            if isinstance(item, (_Pillar, _Bird)):
                item.freeze()

    def jump(self):
        # type: () -> None
        """Make the bird jump."""
        self.bird_jumped.emit()

    def __action(self):
        # type: () -> None
        if self.is_running():
            self.jump()
        else:
            self.start_game()

    def keyPressEvent(self, event):  # noqa: N802
        # type: (QtGui.QKeyEvent) -> None
        if event.key() == QtCore.Qt.Key_Space:
            self.__action()
        elif event.key() == QtCore.Qt.Key_Escape:
            self.stop_game()
        else:
            super(FlappyBird, self).keyPressEvent(event)

    def closeEvent(self, event):  # noqa: N802
        # type: (QtGui.QCloseEvent) -> None
        self.stop_game()
        super(FlappyBird, self).closeEvent(event)
