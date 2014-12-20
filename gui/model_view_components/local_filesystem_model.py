__author__ = 'Галлям'

from PyQt5 import QtWidgets, QtCore


class LocalFileSystemModel(QtWidgets.QDirModel):
    file_downloading = QtCore.pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot
                       | QtCore.QDir.Drives | QtCore.QDir.Files)
        self.setSorting(QtCore.QDir.DirsFirst | QtCore.QDir.IgnoreCase |
                        QtCore.QDir.Name)
        self.setReadOnly(False)

    def dropMimeData(self, mime_data: QtCore.QMimeData,
                     drop_actions: QtCore.Qt.DropActions,
                     row: int, column: int,
                     index: QtCore.QModelIndex):
        if not index.isValid() or not drop_actions & QtCore.Qt.CopyAction:
            return False
        urls = mime_data.urls()
        target_path = self.filePath(index)
        for url in urls:
            self.file_downloading.emit(url.path(), target_path)
        return True

    def supportedDropActions(self) -> QtCore.Qt.DropActions:
        return QtCore.Qt.CopyAction

    def supportedDragActions(self) -> QtCore.Qt.DropActions:
        return QtCore.Qt.CopyAction


