#!/usr/bin/env python
import sys
from utils import *
from PyQt4.QtGui import QApplication, QIcon
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
from models import Configuration
from views import MyWindow, FileTransferStatusBar, TrayIcon

def init_monitor(model):
    monitor = FSMonitor()
    directory = Configuration.get_directory()
    if directory:
        monitor.watch(directory)
    Configuration.have_updated.connect(lambda:monitor.watch(directory))
    monitor.scanned.connect(model.merge_changes)

def main():
    app = QApplication(sys.argv)
    window = MyWindow()
    model = window.centralWidget().model().sourceModel()
    init_monitor( model)
    window.resize(800, 400)
    window.show()
    tray = TrayIcon(app, parent=app)
    tray.show()
    app.exec_()
    tray = None
    sys.exit()

if __name__ == '__main__':
    main()


