from PyQt4.QtGui import QSortFilterProxyModel
from PyQt4.QtSql import QSqlTableModel, QSqlQuery
from PyQt4.QtCore import Qt, QModelIndex, SIGNAL, QDir
from utils import *

class FileTransferSortProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(FileTransferSortProxyModel, self).__init__(parent)
        self.setSourceModel(FileTransferTableModel())
        self.sort(0)
        self.set_calculated_column = self.sourceModel().set_calculated_column
        self.global_speed = self.sourceModel().global_speed
        self.global_time_left = self.sourceModel().global_time_left
        self.transfer_count = self.sourceModel().transfer_count

    def lessThan(self, left_index, right_index):
        if not (left_index.data() and right_index.data()): return False
        return left_index.data() < right_index.data()

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

class FileTransferTableModel(QSqlTableModel):
    __calculated_column_index = {'progress':4, 'speed':5}

    def __init__ (self, parent=None):
        super(FileTransferTableModel, self).__init__(parent)
        self.setTable('file_list')
        self.select()
        self.__columnCount = super().columnCount
        self.raw_data = super().data
        self.__calculated_column = dict()
        for key in self.__class__.__calculated_column_index:
            self.__calculated_column[key] = dict()

    def columnCount(self, parent):
        return self.__columnCount(parent) + len(self.__class__.__calculated_column_index)

    def data(self, index, role=Qt.DisplayRole):
        if Qt.DisplayRole == role:
            status = self.raw_data(self.index(index.row(), 1))
            fid = self.raw_data(self.index(index.row(), 0))

            if 1 == index.column():
                return status and '同步中' or '同步完毕'
            if 3 == index.column():
                return convert_byte_size(int(self.raw_data(index)))
            if 4 == index.column() and status:
                return self.__calculated_column['progress'].get(fid, 0)
            if 5 == index.column() and status:
                return convert_byte_size(int(self.__calculated_column['speed'].get(fid, 0))) + '/s'

        return self.raw_data(index, role)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return ['id', '状态', '文件名', '大小', '进度', '速度'][section]

    def set_calculated_column(self, column, row, value):
        status = self.raw_data(self.index(row, 1))
        if not status:
            return False
        fid = self.raw_data(self.index(row, 0))
        index = self.index(row, self.__class__.__calculated_column_index[column])
        self.__calculated_column[column][fid] = value
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index)
        return True

    def global_speed(self):
        return sum(self.__calculated_column['speed'].values())

    def transfer_count(self):
        query = QSqlQuery('SELECT SUM(status) FROM file_list')
        while query.next():
            return query.value(0)

    def total_size(self):
        query = QSqlQuery('SELECT SUM(size) FROM file_list')
        while query.next():
            return query.value(0)

    def time_left(self, row):
        fid = self.raw_data(self.index(row, 0))
        size = self.raw_data(self.index(row, 3))
        progress = 1 - (self.__calculated_column['progress'].get(fid, 0) / 100)
        speed = self.__calculated_column['speed'].get(fid, 0)
        if not speed:
            return -1
        return size * progress / speed

    def global_time_left(self):
        time_left_collection = [self.time_left(row) for row in range(self.rowCount())]
        return sum(time_left_collection)

class Configuration:
    def __init__(self):
        self.query = QSqlQuery()
        if not self.get_directory():
            self.set_directory(QDir.homePath())

    def set_directory(self, directory):
        self.query.prepare('UPDATE configuration SET directory=:directory WHERE id=1')
        self.query.bindValue(':directory', directory)
        self.query.exec_()

    def get_directory(self):
        self.query.exec_('SELECT directory FROM configuration WHERE id=1')
        while self.query.next():
            return self.query.value(0)
