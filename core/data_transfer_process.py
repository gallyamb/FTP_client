import random
import sys
import subprocess

__author__ = 'Галлям'

import socket
import logging

from PyQt5 import QtCore


logger = logging.getLogger(__name__)


def get_port_as_tuple(port):
    first = port >> 8
    second = port % 256
    return first, second


def find_available_port() -> int:
    min_port = 30000
    max_port = 40000
    if sys.platform == 'linux':
        command = 'netstat -an | grep tcp | grep %s'
    else:  # sys.platform == 'win32'
        command = 'netstat -an | find "TCP" | find "%s"'
    port = None
    while port is None:
        tmp_port = random.randint(min_port, max_port)
        try:
            subprocess.check_output(command % tmp_port, shell=True)
        except subprocess.CalledProcessError:
            port = tmp_port
    return port


class DataTransferProcess(QtCore.QObject):
    complete = QtCore.pyqtSignal([bytes], [bytes, str])
    ready = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, is_passive: bool=False):
        super().__init__()
        self.socket = socket.socket()
        self.is_passive = is_passive
        if is_passive:
            self.ip = '0.0.0.0'
            self.port = find_available_port()
            self.remote_socket = None
            logger.debug('IP: {0}'.format(self.ip))
            logger.debug('port: {0}'.format(self.port))
        else:
            logger.debug('in active mode')

    def read_lines(self) -> bytes:
        data = b''
        count = 2 ** 16
        tmp = self.socket.recv(count)
        while True:
            full = data + tmp
            lines = full.splitlines()[:-1] if tmp else full.splitlines()
            yield from lines
            data = full.splitlines()[-1]
            if not tmp:
                break
            tmp = self.socket.recv(count)

    @QtCore.pyqtSlot(tuple)
    def start_transfer(self, address: tuple):
        self.socket.connect(address)
        self.ready.emit()

    def upload(self):
        with open(self.filename, 'rb') as file:
            step = 2 ** 16
            pie = file.read(step)
            while pie:
                pie = file.read()
                self.socket.send(pie)

    def download(self):
        count = 2 ** 16
        tmp = self.socket.recv(count)
        while tmp:
            yield tmp
            tmp = self.socket.recv(count)
