from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from PySide2 import QtWidgets


def main():
    # type: () -> None
    """Main entry point of the application."""
    app = QtWidgets.QApplication([])
    window = QtWidgets.QWidget()
    window.show()
    app.exec_()
