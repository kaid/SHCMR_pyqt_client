# encoding=utf-8

import datetime
from PyQt4.QtGui import QSortFilterProxyModel
from PyQt4.QtSql import QSqlTableModel, QSqlQuery
from PyQt4.QtCore import Qt, QModelIndex, pyqtSignal, QObject, QFileInfo, QVariant
from env import DataStore, Configuration
from utils import *

set_unicode()

class FileTransferSortProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(FileTransferSortProxyModel, self).__init__(parent)
        self.setSourceModel(FileTransferTableModel())
        self.setDynamicSortFilter(True)
        self.__method_forward()

    def __method_forward(self):
        methods = ['global_speed', 'global_time_left', 'set_calculated_column',
                   'transfer_count', 'scan_files', 'sort_by_modified_at']

        for method in methods:
            setattr(self,
                    method,
                    getattr(self.sourceModel(), method))

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def lessThan(self, left_index, right_index):
        left = from_qvariant(self.sourceModel().raw_data(left_index))
        right = from_qvariant(self.sourceModel().raw_data(right_index))

        if (left == None or right == None): return True
        return left < right

class FileTransferTableModel(QSqlTableModel):
    __calculated_column_index = {'progress':7, 'speed':8}

    def __init__ (self, parent=None):
        super(FileTransferTableModel, self).__init__(parent)
        self.query = QSqlQuery()
        self.worker = Worker()
        self.setTable('file_list')
        self.setFilter('modified_at NOT NULL')
        self.select()
        DataStore.committed.connect(self.sort_by_modified_at)
        self.sort_by_modified_at()
        self.__columnCount = super(self.__class__, self).columnCount
        self.__calculated_columns = dict()
        for key in self.__class__.__calculated_column_index:
            self.__calculated_columns[key] = dict()

    def columnCount(self, parent=QModelIndex()):
        return self.__columnCount(parent) + len(self.__class__.__calculated_column_index)

    def data(self, index, role=Qt.DisplayRole):
        if Qt.DisplayRole == role:
            status = super(FileTransferTableModel, self).data(self.index(index.row(), 1))
            data = from_qvariant(self.raw_data(index))
            if 1 == index.column():
                return unicode_str('同步中' if status else '同步完毕')
            if 3 == index.column():
                return convert_byte_size(int(data))
            if 5 == index.column():
                return unicode_str('目录' if data else '文件')
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
            return unicode_str(['id', '状态', '文件名', '大小', '路径', '类型', '最近修改于', '进度', '速度'][section])

    def set_calculated_column(self, column, row, value):
        status = self.raw_data(self.index(row, 1))
        if not status:
            return False
        fid = from_qvariant(self.raw_data(self.index(row, 4)))
        index = self.index(row, self.__class__.__calculated_column_index[column])
        self.__calculated_columns[column][fid] = from_qvariant(value)
        self.dataChanged.emit(index, index)
        return True

    def raw_data(self, index, role=Qt.DisplayRole):
        if Qt.DisplayRole == role:
            fid = from_qvariant(super(FileTransferTableModel, self).data(self.index(index.row(), 4)))
            if 7 == index.column():
                return self.__calculated_columns['progress'].get(fid, 0)
            if 8 == index.column():
                return int(self.__calculated_columns['speed'].get(fid, 0))

        return super(FileTransferTableModel, self).data(index, role)

    def global_speed(self):
        return sum(self.__calculated_columns['speed'].values())

    def transfer_count(self):
        query = self.query
        query.exec_('SELECT SUM(status) FROM file_list')
        while query.next():
            return query.value(0)

    def time_left(self, row):
        fid = from_qvariant(self.raw_data(self.index(row, 4)))
        size = from_qvariant(self.raw_data(self.index(row, 3)))
        progress = self.__calculated_columns['progress'].get(fid, 0) / 100.0
        speed = self.__calculated_columns['speed'].get(fid, 0)
        if not speed:
            return -1
        return size * (1 - progress) / speed

    def global_time_left(self):
        time_left_collection = [self.time_left(row) for row in range(self.rowCount())]
        return sum(time_left_collection)

    def scan_files(self):
        self.worker.done.connect(lambda: DataStore.batch_insert(self.file_infos))
        self.worker.begin(self.__file_iteration, Configuration.get_directory())

    def __file_iteration(self, directory):
        self.file_infos = DirFileInfoList(directory).file_infos

    def sort_by_modified_at(self):
        self.sort(6, Qt.DescendingOrder)

    def get_meta_dict(self):
        query = self.query
        query.exec_('SELECT * FROM file_list WHERE modified_at NOT NULL')
        path_number, modified_at_number = query.record().indexOf('path'), query.record().indexOf('modified_at')
        meta_dict = {}
        while query.next():
            path, modified_at = from_qvariant(query.value(path_number)), query.value(modified_at_number)
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
