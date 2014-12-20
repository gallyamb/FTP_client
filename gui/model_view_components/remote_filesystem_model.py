from PyQt5 import QtCore, QtWidgets, QtGui
from switch_case import switch
import logging

__author__ = 'Галлям'

logger = logging.getLogger('RFSM')


class FileItem:
    def __init__(self, file_path: str, is_dir: bool,
                 parent=None, size: int=0,
                 last_modified_date: QtCore.QDateTime=
                 QtCore.QDateTime.currentDateTime(),
                 row_in_parent: int=0):
        self.file_path = file_path

        file_name = ""
        if file_path:
            file_name = file_path.split('/')[-1]

        self.data = [file_name,
                     None if is_dir else size,
                     'dir' if is_dir else 'file',
                     last_modified_date]

        self.is_dir = is_dir
        self.parent = parent
        self.children = []
        self.fetched = True
        if is_dir and file_path:
            self.fetched = False
        self.row = row_in_parent

    @property
    def file_name(self):
        return self.data[0]

    @property
    def type(self):
        return self.data[2]

    @property
    def size(self):
        return "" if self.data[1] is None else self.data[1]

    def add_child(self, item):
        self.children.append(item)

    def child_count(self):
        return len(self.children)

    def __eq__(self, other) -> bool:
        return self.data == other.data and self.children == other.children \
               and self.file_path == other.file_path

    def __ne__(self, other) -> bool:
        return not self == other

    def __hash__(self):
        return (hash(self.file_path) << 5) & hash(self.file_name)


