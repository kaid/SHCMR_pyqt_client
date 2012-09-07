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
        status_bar.addWidget(status_bar.progress_button)
        status_bar.progress_button.clicked.connect(self.__plus_plus)

    def __plus_plus(self):
        model = self.centralWidget().model()
        for row in range(model.rowCount()):
            index = model.index(row, 4)
            #data = model.data(index)
            model.setData(index, random.randint(0, 100))

class FileTransferTable(QTableView):
    def __init__(self, parent=None):
        super(FileTransferTable, self).__init__(parent)
        self.resizeColumnsToContents()
        self.setModel(FileTransferSortProxyModel(FileTransferTableModel('file_list', self)))
        self.setItemDelegateForColumn(4, ProgressDelegate())
        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(True)
        self.setColumnHidden(0, True)

class FileTransferSortProxyModel(QSortFilterProxyModel):
    def __init__(self, source_model, parent=None):
        super(FileTransferSortProxyModel, self).__init__(parent)
        self.setSourceModel(source_model)
        self.sort(0)

    def lessThan(self, left_index, right_index):
        left_val = left_index.data()
        right_val = right_index.data()

        return left_val < right_val


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

class ProgressDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        value = index.data(Qt.DisplayRole)
        opts = QStyleOptionProgressBarV2()
        opts.rect = option.rect
        opts.minum = 0
        opts.maximum = 100
        opts.text = str(value)
        opts.textAlignment = Qt.AlignCenter
        opts.textVisible = True
        opts.progress = value

        QApplication.style().drawControl(QStyle.CE_ProgressBar, opts, painter)

class FileTransferTableModel(QSqlTableModel):
    def __init__ (self, table, parent=None):
        super(FileTransferTableModel, self).__init__(parent)
        self.setTable(table)
        self.select()
        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.__setData = super(FileTransferTableModel, self).setData
        self.__columnCount = super(FileTransferTableModel, self).columnCount
        self.__sort = super(FileTransferTableModel, self).sort
        self.raw_data = super(FileTransferTableModel, self).data
        self.insertColumns(4, 1)
        self.__progress_column = dict()

    def columnCount(self, parent):
        return self.__columnCount(parent) + 1

    def data(self, index, role=Qt.DisplayRole):
        if Qt.DisplayRole == role:
            if 1 == index.column():
                return self.raw_data(index) and '同步中' or '同步完毕'
            if 3 == index.column():
                return convert_byte_size(int(self.raw_data(index)))
            # if 5 == index.column():
            #     return convert_byte_size(int(self.rawData(index))) + '/s'
            if 4 == index.column():
                return self.__progress_column.get(self.get_row_id(index.row()), 0)

        return self.raw_data(index, role)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return ['id', '状态', '文件名', '大小', '进度', '速度', '所嘛'][section]

    def insertColumns(self, column, count, parent=QModelIndex()):
        return True

    def setData(self, index, value, role=Qt.DisplayRole):
        if index.column() == 4:
            self.__progress_column[self.get_row_id(index.row())] = value
            self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index)
            return True

        return self.__setData(index, value, role)

    def get_row_id(self, row):
        return self.raw_data(self.index(row, 0))


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

