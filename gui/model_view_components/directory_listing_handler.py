import logging
from PyQt5 import QtCore
from gui.model_view_components.remote_filesystem_model import FileItem
from core.data_transfer_process import DataTransferProcess
from gui.model_view_components.data_container import DataContainer

__author__ = 'Галлям'


logger = logging.getLogger(__name__)


class DirectoryListingHandler(QtCore.QThread):
    complete = QtCore.pyqtSignal()

    def __init__(self, parent: FileItem, dt: DataTransferProcess=None):
        super().__init__()
        self.parent = parent
        if self.parent is None:
            raise Exception('No fetched item to associate with')

        self.data_transfer_process = DataTransferProcess() if dt is None else dt
        self.data_transfer_process.ready.connect(self.start)

    @staticmethod
    def create_data_container(line: str) -> DataContainer:
        args = line.split(";")
        filename = args[-1]
        properties = {}
        for kv in [arg.split("=") for arg in args[:-1]]:
            properties[kv[0]] = kv[1]
        properties['name'] = filename
        dir_model_item = DataContainer(**properties)
        return dir_model_item

    @QtCore.pyqtSlot()
    def run(self):
        logger.debug('directory listing handling')

        for line in self.data_transfer_process.read_lines():
            if line == b'':
                continue
            try:
                line = line.decode()
            except UnicodeDecodeError:
                continue
            dir_model_item = self.create_data_container(line)
            self.add_child(dir_model_item)
        self.sort()

        logger.debug('dirlist handled')
        self.data_transfer_process.ready.disconnect()
        self.data_transfer_process.deleteLater()
        self.complete.emit()

    @staticmethod
    def get_modified_date(item: DataContainer) -> QtCore.QDateTime:
        year = int(item.modify[:4])
        month = int(item.modify[4:6])
        day = int(item.modify[6:8])
        date = QtCore.QDate(year, month, day)
        hour = int(item.modify[8:10])
        minute = int(item.modify[10:12])
        second = int(item.modify[-2:])
        time = QtCore.QTime(hour, minute, second)
        date_time = QtCore.QDateTime(date, time)
        return date_time

    def add_child(self, item: DataContainer):
        if item.type == 'pdir' or item.type == 'cdir':
            return
        date_time = self.get_modified_date(item)
        is_dir = item.type == 'dir'
        file_path = self.parent.file_path + '/%s' % item.name[1:]
        item_to_add = FileItem(file_path,
                               is_dir,
                               self.parent,
                               item.size if not is_dir else 0,
                               date_time)
        self.parent.add_child(item_to_add)

    def sort(self):
        self.parent.children \
            .sort(key=lambda file_item:
        (file_item.type, file_item.file_name, file_item.size))
        for index in range(self.parent.child_count()):
            self.parent.children[index].row = index

    def __hash__(self):
        return hash(self.parent)