class RemoteFileSystemModel(QtCore.QAbstractItemModel):
    directory_listing_needed = QtCore.pyqtSignal(str)
    file_uploading = QtCore.pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.last_fetched_item = None

        self.root_item = FileItem("", True)

        self.read_dir(self.root_item)
        self.columnCount = 4

        iconProvider = QtWidgets.QFileIconProvider()
        self.file_icon = QtGui.QIcon('gui/model_view_components/file.png')
        self.folder_icon = iconProvider.icon(QtWidgets.
                                             QFileIconProvider.Folder)

    @QtCore.pyqtSlot(list)
    def handle_directory_list(self, directory_items: list):
        logger.debug('directory listing handling')
        if self.last_fetched_item is None:
            raise Exception('No fetched item to associate with')
        model_item = self.createIndex(self.last_fetched_item.row, 0,
                                      self.last_fetched_item)
        super().rowsAboutToBeInserted.emit(model_item,
                                           0, len(directory_items) - 1)
        for item in directory_items:
            if item.type == 'pdir' or item.type == 'cdir':
                continue
            year = int(item.modify[:4])
            month = int(item.modify[4:6])
            day = int(item.modify[6:8])
            date = QtCore.QDate(year, month, day)

            hour = int(item.modify[8:10])
            minute = int(item.modify[10:12])
            second = int(item.modify[-2:])
            time = QtCore.QTime(hour, minute, second)

            date_time = QtCore.QDateTime(date, time)
            item_to_add = FileItem(self.last_fetched_item.file_path +
                                   '/%s' % item.name[1:-1], item.type == 'dir',
                                   self.last_fetched_item,
                                   item.size if item.type != 'dir'
                                   else item.sizd,
                                   date_time)
            self.last_fetched_item.add_child(item_to_add)
        self.sort()
        super().rowsInserted.emit(model_item,
                                  0, len(directory_items) - 1)
        self.refresh()

    def sort(self, column: int=0, sort_order=None):
        self.last_fetched_item.children\
            .sort(key=lambda file_item:
                (file_item.type, file_item.file_name, file_item.size))
        for index in range(self.last_fetched_item.child_count()):
            self.last_fetched_item.children[index].row = index

    def read_dir(self, parent: FileItem) -> None:
        self.last_fetched_item = parent
        self.directory_listing_needed.emit(parent.file_path)

    def data(self, index: QtCore.QModelIndex,
             role: int=QtCore.Qt.DisplayRole) -> QtCore.QVariant:
        if not index.isValid():
            return QtCore.QVariant()

        if index.column() < 0 or index.column() >= self.columnCount:
            return QtCore.QVariant()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return self.item(index).data[index.column()]

        if index.column() == 0:
            for case in switch(role):
                if case(QtWidgets.QDirModel.FileIconRole):
                    return self.file_icon if not self.item(index).is_dir else \
                        self.folder_icon
                if case():
                    return QtCore.QVariant()

        return QtCore.QVariant()

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        flags = super().flags(index)
        if not index.isValid():
            return flags
        flags |= QtCore.Qt.ItemIsDragEnabled
        file_item = self.item(index)
        if index.column() == 0:
            flags |= QtCore.Qt.ItemIsEditable
            if file_item.is_dir:
                flags |= QtCore.Qt.ItemIsDropEnabled
        return flags

    def headerData(self, section: int,
                   orientation: QtCore.Qt.Orientation,
                   role: int=QtCore.Qt.DisplayRole) -> QtCore.QVariant:
        if orientation == QtCore.Qt.Horizontal and \
                        role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        for case in switch(section):
            if case(0):
                return self.tr('Name')
            if case(1):
                return self.tr('Size')
            if case(2):
                return self.tr('Type')
            if case(3):
                return self.tr('Date modified')
            if case():
                return QtCore.QVariant()

    def item(self, index: QtCore.QModelIndex) -> FileItem:
        return index.internalPointer() if index.isValid() else self.root_item

    def hasChildren(self, index: QtCore.QModelIndex=None,
                    *args, **kwargs) -> bool:
        if not self.item(index).fetched:
            return True

        return self.item(index).child_count() > 0

    def canFetchMore(self, index: QtCore.QModelIndex) -> bool:
        return not self.item(index).fetched

    def fetchMore(self, index: QtCore.QModelIndex) -> None:
        if index.isValid() and not self.item(index).fetched:
            self.read_dir(self.item(index))
            self.item(index).fetched = True
        self.refresh()

    def refresh(self):
        self.layoutChanged.emit()

    def columnCount(self, index: QtCore.QModelIndex=None,
                    *args, **kwargs) -> int:
        return self.columnCount

    def rowCount(self, index: QtCore.QModelIndex=None,
                 *args, **kwargs) -> int:
        if index.column() > 0:
            return 0

        return self.item(index).child_count()

    def index(self, row: int, column: int,
              parent: QtCore.QModelIndex=None,
              *args, **kwargs) -> QtCore.QModelIndex:
        item = self.item(parent)
        if row < 0 or row >= item.child_count() \
                or column < 0 or column >= self.columnCount:
            return QtCore.QModelIndex()
        return self.createIndex(row, column, item.children[row])

    def parent(self, index: QtCore.QModelIndex=None,
               *args, **kwargs) -> QtCore.QModelIndex:
        parent = self.item(index).parent

        if parent == self.root_item:
            return QtCore.QModelIndex()

        return self.createIndex(parent.row, 0, parent)

    def supportedDropActions(self) -> QtCore.Qt.DropActions:
        return QtCore.Qt.CopyAction

    def supportedDragActions(self) -> QtCore.Qt.DropActions:
        return QtCore.Qt.CopyAction

    def dropMimeData(self, mime_data: QtCore.QMimeData,
                     drop_actions: QtCore.Qt.DropActions,
                     row: int, column: int,
                     index: QtCore.QModelIndex) -> bool:
        if not index.isValid() or not drop_actions &\
                self.supportedDropActions():
            return False
        urls = mime_data.urls()

        for url in urls:
            self.file_uploading.emit(url.path()[1:], self.item(index).file_path)

        return True

    def mimeTypes(self) -> list:
        return ["text/uri-list"]

    def mimeData(self, indexes: list) -> QtCore.QMimeData:
        urls = []
        for index in indexes:
            if index.column() != 0:
                continue
            urls.append(QtCore.QUrl(self.item(index).file_path))
        data = QtCore.QMimeData()
        data.setUrls(urls)
        return data
