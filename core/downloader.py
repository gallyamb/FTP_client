import os
from PyQt5 import QtCore
import sys
from core.data_transfer_process import DataTransferProcess

__author__ = 'root'


class Downloader(QtCore.QThread):
    complete = QtCore.pyqtSignal()

    def __init__(self, path_to_save: str, filename: str,
                 dt: DataTransferProcess=None):
        super().__init__()
        self.path_to_save = path_to_save
        self.filename = filename

        self.data_transfer_process = DataTransferProcess() if dt is None else dt
        self.data_transfer_process.ready.connect(self.start)

    def run(self):
        if not os.path.exists(self.path_to_save):
            os.makedirs(self.path_to_save)
        with open(self.path_to_save + '/' + self.filename, 'wb') as file:
            for data in self.data_transfer_process.download():
                file.write(data)
        self.data_transfer_process.ready.disconnect()
        self.data_transfer_process.deleteLater()
        self.complete.emit()