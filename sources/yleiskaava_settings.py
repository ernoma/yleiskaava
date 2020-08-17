
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QSettings

from qgis.core import (
    Qgis, QgsMessageLog,
    QgsAuthMethodConfig, QgsAuthManager,
    QgsApplication
)

import os.path

from .qaava.settings import parse_value, set_setting, get_setting
from .qaava.exceptions import QaavaDatabaseNotSetException, QaavaAuthConfigException

from .yleiskaava_database import YleiskaavaDatabase

class YleiskaavaSettings:

    PG_CONNECTIONS = "PostgreSQL/connections"

    def __init__(self, iface, plugin_dir, yleiskaavaDatabase):
        self.iface = iface
        self.plugin_dir = plugin_dir
        self.yleiskaavaDatabase = yleiskaavaDatabase

        self.dialogSettings = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_settings.ui'))


    def setupDialog(self):
        self.dialogSettings.checkBoxKeepDialogsOnTop.stateChanged.connect(self.handleCheckBoxKeepDialogsOnTopStateChanged)

        self.dialogSettings.pushButtonClose.clicked.connect(self.dialogSettings.hide)


    def openDialogSettings(self):
        try:
            self.dialogSettings.comboBoxUsedDBConnection.currentTextChanged.disconnect(self.handleComboBoxUsedDBConnectionCurrentTextChanged)
        except TypeError:
            pass
        except RuntimeError:
            pass

        self.readSettings()

        self.dialogSettings.comboBoxUsedDBConnection.currentTextChanged.connect(self.handleComboBoxUsedDBConnectionCurrentTextChanged)

        if self.shouldKeepDialogsOnTop():
            self.dialogSettings.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        else:
            self.dialogSettings.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)

        self.dialogSettings.show()


    def readSettings(self):
        if QSettings().value("/yleiskaava_tyokalu/keepDialogsOnTop", True, type=bool):
            self.dialogSettings.checkBoxKeepDialogsOnTop.setChecked(True)
        else:
            self.dialogSettings.checkBoxKeepDialogsOnTop.setChecked(False)

        self.setupDatabaseConnectionSettings()


    def setupDatabaseConnectionSettings(self):
        self.dialogSettings.comboBoxUsedDBConnection.clear()
        self.dialogSettings.comboBoxUsedDBConnection.addItem("")

        s = QSettings()
        s.beginGroup(YleiskaavaSettings.PG_CONNECTIONS)
        keys = s.allKeys()
        s.endGroup()
        connections = {key.split('/')[0] for key in keys if '/' in key}
        
        for conn in connections:
            # QgsMessageLog.logMessage('readSettings - connection: ' + conn, 'Yleiskaava-työkalu', Qgis.Info)
            self.dialogSettings.comboBoxUsedDBConnection.addItem(conn)

        usedDatabaseConnection = s.value("/yleiskaava_tyokalu/usedDatabaseConnection", "")

        QgsMessageLog.logMessage('setupDatabaseConnectionSettings - usedDatabaseConnection: ' + usedDatabaseConnection, 'Yleiskaava-työkalu', Qgis.Info)
        self.dialogSettings.comboBoxUsedDBConnection.setCurrentText(usedDatabaseConnection)


    def handleCheckBoxKeepDialogsOnTopStateChanged(self):
        # QgsMessageLog.logMessage('handleCheckBoxKeepDialogsOnTopStateChanged', 'Yleiskaava-työkalu', Qgis.Info)
        if self.dialogSettings.checkBoxKeepDialogsOnTop.isChecked():
            QSettings().setValue("/yleiskaava_tyokalu/keepDialogsOnTop", True)
        else:
            QSettings().setValue("/yleiskaava_tyokalu/keepDialogsOnTop", False)


    def shouldKeepDialogsOnTop(self):
        return QSettings().value("/yleiskaava_tyokalu/keepDialogsOnTop", True, type=bool)


    def handleComboBoxUsedDBConnectionCurrentTextChanged(self, connName):
        QSettings().setValue("/yleiskaava_tyokalu/usedDatabaseConnection", connName)

        databaseConnectionParams = None

        if connName != "":
            databaseConnectionParams = self. readDatabaseParamsFromSettings(connName)

        self.yleiskaavaDatabase.setDatabaseConnection(databaseConnectionParams)


    def readDatabaseParamsFromSettings(self, connName):
        settings = QSettings()
        settings.beginGroup(YleiskaavaSettings.PG_CONNECTIONS + "/" + connName)
        
        params = {}

        auth_cfg_id = parse_value(settings.value("authcfg"))
        username_saved = parse_value(settings.value("saveUsername"))
        pwd_saved = parse_value(settings.value("savePassword"))

        for qgs_key, psyc_key in YleiskaavaDatabase.QGS_SETTINGS_PSYCOPG2_PARAM_MAP.items():
            params[psyc_key] = parse_value(settings.value(qgs_key))

        settings.endGroup()
        # username or password might have to be asked separately
        if not username_saved:
            params["user"] = None

        if not pwd_saved:
            params["password"] = None

        if auth_cfg_id is not None and auth_cfg_id != "":
            # LOGGER.info(f"Auth cfg: {auth_cfg_id}")
            # Auth config is being used to store the username and password
            auth_config = QgsAuthMethodConfig()
            authMgr = QgsApplication.authManager()
            authMgr.loadAuthenticationConfig(auth_cfg_id, auth_config, True)

            if auth_config.isValid():
                params["user"] = auth_config.configMap().get("username")
                params["password"] = auth_config.configMap().get("password")
            else:
                raise QaavaAuthConfigException()

        # LOGGER.info(f"PR{params} {username_saved} {pwd_saved}")

        return params

