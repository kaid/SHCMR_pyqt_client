#!/usr/bin/env python
import sys
from PyQt4.QtGui import QIcon
from env import Configuration, App
from utils import *
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
    window = MyWindow()
    model = window.centralWidget().model().sourceModel()
    init_monitor( model)
    window.resize(800, 400)
    window.show()
    tray = TrayIcon(App)
    tray.show()
    App.exec_()
    tray = None
    sys.exit()

if __name__ == '__main__':
    main()
    

