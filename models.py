# encoding=utf-8

import datetime
from PyQt4.QtGui import QSortFilterProxyModel, QApplication
from PyQt4.QtSql import QSqlTableModel, QSqlQuery
from PyQt4.QtCore import Qt, QModelIndex, SIGNAL, pyqtSignal, QObject, QEventLoop, QFileInfo
from env import DataStore, Configuration
from utils import *

class FileTransferSortProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(FileTransferSortProxyModel, self).__init__(parent)
        self.setSourceModel(FileTransferTableModel())
        self.sort(6, Qt.DescendingOrder)
        self.setDynamicSortFilter(True)
        self.__method_forward()

    def __method_forward(self):
        self.global_speed = self.sourceModel().global_speed
        self.global_time_left = self.sourceModel().global_time_left
        self.set_calculated_column = self.sourceModel().set_calculated_column
        self.transfer_count = self.sourceModel().transfer_count
        self.scan_files = self.sourceModel().scan_files

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def lessThan(self, left_index, right_index):
        left = self.sourceModel().raw_data(left_index)
        right = self.sourceModel().raw_data(right_index)

        if (left == None or right == None): return True
        return left < right

class FileTransferTableModel(QSqlTableModel):
    __calculated_column_index = {'progress':7, 'speed':8}

    def __init__ (self, parent=None):
        super(FileTransferTableModel, self).__init__(parent)
        self.query = QSqlQuery()
        self.worker = Worker()
        self.setTable('file_list')
        DataStore.committed.connect(self.__sort_by_modified_at)
        self.setFilter('modified_at NOT NULL')
        self.select()
        self.__sort_by_modified_at()
        self.__columnCount = super(self.__class__, self).columnCount
        self.__calculated_column = dict()
        for key in self.__class__.__calculated_column_index:
            self.__calculated_column[key] = dict()

    def __init_monitor(self):
        self.monitor = FSMonitor()


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

    def record_count(self):
        query = self.query
        query.exec_('SELECT COUNT(*) FROM file_list')
        if query.next():
            return query.value(0)

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

    def scan_files(self):
        self.worker.done.connect(lambda: DataStore.batch_insert(self.file_infos))
        self.worker.begin(self.__file_iteration, Configuration.get_directory())

    def __file_iteration(self, directory):
        self.file_infos = DirFileInfoList(directory).file_infos

    def __sort_by_modified_at(self):
        self.sort(6, Qt.DescendingOrder)

    def get_meta_dict(self):
        query = self.query
        query.exec_('SELECT * FROM file_list WHERE modified_at NOT NULL')
        path_number, modified_at_number = query.record().indexOf('path'), query.record().indexOf('modified_at')
        meta_dict = {}
        while query.next():
            path, modified_at = query.value(path_number), query.value(modified_at_number)
            meta_dict[path] = modified_at
        return meta_dict

    def merge_changes(self, new_meta_dict):
        differ = DictDiffer(new_meta_dict, self.get_meta_dict())
        removed_files = list(differ.removed())
        added_files = [QFileInfo(path) for path in differ.added()]
        modified_files = [QFileInfo(path) for path in differ.changed()]

        print('>>>>>>> records gonna be changed: ', differ.changed())
        print('>>>>>>> records gonna be deleted: ', differ.removed())
        print('>>>>>>> records gonna be added: ',   differ.added())

        DataStore.batch_delete(removed_files)
        DataStore.batch_update(modified_files)
        DataStore.batch_insert(added_files)

        self.__sort_by_modified_at()


