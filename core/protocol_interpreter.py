__author__ = 'Галлям'

import logging
import asyncore

from PyQt5 import QtCore

from .import asynchat_patched


logger = logging.getLogger(__name__)


class ProtocolInterpreter(QtCore.QThread, asynchat_patched.AsyncChat):

    wait_until_next_command = QtCore.pyqtSignal()                       # 100
    data_canal_opened_transfer_started = QtCore.pyqtSignal()            # 125
    data_canal_opening = QtCore.pyqtSignal()                            # 150

    correct_command = QtCore.pyqtSignal()                               # 200
    unsupported_command = QtCore.pyqtSignal()                           # 202
    username_required = QtCore.pyqtSignal()                             # 220
    quit_success = QtCore.pyqtSignal()                                  # 221
    canal_opened_but_no_transfer = QtCore.pyqtSignal()                  # 225
    canal_closing_success_transfer = QtCore.pyqtSignal()                # 226
    passive_mode = QtCore.pyqtSignal(tuple)                             # 227
    user_authorised = QtCore.pyqtSignal()                               # 230
    wait_until_file_downloaded = QtCore.pyqtSignal()                    # 232
    request_succeeded = QtCore.pyqtSignal()                             # 250
    path_created = QtCore.pyqtSignal()                                  # 257

    password_required = QtCore.pyqtSignal()                             # 331
    authentication_required = QtCore.pyqtSignal()                       # 332
    requested_action_require_more_info = QtCore.pyqtSignal()            # 350

    server_not_found = QtCore.pyqtSignal()                              # 404
    impossible_procedure_canal_closing = QtCore.pyqtSignal()            # 421
    cannot_open_transfer_canal = QtCore.pyqtSignal()                    # 425
    canal_closed_transfer_cancelled = QtCore.pyqtSignal()               # 426
    host_unavailable = QtCore.pyqtSignal()                              # 434
    file_unavailable = QtCore.pyqtSignal()                              # 450
    local_error_operation_cancelled = QtCore.pyqtSignal()               # 451
    not_enough_space = QtCore.pyqtSignal()                              # 452

    syntax_error = QtCore.pyqtSignal()                                  # 500
    syntax_error_wrong_argument = QtCore.pyqtSignal()                   # 501
    unused_command = QtCore.pyqtSignal()                                # 502
    wrong_command_sequence = QtCore.pyqtSignal()                        # 503
    not_appropriate_command_and_argument = QtCore.pyqtSignal()          # 504
    logging_in_failed = QtCore.pyqtSignal()                             # 530
    authentication_required_for_file_saving = QtCore.pyqtSignal()       # 532
    file_not_found = QtCore.pyqtSignal()                                # 550

    buffer_changed = QtCore.pyqtSignal(list)

    def __init__(self, host, port):
        super(QtCore.QThread, self).__init__()
        super(asynchat_patched.AsyncChat, self).__init__()
        self.create_socket()
        self.set_reuse_addr()
        self.host = host
        self.port = port
        self.set_terminator(b'\r\n')
        self._buffer = []
        self._ftp_codes = {
            '100': self.wait_until_next_command.emit,
            '110': None,
            '120': None,
            '125': self.data_canal_opened_transfer_started.emit,
            '150': self.data_canal_opening.emit,
            '200': self.correct_command.emit,
            '202': self.unsupported_command.emit,
            '211': None,
            '212': None,
            '213': None,
            '214': None,
            '215': None,
            '220': self.username_required.emit,
            '221': self.quit_success.emit,
            '225': self.canal_opened_but_no_transfer.emit,
            '226': self.canal_closing_success_transfer.emit,
            '227': self.handle_passive_mode_entering,
            '228': None,
            '229': None,
            '230': self.user_authorised.emit,
            '231': None,
            '232': self.wait_until_file_downloaded.emit,
            '250': self.request_succeeded.emit,
            '257': self.path_created.emit,
            '331': self.password_required.emit,
            '332': self.authentication_required.emit,
            '350': self.requested_action_require_more_info.emit,
            '404': self.server_not_found.emit,
            '421': self.impossible_procedure_canal_closing.emit,
            '425': self.cannot_open_transfer_canal.emit,
            '426': self.canal_closed_transfer_cancelled.emit,
            '434': self.host_unavailable.emit,
            '450': self.file_unavailable.emit,
            '451': self.local_error_operation_cancelled.emit,
            '452': self.not_enough_space.emit,
            '500': self.syntax_error.emit,
            '501': self.syntax_error_wrong_argument.emit,
            '502': self.unused_command.emit,
            '503': self.wrong_command_sequence.emit,
            '504': self.not_appropriate_command_and_argument.emit,
            '530': self.logging_in_failed.emit,
            '532': self.authentication_required_for_file_saving.emit,
            '550': self.file_not_found.emit,
            '551': None,
            '552': None,
            '553': None,
        }

    def run(self):
        self.connect((self.host, self.port))
        asyncore.loop()

    def collect_incoming_data(self, data):
        self._collect_incoming_data(data)

    def found_terminator(self):
        received_message = self._get_data().decode()
        self._buffer.append(received_message)
        if received_message[3] == '-' or received_message[0] == " ":
            return
        self.buffer_changed.emit(self._buffer.copy())
        self._ftp_codes[received_message[:3]]()
        del self._buffer[:]

    def readable(self):
        return True

    def handle_connect(self):
        pass

    def send_username(self, username: str='anonymous'):
        username_request = bytes(('USER %s\r\n' % username), 'utf8')
        self.push(username_request)

    def send_password(self, password: str):
        password_request = bytes(('PASS %s\r\n' % password), 'utf8')
        self.push(password_request)

    def handle_passive_mode_entering(self):  # 227
        in_brackets = False
        result = ""
        for i in self._buffer[0]:
            if i == '(':
                in_brackets = True
                continue
            if i == ")":
                break
            if in_brackets:
                result += i
        result = result.split(',')
        ip = '.'.join(result[:4])
        port = int(result[4]) * 256 + int(result[5])
        self.passive_mode[tuple].emit((ip, port))

    def get_current_dir(self):
        self.push(b'PWD\r\n')

    def push(self, data: bytes):
        super().push(data)
        if data[:4] == b'PASS':
            self.buffer_changed.emit(['PASS *********'])
        else:
            self.buffer_changed.emit([data.decode()[:-2]])

    def send_ip_and_port(self, ip: str, port: tuple):
        ip = ip.split('.')
        logger.debug('port: {0}'.format(port))
        port = (str(x) for x in port)
        port_msg = bytes(("PORT " + ','.join(ip) + ','
                          + ','.join(port) + '\r\n').
                         encode())
        logger.debug(port_msg)
        self.push(port_msg)

    def initiate_passive_mode(self):
        self.push(b'PASV\r\n')

    def get_dirlist_in_passive(self):
        self.push(b'MLSD\r\n')

    def set_binary_type(self):
        self.push(b'TYPE I\r\n')

    def change_dir(self, path: str):
        self.push(b'CWD ' + path.encode() + b'/\r\n')

    def download_file(self, filename: str):
        self.push(b'RETR ' + filename.encode() + b'\r\n')
