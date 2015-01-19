from queue import Queue
from threading import Thread
import logging
from time import sleep

from PyQt5 import QtCore
import core.data_transfer_process as dtp

from core.downloader import Downloader
from core.protocol_interpreter import ProtocolInterpreter
from gui.model_view_components.directory_listing_handler import \
    DirectoryListingHandler
from gui.model_view_components.remote_filesystem_model import FileItem
from switch_case import switch


logging.basicConfig(filename='log.txt', level=logging.DEBUG, filemode='w')
logger = logging.getLogger(__name__)

ftp_std_port = 21


class Core(QtCore.QObject):
    new_log = QtCore.pyqtSignal(str)
    already_connected = QtCore.pyqtSignal()
    hostname_not_specified = QtCore.pyqtSignal()
    update_local_model = QtCore.pyqtSignal()
    ready_to_read_dirlist = QtCore.pyqtSignal()
    update_remote_model = QtCore.pyqtSignal()

    download_file = QtCore.pyqtSignal(str, str, str)
    get_dirlist = QtCore.pyqtSignal(FileItem)

    def __init__(self):
        super().__init__()
        self.download_file.connect(self.start_file_downloading)
        self.get_dirlist.connect(self.get_directory_list)
        self.pi = ProtocolInterpreter(None, None)
        self.connected = False
        self._username = ""
        self._password = ""
        self._log = []
        self.active_mode = True
        self.dtp = None
        self.can_continue = True

        self.dlh_queue = Queue()
        self.download_queue = Queue()

        def queue_controller():
            while True:
                sleep(0.1)
                if self.can_continue and self.dtp is None:
                    if not self.dlh_queue.empty():
                        item = self.dlh_queue.get()
                    elif not self.download_queue.empty():
                        item = self.download_queue.get()
                    else:
                        continue
                    # getattr(self, item[0])(*item[1])
                    for case in switch(item[0]):
                        if case('down'):
                            self.download_file.emit(*item[1])
                            break
                        if case('up'):
                            break
                        if case('dir'):
                            self.get_dirlist.emit(*item[1])
                            break

        Thread(target=queue_controller, daemon=True).start()

    @QtCore.pyqtSlot()
    def on_log_read(self):
        del self._log[:]

    def read_log(self):
        return '\r\n'.join(self._log)

    def start_connecting(self, hostname, port, username, password):
        logger.debug('Core starting')

        if hostname == "":
            self.hostname_not_specified.emit()
            return
        if self.connected:
            self.already_connected.emit()
            return
        if port == "":
            port = ftp_std_port
        if username == "":
            username = "anonymous"

        self.pi = ProtocolInterpreter(hostname, port)
        self._connect_signals_to_slots()
        self._username = username
        self._password = password
        self.pi.start()
        self.connected = True
        logger.debug('Core started')

    @QtCore.pyqtSlot()
    def set_type_binary(self):
        self.pi.set_binary_type()

    def start_file_downloading(self, source_path: str, path_to_save: str,
                               filename: str):
        if not self.can_continue or self.dtp is not None:
            self.download_queue.put(('down',
                                     (source_path, path_to_save, filename)))
            return
        logger.debug('file %s downloading started. destination: %s' %
                     (filename, path_to_save))

        self.pi.change_dir(source_path)

        downloader = Downloader(path_to_save, filename)

        self.dtp = downloader
        self.pi.passive_mode.connect(downloader.data_transfer_process
                                     .start_transfer, QtCore.Qt.QueuedConnection)

        downloader.complete.connect(self.update_local_model)
        downloader.complete.connect(self.set_dtp_to_none)
        downloader.complete.connect(downloader.deleteLater)
        self.pi.initiate_passive_mode()
        self.pi.download_file(filename)

    def set_dtp_to_none(self):
        self.dtp = None

    @QtCore.pyqtSlot(FileItem)
    def get_directory_list(self, parent: FileItem):
        if not self.can_continue or self.dtp is not None:
            self.dlh_queue.put(('dir', (parent,)))
            return
        logger.debug('directory listing getting')

        path = parent.file_path
        logger.debug('path: %s' % path + '/')
        self.pi.change_dir(path)
        if self.active_mode:
            dlh = DirectoryListingHandler(parent)
            self.pi.passive_mode.connect(dlh.data_transfer_process
                                         .start_transfer)
        else:
            dt = dtp.DataTransferProcess(True)
            dlh = DirectoryListingHandler(parent, dt)
            self.pi.correct_command.connect(dt.start_transfer)
            dt.ready.connect(lambda: self.pi.correct_command
                             .disconnect(dt.start_transfer))

        self.dtp = dlh
        dlh.complete.connect(self.update_remote_model)
        dlh.complete.connect(self.set_dtp_to_none)
        dlh.complete.connect(dlh.deleteLater)

        if self.active_mode:
            self.pi.initiate_passive_mode()
            self.pi.get_dirlist_in_passive()
        else:
            # stub for passive mode
            self.pi.send_ip_and_port('127.0.0.1',
                                     dlh.data_transfer_process.port_as_tuple)

    def set_can_continue(self, can: bool):
        self.can_continue = can

    def _connect_signals_to_slots(self):
        logger.debug('Slots connecting')
        self.pi.username_required.connect(self._send_username)
        self.pi.password_required.connect(self._send_password)
        self.pi.buffer_changed.connect(self.print_log)
        #
        self.pi.user_authorised.connect(self.set_type_binary)
        # self.pi.user_authorised.connect(lambda: self.pi.push(b'MODE S\r\n'))
        self.pi.user_authorised.connect(self.ready_to_read_dirlist)

        self.pi.data_canal_opening.connect(lambda: self.set_can_continue(False))
        self.pi.canal_closing_success_transfer \
            .connect(lambda: self.set_can_continue(True))
        logger.debug('Slots connected')

    @QtCore.pyqtSlot(bool)
    def set_connected(self, is_connected):
        self.connected = is_connected

    @QtCore.pyqtSlot()
    def _send_username(self):
        logger.debug('Username sent')
        self.pi.send_username(self._username)

    @QtCore.pyqtSlot()
    def _send_password(self):
        logger.debug('Password sent')
        self.pi.send_password(self._password)

    @QtCore.pyqtSlot(list)
    def print_log(self, log: list):
        self._log.extend(log)
        self.new_log.emit(self.read_log())
