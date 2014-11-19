import sys
import subprocess

import arrow

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QState, QStateMachine
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMessageBox, QMenu,
                             QAction, QInputDialog)

from . import resources  # noqa

app = None


class Watson(object):
    def __init__(self, systray):
        self.systray = systray
        self.running = self.is_running()
        self.last_project = None

    def _run(self, *args):
        try:
            output = subprocess.check_output(
                ['watson'] + list(args), stderr=subprocess.STDOUT
            )
            return output.decode('utf-8')[:-1]
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(
                None, "Watson",
                "Error: {}".format(e.output.decode('utf-8')[:-1])
            )

    def start(self):
        if self.running:
            return

        project = self.get_project()

        if not project:
            return self.systray.stop.emit()

        if not self._run('start', *project.split()):
            return self.systray.stop.emit()

        self.systray.setToolTip('Project {} started at {:HH:mm}'.format(
            project, arrow.now().to('local')
        ))

        self.running = True

    def stop(self):
        if not self.running:
            return

        self.running = False

        self._run('stop')

    def status(self):
        return self._run('status')

    def projects(self):
        return self._run('projects').split('\n')

    def push(self):
        if self._run('push') is not None:
            self.systray.showMessage(
                "Watson", "Watson has been synchronized."
            )

    def get_project(self):
        projects = self.projects()
        current = 0

        if self.last_project and self.last_project in projects:
            current = projects.index(self.last_project)
        content, ok = QInputDialog.getItem(
            None, "Watson", "Project name:", projects,
            current=current, editable=True
        )
        if not ok or not content:
            return None

        self.last_project = content
        return content

    def is_running(self):
        return self.status() != "No project started"


class SysTray(QSystemTrayIcon):
    clicked = pyqtSignal()
    start = pyqtSignal()
    stop = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(SysTray, self).__init__(*args, **kwargs)

        self.watson = Watson(self)

        self.start_action = QAction("St&art", self)
        self.stop_action = QAction("St&op", self)

        self.menu = QMenu()
        self.menu.addAction(self.start_action)
        self.menu.addAction(self.stop_action)
        self.menu.addSeparator()
        self.menu.addAction(
            QAction("&Synchronize", self, triggered=self.watson.push)
        )
        self.menu.addSeparator()
        self.menu.addAction(
            QAction("&Quit", self, triggered=self.quit)
        )

        self.setContextMenu(self.menu)

        self.machine = QStateMachine()
        self.started = QState(self.machine)
        self.stopped = QState(self.machine)

        if self.watson.running:
            self.machine.setInitialState(self.started)
        else:
            self.machine.setInitialState(self.stopped)

        self.started.entered.connect(self.watson.start)
        self.started.assignProperty(self.start_action, 'enabled', False)
        self.started.assignProperty(self.stop_action, 'enabled', True)
        self.started.assignProperty(self, 'icon',
                                    QIcon(':/images/running.svg'))
        self.started.addTransition(self.stop_action.triggered, self.stopped)
        self.started.addTransition(self.clicked, self.stopped)
        self.started.addTransition(self.stop, self.stopped)

        self.stopped.entered.connect(self.watson.stop)
        self.stopped.assignProperty(self.start_action, 'enabled', True)
        self.stopped.assignProperty(self.stop_action, 'enabled', False)
        self.stopped.assignProperty(self, 'icon',
                                    QIcon(':/images/default.svg'))
        self.stopped.assignProperty(self, 'toolTip', "Watson")
        self.stopped.addTransition(self.start_action.triggered, self.started)
        self.stopped.addTransition(self.clicked, self.started)
        self.stopped.addTransition(self.start, self.started)

        self.activated.connect(self.on_activated)

        self.machine.start()
        self.show()

    @pyqtSlot(int)
    def on_activated(self, reason):
        if reason == self.Context:
            return
        self.clicked.emit()

    def quit(self):
        self.watson.stop()
        return app.quit()


def main():
    global app

    app = QApplication(sys.argv)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None, "Watson", "The system tray is not available."
        )
        sys.exit(1)

    QApplication.setQuitOnLastWindowClosed(False)

    SysTray()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
