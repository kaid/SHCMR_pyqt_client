from PyQt4.QtGui import QStyledItemDelegate, QStyleOptionProgressBarV2, QApplication, QStyle
from PyQt4.QtCore import Qt

class FileTransferDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if 4 == index.column():
            value = index.data(Qt.DisplayRole)
            if value != None:
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

