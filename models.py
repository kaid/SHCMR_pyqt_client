# encoding=utf-8

from PyQt4.QtGui import QSortFilterProxyModel
from PyQt4.QtSql import QSqlTableModel, QSqlQuery, QSqlRecord
from PyQt4.QtCore import Qt, QModelIndex, pyqtSignal, QObject, QFileInfo, QVariant
from env import DataStore, Configuration
from utils import *

set_unicode()

class FileTransferSortProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(FileTransferSortProxyModel, self).__init__(parent)
        self.setSourceModel(FileTransferTableModel())
        self.setDynamicSortFilter(True)
        self.setFilterFixedString('0')
        self.setFilterKeyColumn(7)
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
    __calculated_column_keys = {'progress':8, 'speed':9}

    def __init__ (self, parent=None):
        super(FileTransferTableModel, self).__init__(parent)
        self.query = QSqlQuery()
        self.worker = Worker()
        self.setTable('file_list')
        self.setFilter('removed=0')
        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.select()
        self.sort_by_modified_at()
        self.__init_slots()
        self.__init_calculated_column()

    def __init_slots(self):
        DataStore.batch_done.connect(self.select)
        DataStore.inserting.connect(self.begin_insert)
        DataStore.inserted.connect(self.end_insert)
        DataStore.updating.connect(self.begin_update)
        DataStore.updated.connect(self.end_update)
        DataStore.deleted.connect(self.end_delete)
        DataStore.moved.connect(self.end_move)

    def __init_calculated_column(self):
        self.__columnCount = super(self.__class__, self).columnCount
        self.__calculated_columns = dict()
        for key in self.__class__.__calculated_column_keys:
            self.__calculated_columns[key] = dict()

    def columnCount(self, parent=QModelIndex()):
        return self.__columnCount(parent) + len(self.__class__.__calculated_column_keys)

    def data(self, index, role=Qt.DisplayRole):
        if Qt.DisplayRole == role:
            status = from_qvariant(self.raw_data(self.index(index.row(), 1)))
            data = from_qvariant(self.raw_data(index))
            if data == None or data == '': return
            return {
                1 : lambda source: unicode_str('同步中' if status else '同步完毕'),
                3 : lambda source: convert_byte_size(int(source)),
                5 : lambda source: unicode_str('目录' if source else '文件'),
                6 : lambda source: format_date(source),
                8 : lambda source: source,
                9 : lambda source: convert_byte_size(int(source)) + '/s'
            }.get(index.column(), lambda source: source)(data)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            header = ['id', '状态', '文件名', '大小', '路径', '类型',
                      '最近修改于', '已删除', '进度', '速度'][section]
            return unicode_str(header)

    def row_from(self, path):
        result = self.match(self.index(0, 4), Qt.DisplayRole, path)
        return result[0].row() if 0 < len(result) else None

    def begin_insert(self):
        self.insertRows(self.rowCount(), 1)

    def end_insert(self, data):
        self.set_row(self.rowCount() - 1, data)

    def begin_update(self, data):
        row = self.rowCount()
        self.insertRows(row, 1)
        self.set_row(row, data)
            
    def end_update(self, data):
        self.set_row(self.row_from(data[4]), data)

    def end_delete(self, data):
        self.set_row(self.row_from(data[4]), data)

    def end_move(self, old_path, new_data):
        self.set_row(self.row_from(old_path), new_data)

    def set_row(self, row, data):
        for column in range(8):
            self.setData(self.index(row, column),
                         from_qvariant(data[column]))

    def __remove_blank_rows(self):
        pass

    def set_calculated_column(self, key, row, value):
        status = self.raw_data(self.index(row, 1))
        if not status:
            return False
        path = from_qvariant(self.raw_data(self.index(row, 4)))
        index = self.index(row, self.__class__.__calculated_column_keys[key])
        self.__calculated_columns[key][path] = from_qvariant(value)
        self.dataChanged.emit(index, index)
        return True

    def raw_data(self, index, role=Qt.DisplayRole):
        if Qt.DisplayRole == role:
            fid = from_qvariant(super(FileTransferTableModel, self).data(self.index(index.row(), 4)))
            if 8 == index.column():
                return self.__calculated_columns['progress'].get(fid, 0)
            if 9 == index.column():
                return int(self.__calculated_columns['speed'].get(fid, 0))

        return super(FileTransferTableModel, self).data(index, role)

    def global_speed(self):
        return sum(self.__calculated_columns['speed'].values())

    def transfer_count(self):
        self.query.exec_('SELECT COUNT(*) FROM file_list WHERE (removed=0)')
        while self.query.next():
            return self.query.value(0)

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
