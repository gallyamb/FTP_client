from PyQt5 import QtWidgets, QtCore

__author__ = 'Галлям'

from .local_filesystem_model import LocalFileSystemModel


class FileSystemExplorer(QtWidgets.QTreeView):
    def __init__(self):
        super().__init__()
        model = LocalFileSystemModel(self)
        self.setModel(model)

        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        index = self.model().index("d:")
        self.expand(index)
        self.scrollTo(index)
        self.setCurrentIndex(index)
        self.resizeColumnToContents(0)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)

    def remove_error(self):
        warning_window = QtWidgets.QMessageBox()
        warning_window.setWindowTitle("Remove error")
        warning_window.setText("File can't be removed\r\n"
                               "It used by other process")
        warning_window.addButton(QtWidgets.QMessageBox.Ok)
        warning_window.resize(400, 200)
        warning_window.setIcon(QtWidgets.QMessageBox.Warning)
        warning_window.setWindowModality(QtCore.Qt.ApplicationModal)
        warning_window.exec_()

    def remove_item(self):
        indexes = self.selectedIndexes()
        for index in indexes:
            if index.column() != 0:
                continue
            if self.model().remove(index):
                pass
            else:
                self.remove_error()

    def contextMenuEvent(self, e):
        menu = QtWidgets.QMenu()

        delete_action = QtWidgets.QAction('&Delete', self)
        delete_action.triggered.connect(self.remove_item)

        menu.addAction(delete_action)
        menu.exec_(e.globalPos())
