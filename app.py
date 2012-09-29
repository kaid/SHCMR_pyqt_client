#!/usr/bin/env python
import sys
from utils import *
from PyQt4.QtGui import QApplication, QIcon
from models import Configuration
from views import MyWindow, FileTransferStatusBar, TrayIcon
from fsmonitor import FSMonitor

def init_monitor(model):
    monitor = FSMonitor()
    directory = Configuration.get_directory()
    if directory:
        monitor.watch(directory)
    Configuration.have_updated.connect(lambda:monitor.watch(Configuration.get_directory()))
    monitor.start()

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
    

