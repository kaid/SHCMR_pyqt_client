# encoding=utf-8

import random
from PyQt4.QtGui import (QMainWindow,
                         QTableView,
                         QStatusBar,
                         QLabel,
                         QPushButton,
                         QSystemTrayIcon,
                         QDesktopServices,
                         QAbstractItemView,
                         QFileDialog,
                         QAction,
                         QIcon,
                         QMenu,
                         qApp)

from PyQt4.QtCore import QTimer, SIGNAL, QUrl, QThreadPool
from PyQt4.QtSql import QSqlQuery
from env import DataStore, Configuration
from models import *
from delegates import FileTransferDelegate
from utils import *

class MyWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setWindowTitle('文件传输详情')
        self.setCentralWidget(FileTransferTable())
        self.setWindowIcon(QIcon('s.png'))
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
        self.worker = Worker()
        status_bar = self.statusBar()
        status_bar.progress_button = QPushButton('进度')
        status_bar.speed_button = QPushButton('速度')
        status_bar.scan_button = QPushButton('扫描目录')
        status_bar.cleandb_button = QPushButton('清空文件列表')
        status_bar.addWidget(status_bar.scan_button)
        status_bar.addWidget(status_bar.progress_button)
        status_bar.addWidget(status_bar.speed_button)
        status_bar.addWidget(status_bar.cleandb_button)
        status_bar.progress_button.clicked.connect(self.__random_progress)
        status_bar.speed_button.clicked.connect(self.__random_speed)
        status_bar.scan_button.clicked.connect(self.__scan_files)
        status_bar.cleandb_button.clicked.connect(self.__cleandb)

    def __random_progress(self):
        model = self.centralWidget().model()
        for row in range(model.rowCount()):
            model.set_calculated_column('progress', row, random.randint(0, 100))

    def __random_speed(self):
        model = self.centralWidget().model()
        for row in range(model.rowCount()):
            model.set_calculated_column('speed', row, random.randint(0, 2000))

    def __scan_files(self):
        self.centralWidget().model().scan_files()

    def __cleandb(self):
        model = self.centralWidget().model().sourceModel()
        model.query.exec_('DELETE FROM file_list')
        model.select()

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
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

class FileTransferStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super(FileTransferStatusBar, self).__init__(parent)
        self.set_transfer_count()
        self.set_time_left()
        self.set_global_speed()
        self.init_config_button()
        self.init_config_dialog()

    def set_transfer_count(self, count=0):
        self.__init_widget('file_transfer_count', QLabel())
        self.file_transfer_count.setText('同步%d个文件' % (count or 0))

    def set_time_left(self, seconds_left=-1):
        text = 0 > seconds_left and '无法估计' or format_time(seconds_left)
        self.__init_widget('time_left', QLabel())
        self.time_left.setText('剩余时间: %s' % text)

    def set_global_speed(self, byte_per_second=0.0):
        self.__init_widget('global_speed', QLabel())
        self.global_speed.setText('全局速度: %s' % convert_byte_size(byte_per_second) + '/s')

    def init_config_button(self):
        self.__init_widget('config_button', QPushButton())
        self.config_button.setText('设置同步目录')
        self.config_button.clicked.connect(self.show_config_dialog)

    def init_config_dialog(self):
        self.config_dialog = QFileDialog()
        self.config_dialog.setFileMode(QFileDialog.Directory)
        self.config_dialog.setViewMode(QFileDialog.List)

    def show_config_dialog(self):
        self.config_dialog.show()
        if self.config_dialog.exec_():
            Configuration.set_directory(self.config_dialog.selectedFiles()[0])
            print('当前同步目录: %s' % Configuration.get_directory())

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
        self.open_directory_action = QAction('&打开同步目录 ', self.app)
        self.open_directory_action.triggered.connect(self.open_directory)
        Configuration.have_updated.connect(self.__toggle_open_directory_action)
        self.open_directory_action.setDisabled(not Configuration.get_directory())
        self.addAction(self.open_directory_action)
        self.recent_transfers = self.addMenu('&最近同步的文件 ')
        self.addSeparator()
        self.addAction(QAction('&退出 ', self.app, triggered=qApp.quit))
        self.recent_transfers.addAction(QAction('&larmageddon.jpg ', self.app))

    def open_directory(self):
        directory = Configuration.get_directory()
        QDesktopServices.openUrl(QUrl('file:///%s' % directory, QUrl.TolerantMode))

    def __toggle_open_directory_action(self):
        self.open_directory_action.setDisabled(not Configuration.get_directory())
