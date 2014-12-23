from gui.model_view_components.remote_filesystem_model import FileItem

__author__ = 'Галлям'

from PyQt5 import QtWidgets, QtGui, QtCore
from core.core import Core
import gui.model_view_components.local_filesystem_view as local
import gui.model_view_components.remote_filesystem_view as remote


class MainWindow(QtWidgets.QMainWindow):
    text_read = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget=None):
        super().__init__(parent)
        self.actions = {}
        self.menus = {}
        self.edit_lines = {}
        self.buttons = {}
        self.layouts = {}
        self.widgets = {}

        self.core = Core()

        self.create_edit_lines()
        self.create_buttons()
        self.create_actions()

        self.create_menus()
        self.create_layouts()
        self.create_widgets()
        self.create_toolbars()

        self.setCentralWidget(self.widgets['central_widget'])

        self.connect_widgets_and_layouts()
        self.statusBar()
        self.connect_signals_to_slots()

    def connect_widgets_and_layouts(self):
        self.widgets['central_widget'].setLayout(self.layouts['main_layout'])
        self.widgets['conn_widget']. \
            setLayout(self.layouts['conn_toolbar_layout'])
        self.layouts['dir_models_layout']. \
            addWidget(self.widgets['local_filesystem'])
        self.layouts['dir_models_layout']. \
            addWidget(self.widgets['remote_filesystem'])
        self.layouts['main_layout']. \
            insertWidget(0, self.widgets['log_browser'])
        self.layouts['main_layout'].addLayout(self.layouts['dir_models_layout'])

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        menu.addAction(self.actions['exit_action'])
        menu.exec(event.globalPos())

    def create_menus(self):
        file_menu = self.menuBar().addMenu("&File")
        # file_menu.addAction(self.actions['new_action'])
        self.menus['file_menu'] = file_menu

        more_menu = file_menu.addMenu("&More")
        more_menu.addAction(self.actions['exit_action'])
        self.menus['more_menu'] = more_menu

    def create_actions(self):
        exit_action = QtWidgets.QAction("&Exit", self)
        exit_action.setShortcuts(QtGui.QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        self.actions['exit_action'] = exit_action

    def create_edit_lines(self):
        host_edit = QtWidgets.QLineEdit()
        host_edit.setFixedSize(150, 25)
        host_edit.setToolTip('Enter host name without protocol\r\n'
                             'FTP protocol only supported')
        self.edit_lines['host_edit'] = host_edit

        password_edit = QtWidgets.QLineEdit()
        password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        password_edit.setFixedSize(150, 25)
        password_edit.setToolTip('Enter password\r\n'
                                 'Password never be saved')
        self.edit_lines['password_edit'] = password_edit

        username_edit = QtWidgets.QLineEdit()
        username_edit.setPlaceholderText('anonymous')
        username_edit.setFixedSize(150, 25)
        username_edit.setToolTip('Enter username\r\n'
                                 'If skipped, '
                                 '"anonymous" username will be used')
        self.edit_lines['username_edit'] = username_edit

        port_edit = QtWidgets.QLineEdit()
        port_edit.setPlaceholderText('21')
        port_edit.setFixedSize(50, 25)
        port_edit.setValidator(QtGui.QIntValidator(0, 65536, port_edit))
        self.edit_lines['port_edit'] = port_edit

    def connect_remote_file_system(self):
        self.core.ready_to_read_dirlist. \
            connect(self.widgets['remote_filesystem']
                    .model()
                    .fetch_root)

        self.core.update_remote_model.connect(self.widgets['remote_filesystem']
                                              .model().refresh)

        self.widgets['remote_filesystem'] \
            .model() \
            .directory_listing_needed \
            .connect(self.core.get_directory_list)

        # self.widgets['remote_filesystem'] \
        #     .model() \
        #     .file_uploading \
        #     .connect(self.core.upload_file)

    def connect_signals_to_slots(self):
        self.buttons['conn_button'].clicked.connect(self.send_conn_info)
        for edit_line in self.edit_lines.values():
            edit_line.returnPressed. \
                connect(self.send_conn_info)
        self.core.already_connected.connect(self.on_already_connected)
        self.core.new_log.connect(self.widgets['log_browser'].append)

        self.connect_remote_file_system()

        self.widgets['local_filesystem'].model() \
            .file_downloading.connect(self.core.start_file_downloading)
        self.core.update_local_model.connect(self.widgets['local_filesystem']
                                             .model().refresh)

    def disconnect_old_remote_model(self):
        self.core.update_remote_model.disconnect()
        self.core.ready_to_read_dirlist.disconnect()

    def on_already_connected(self):
        warning_window = QtWidgets.QMessageBox()
        warning_window.setWindowTitle("Are you sure want to reconnect?")
        warning_window.setText("If you reconnect, all of your "
                               "connections and transfers "
                               "will be lost.\r\n"
                               "Do you want to continue?")
        yes_button = warning_window.addButton(QtWidgets.QMessageBox.Yes)
        warning_window.addButton(QtWidgets.QMessageBox.No)
        warning_window.setIcon(QtWidgets.QMessageBox.Warning)
        warning_window.setWindowModality(QtCore.Qt.ApplicationModal)
        warning_window.exec()

        if warning_window.clickedButton() == yes_button:
            self.core.set_connected(False)
            self.widgets['remote_filesystem'].reinitialise()
            self.disconnect_old_remote_model()
            self.connect_remote_file_system()
            self.send_conn_info()
        else:
            pass

    def send_conn_info(self) -> None:
        hostname = self.edit_lines['host_edit'].text()
        username = self.edit_lines['username_edit'].text()
        password = self.edit_lines['password_edit'].text()
        port = self.edit_lines['port_edit'].text()
        self.core.start_connecting(hostname, port, username, password)

    def create_buttons(self):
        conn_button = QtWidgets.QPushButton("Connect")

        def keyPressEvent(e):
            if e.key() == QtCore.Qt.Key_Enter or QtCore.Qt.Key_Return:
                conn_button.click()

        conn_button.keyPressEvent = keyPressEvent
        self.buttons['conn_button'] = conn_button

    def create_layouts(self):
        conn_toolbar_layout = QtWidgets.QHBoxLayout()
        conn_toolbar_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        host_form_layout = QtWidgets.QFormLayout()
        password_form_layout = QtWidgets.QFormLayout()
        username_form_layout = QtWidgets.QFormLayout()
        port_form_layout = QtWidgets.QFormLayout()

        host_form_layout.addRow('Host: ',
                                self.edit_lines['host_edit'])
        username_form_layout.addRow('Username: ',
                                    self.edit_lines['username_edit'])
        password_form_layout.addRow('Password: ',
                                    self.edit_lines['password_edit'])
        port_form_layout.addRow('Port: ',
                                self.edit_lines['port_edit'])

        conn_toolbar_layout.addLayout(host_form_layout)
        conn_toolbar_layout.addLayout(username_form_layout)
        conn_toolbar_layout.addLayout(password_form_layout)
        conn_toolbar_layout.addLayout(port_form_layout)
        conn_toolbar_layout.addWidget(self.buttons['conn_button'])
        self.layouts['conn_toolbar_layout'] = conn_toolbar_layout

        dir_models_layout = QtWidgets.QHBoxLayout()
        self.layouts['dir_models_layout'] = dir_models_layout

        main_layout = QtWidgets.QVBoxLayout()
        self.layouts['main_layout'] = main_layout

    def create_toolbars(self):
        def create_main_toolbar():
            main_toolbar = self.addToolBar('Main tools')

            main_toolbar.addAction(self.actions['exit_action'])
            main_toolbar.insertSeparator(self.actions['exit_action'])

            main_toolbar.setAllowedAreas(QtCore.Qt.TopToolBarArea)
            main_toolbar.setFloatable(False)
            main_toolbar.setMovable(False)
            self.addToolBarBreak()

        def create_connection_toolbar():
            connection_toolbar = self.addToolBar('Connection tools')
            connection_toolbar.addWidget(self.widgets['conn_widget'])
            connection_toolbar.setFloatable(False)
            connection_toolbar.setMovable(False)

        create_main_toolbar()
        create_connection_toolbar()

    def create_widgets(self):
        log_browser = QtWidgets.QTextEdit()
        log_browser.textChanged.connect(self.core.on_log_read)
        log_browser.setReadOnly(True)
        self.widgets['log_browser'] = log_browser

        local_filesystem = local.FileSystemExplorer()
        self.widgets['local_filesystem'] = local_filesystem

        remote_filesystem = remote.RemoteFileSystemExplorer()
        self.widgets['remote_filesystem'] = remote_filesystem

        conn_widget = QtWidgets.QWidget()
        self.widgets['conn_widget'] = conn_widget

        widget = QtWidgets.QWidget()
        self.widgets['central_widget'] = widget
