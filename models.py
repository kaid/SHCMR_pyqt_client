import datetime
from PyQt4.QtGui import QSortFilterProxyModel, QApplication
from PyQt4.QtSql import QSqlTableModel, QSqlQuery
from PyQt4.QtCore import Qt, QModelIndex, SIGNAL, QDir, pyqtSignal, QObject, QDirIterator, QFileInfo, QEventLoop, QFileSystemWatcher
from utils import *

class FileTransferSortProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(FileTransferSortProxyModel, self).__init__(parent)
        self.setSourceModel(FileTransferTableModel())
        self.__method_forward()
        self.sort(0)

    def lessThan(self, left_index, right_index):
        left = self.sourceModel().raw_data(left_index)
        right = self.sourceModel().raw_data(right_index)

        if (left == None or right == None): return True
        return left < right

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def __method_forward(self):
        self.global_speed = self.sourceModel().global_speed
        self.global_time_left = self.sourceModel().global_time_left
        self.set_calculated_column = self.sourceModel().set_calculated_column
        self.transfer_count = self.sourceModel().transfer_count
        self.scan_files = self.sourceModel().scan_files

class FileTransferTableModel(QSqlTableModel):
    __calculated_column_index = {'progress':7, 'speed':8}

    def __init__ (self, parent=None):
        super(FileTransferTableModel, self).__init__(parent)
        self.worker = Worker()
        self.setTable('file_list')
        self.select()
        self.__columnCount = super().columnCount
        self.__calculated_column = dict()
        self.query = QSqlQuery()
        for key in self.__class__.__calculated_column_index:
            self.__calculated_column[key] = dict()

    def columnCount(self, parent=QModelIndex()):
        return self.__columnCount(parent) + len(self.__class__.__calculated_column_index)

    def data(self, index, role=Qt.DisplayRole):
        if Qt.DisplayRole == role:
            status = super().data(self.index(index.row(), 1))
            data = self.raw_data(index)
            if 1 == index.column():
                return '同步中' if status else '同步完毕'
            if 3 == index.column():
                return convert_byte_size(int(data))
            if 5 == index.column():
                return '目录' if data else '文件'
            if 6 == index.column():
                if data < 0:
                    return
                return datetime.datetime.fromtimestamp(data).isoformat(' ')
            if 7 == index.column() and status:
                return data
            if 8 == index.column() and status:
                return convert_byte_size(int(data)) + '/s'

        return self.raw_data(index, role)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return ['id', '状态', '文件名', '大小', '路径', '类型', '最近修改于', '进度', '速度'][section]

    def set_calculated_column(self, column, row, value):
        status = self.raw_data(self.index(row, 1))
        if not status:
            return False
        fid = self.raw_data(self.index(row, 0))
        index = self.index(row, self.__class__.__calculated_column_index[column])
        self.__calculated_column[column][fid] = value
        self.dataChanged.emit(index, index)
        return True

    def raw_data(self, index, role=Qt.DisplayRole):
        if Qt.DisplayRole == role:
            fid = super().data(self.index(index.row(), 0))
            if 7 == index.column():
                return self.__calculated_column['progress'].get(fid, 0)
            if 8 == index.column():
                return int(self.__calculated_column['speed'].get(fid, 0))

        return super().data(index, role)

    def global_speed(self):
        return sum(self.__calculated_column['speed'].values())

    def transfer_count(self):
        query = self.query
        query.exec_('SELECT SUM(status) FROM file_list')
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

    def scan_files(self, directory):
        self.worker.done.connect(self.__batch_insert)
        self.worker.begin(self.__file_iteration, directory)

    def __file_iteration(self, directory):
        iterator = QDirIterator(directory, QDirIterator.Subdirectories)
        self.file_infos = []
        while iterator.hasNext():
            info = QFileInfo(iterator.next())
            if (info.fileName() != '.') and (info.fileName() != '..'):
                self.file_infos.append(info)

    def __batch_insert(self):
        for info in self.file_infos:
            QApplication.processEvents(QEventLoop.AllEvents)
            self.__insert_info(info)
        
        self.select()

    def __insert_info(self, info):
        query = self.query
        query.prepare('INSERT INTO file_list (name, size, path, is_dir, modified_at) VALUES (:name, :size, :path, :is_dir, :modified_at)')
        query.bindValue(':name', info.fileName())
        query.bindValue(':size', info.size())
        query.bindValue(':path', info.absoluteFilePath())
        query.bindValue(':is_dir', 1 if info.isDir() else 0)
        query.bindValue(':modified_at', -1 if info.isDir() else convert_time(info.lastModified()))
        query.exec_()


class Configuration(QObject):
    have_updated = pyqtSignal()

    def __init__(self, parent=None):
        super(Configuration, self).__init__()
        self.query = QSqlQuery()

    def set_directory(self, directory):
        self.query.prepare('UPDATE configuration SET directory=:directory WHERE id=1')
        self.query.bindValue(':directory', directory)
        self.query.exec_()
        self.have_updated.emit()

    def get_directory(self):
        self.query.exec_('SELECT directory FROM configuration WHERE id=1')
        while self.query.next():
            return self.query.value(0)
