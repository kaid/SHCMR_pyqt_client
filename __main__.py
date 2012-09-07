#!/usr/bin/env python
import sys
import time
import random
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import *

file_transfer_list = [[True, '东方风神录.rar', 348127232, 90, 65740],
                      [True, '旅途之中.mp3', 4194304, 20, 32768],
                      [True, 'zurich.mp4', 9101244, 46, 12768],
                      [True, 'armageddon.jpg', 401244, 4, 4]]

def convert_byte_size(byte_size):
    for unit in ['bytes','KB','MB','GB','TB']:
        if byte_size < 1024.0:
            return "%3.1f%s" % (byte_size, unit)
        byte_size /= 1024.0

def convert_time(seconds):
    for unit in ['秒','分钟','小时']:
        if seconds < 60:
            return "%d%s" % (seconds, unit)
        seconds /= 60

def format_time(seconds):
    return time.strftime('%H小时%M分%S秒', time.gmtime(seconds))

class MyWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setWindowTitle('文件传输详情')
        self.setCentralWidget(FileTransferTable())
        self.__init_statusBar()

        # 界面调试按钮
        self.__debug_buttons()

    def __init_statusBar(self):
        self.setStatusBar(FileTransferStatusBar())

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
        self.setModel(FileTransferSortProxyModel(FileTransferTableModel('file_list', self)))
        self.setItemDelegate(FileTransferDelegate())
        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(True)
        self.setColumnHidden(0, True)

class FileTransferSortProxyModel(QSortFilterProxyModel):
    def __init__(self, source_model, parent=None):
        super(FileTransferSortProxyModel, self).__init__(parent)
        self.setSourceModel(source_model)
        self.sort(0)
        self.set_calculated_column = self.sourceModel().set_calculated_column

    def lessThan(self, left_index, right_index):
        return left_index.data() < right_index.data()

class FileTransferStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super(FileTransferStatusBar, self).__init__(parent)
        self.set_file_transfer_count()
        self.set_time_left()
        self.set_global_speed()
        
    def set_file_transfer_count(self, count=0):
        self.__init_widget('file_transfer_count', QLabel())
        self.file_transfer_count.setText('同步%d个文件' % count)

    def set_time_left(self, seconds_left=0):
        self.__init_widget('time_left', QLabel())
        self.time_left.setText('剩余时间: %s' % format_time(seconds_left))

    def set_global_speed(self, byte_per_second=0.0):
        self.__init_widget('global_speed', QLabel())
        self.global_speed.setText('%3.1f KB/s' % (byte_per_second / 1024))

    def __init_widget(self, attr_name, widget):
        if not hasattr(self, attr_name):
            self.__dict__[attr_name] = widget
            self.addWidget(self.__dict__[attr_name])

class FileTransferDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if 4 == index.column():
            value = index.data(Qt.DisplayRole)
            opts = QStyleOptionProgressBarV2()
            opts.rect = option.rect
            opts.minum = 0
            opts.maximum = 100
            opts.text = str(value) + '%'
            opts.textAlignment = Qt.AlignCenter
            opts.textVisible = True
            opts.progress = value
            QApplication.style().drawControl(QStyle.CE_ProgressBar, opts, painter)
        else:
            super().paint(painter, option, index)

class FileTransferTableModel(QSqlTableModel):
    __calculated_column_index = {'progress':4, 'speed':5}

    def __init__ (self, table, parent=None):
        super(FileTransferTableModel, self).__init__(parent)
        self.setTable(table)
        self.select()
        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.__columnCount = super().columnCount
        self.raw_data = super().data
        self.insertColumns(4, 2)
        self.__calculated_column = dict()
        for key in self.__class__.__calculated_column_index:
            self.__calculated_column[key] = dict()

    def columnCount(self, parent):
        return self.__columnCount(parent) + len(self.__class__.__calculated_column_index)

    def data(self, index, role=Qt.DisplayRole):
        if Qt.DisplayRole == role:
            if 1 == index.column():
                return self.raw_data(index) and '同步中' or '同步完毕'
            if 3 == index.column():
                return convert_byte_size(int(self.raw_data(index)))
            if 4 == index.column():
                return self.__calculated_column['progress'].get(index.row(), 0)
            if 5 == index.column():
                return convert_byte_size(int(self.__calculated_column['speed'].get(index.row(), 0))) + '/s'

        return self.raw_data(index, role)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return ['id', '状态', '文件名', '大小', '进度', '速度', '所嘛'][section]

    def insertColumns(self, column, count, parent=QModelIndex()):
        return True

    def set_calculated_column(self, column, row, value):
        index = self.index(row, self.__class__.__calculated_column_index[column])
        self.__calculated_column[column][row] = value
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index)
        return True

if __name__ == '__main__':
    app = QApplication(sys.argv)
    db=QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName("database.db")
    db.open()
    q=QSqlQuery()
    q.exec_('CREATE TABLE IF NOT EXISTS file_list(\
               id     INTEGER PRIMARY KEY AUTOINCREMENT,\
               status BOOL DEFAULT 0 CHECK (status = 0 OR status = 1),\
               name   VARCHAR(255) NOT NULL,\
               size   INT CHECK (size > 0)\
             )')
    q.exec_('INSERT INTO file_list (id, status, name, size) VALUES(1, 1, \'东方风神录.rar\', 348127232)')
    q.exec_('INSERT INTO file_list (id, status, name, size) VALUES(2, 1, \'旅途之中.mp3\', 4194304)')
    q.exec_('INSERT INTO file_list (id, status, name, size) VALUES(3, 1, \'zurich.mp4\', 9101244)')
    q.exec_('INSERT INTO file_list (id, status, name, size) VALUES(4, 1, \'armageddon.jpg\', 401244)')
    q.exec_('commit')

    window = MyWindow()
    window.resize(640, 240)
    window.show()
    sys.exit(app.exec_())

