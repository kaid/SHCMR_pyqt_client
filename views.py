import random
from PyQt4.QtGui import (QMainWindow,
                         QTableView,
                         QStatusBar,
                         QLabel,
                         QPushButton,
                         QSystemTrayIcon,
                         QAction,
                         QIcon,
                         QMenu,
                         qApp)

from PyQt4.QtCore import QTimer, SIGNAL
from models import FileTransferSortProxyModel
from delegates import FileTransferDelegate
from utils import *

class MyWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setWindowTitle('文件传输详情')
        self.setCentralWidget(FileTransferTable(parent=self))
        self.__init_statusBar()

        # 界面调试按钮
        self.__debug_buttons()

    def __init_statusBar(self):
        self.setStatusBar(FileTransferStatusBar())
        timer = QTimer(self)
        model = self.centralWidget().model()
        status_bar = self.statusBar()
        self.connect(timer, SIGNAL('timeout()'), lambda param = model.global_speed : status_bar.set_global_speed(param()))
        self.connect(timer, SIGNAL('timeout()'), lambda param = model.global_time_left : status_bar.set_time_left(param()))
        self.connect(timer, SIGNAL('timeout()'), lambda param = model.transfer_count : status_bar.set_transfer_count(param()))
        timer.start(640)

    # 以下均为调试方法
    def __debug_buttons(self):
        status_bar = self.statusBar()
        status_bar.progress_button = QPushButton('进度')
        status_bar.speed_button = QPushButton('速度')
        status_bar.addWidget(status_bar.progress_button)
        status_bar.addWidget(status_bar.speed_button)
        status_bar.progress_button.clicked.connect(self.__random_progress)
        status_bar.speed_button.clicked.connect(self.__random_speed)

    def __random_progress(self):
        model = self.centralWidget().model()
        for row in range(model.rowCount()):
            model.set_calculated_column('progress', row, random.randint(0, 100))

    def __random_speed(self):
        model = self.centralWidget().model()
        for row in range(model.rowCount()):
            model.set_calculated_column('speed', row, random.randint(0, 9999999))

class FileTransferTable(QTableView):
    def __init__(self, parent=None):
        super(FileTransferTable, self).__init__(parent)
        self.resizeColumnsToContents()
        self.setModel(FileTransferSortProxyModel())
        self.setItemDelegate(FileTransferDelegate())
        self.setEditTriggers(self.NoEditTriggers)
        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(True)
        self.setColumnHidden(0, True)

class FileTransferStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super(FileTransferStatusBar, self).__init__(parent)
        self.set_transfer_count()
        self.set_time_left()
        self.set_global_speed()
        
    def set_transfer_count(self, count=0):
        self.__init_widget('file_transfer_count', QLabel())
        self.file_transfer_count.setText('同步%d个文件' % count)

    def set_time_left(self, seconds_left=-1):
        text = 0 > seconds_left and '无法估计' or format_time(seconds_left)
        self.__init_widget('time_left', QLabel())
        self.time_left.setText('剩余时间: %s' % text)

    def set_global_speed(self, byte_per_second=0.0):
        self.__init_widget('global_speed', QLabel())
        self.global_speed.setText('全局速度: %s' % convert_byte_size(byte_per_second) + '/s')

    def __init_widget(self, attr_name, widget):
        if not hasattr(self, attr_name):
            self.__dict__[attr_name] = widget
            self.addWidget(self.__dict__[attr_name])

class TrayIcon(QSystemTrayIcon):
    def __init__(self, app, parent=None):
        super(TrayIcon, self).__init__(parent)
        self.setIcon(QIcon('s.png'))
        self.setContextMenu(TrayMenu(app))
        
class TrayMenu(QMenu):
    def __init__(self, app, parent=None):
        super(TrayMenu, self).__init__(parent)
        self.app = app
        self.__setup_actions()

    def __setup_actions(self):
        self.addAction(QAction('&打开同步目录 ', self.app))
        self.recent_transfers = self.addMenu('&最近同步的文件 ')
        self.addSeparator()
        self.addAction(QAction('&退出 ', self.app, triggered=qApp.quit))

        self.recent_transfers.addAction(QAction('&larmageddon.jpg ', self.app))
