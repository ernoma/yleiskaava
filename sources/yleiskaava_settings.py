
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QSettings

from qgis.core import (
    Qgis, QgsProject, QgsMessageLog,
    QgsAuthMethodConfig, QgsAuthManager,
    QgsApplication
)
from qgis.gui import QgsMessageBarItem

import os.path

from .qaava.settings import parse_value, set_setting, get_setting
from .qaava.exceptions import QaavaDatabaseNotSetException, QaavaAuthConfigException

from .yleiskaava_database import YleiskaavaDatabase

class YleiskaavaSettings:

    PG_CONNECTIONS = "PostgreSQL/connections"

    def __init__(self, iface, plugin_dir, yleiskaavaDatabase):
        self.iface = iface
        self.dockWidget = None
        self.plugin_dir = plugin_dir
        self.yleiskaavaDatabase = yleiskaavaDatabase

        self.dialogSettings = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_settings.ui'))

        self.openProjectMessageBarItem = None
        self.openDatabaseProjectMismatchMessageBarItem = None


    def setDockWidget(self, dockWidget):
        self.dockWidget = dockWidget


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

        settings = QSettings()
        settings.beginGroup(YleiskaavaSettings.PG_CONNECTIONS)
        keys = settings.allKeys()
        settings.endGroup()
        connections = sorted({key.split('/')[0] for key in keys if '/' in key})
        
        for conn in connections:
            # QgsMessageLog.logMessage('setupDatabaseConnectionSettings - connection: ' + conn, 'Yleiskaava-työkalu', Qgis.Info)
            self.dialogSettings.comboBoxUsedDBConnection.addItem(conn)

        self.readDatabaseConnectionSettings()


    def readDatabaseConnectionSettings(self):
        settings = QSettings()

        usedDatabaseConnectionName = settings.value("/yleiskaava_tyokalu/usedDatabaseConnection", "")

        QgsMessageLog.logMessage('readDatabaseConnectionSettings - usedDatabaseConnection: ' + usedDatabaseConnectionName, 'Yleiskaava-työkalu', Qgis.Info)
        self.dialogSettings.comboBoxUsedDBConnection.setCurrentText(usedDatabaseConnectionName)

        self.updateDatabaseConnection(usedDatabaseConnectionName)


    def handleCheckBoxKeepDialogsOnTopStateChanged(self):
        # QgsMessageLog.logMessage('handleCheckBoxKeepDialogsOnTopStateChanged', 'Yleiskaava-työkalu', Qgis.Info)
        if self.dialogSettings.checkBoxKeepDialogsOnTop.isChecked():
            QSettings().setValue("/yleiskaava_tyokalu/keepDialogsOnTop", True)
        else:
            QSettings().setValue("/yleiskaava_tyokalu/keepDialogsOnTop", False)


    def shouldKeepDialogsOnTop(self):
        return QSettings().value("/yleiskaava_tyokalu/keepDialogsOnTop", True, type=bool)


    def handleComboBoxUsedDBConnectionCurrentTextChanged(self, usedDatabaseConnectionName):
        QSettings().setValue("/yleiskaava_tyokalu/usedDatabaseConnection", usedDatabaseConnectionName)
        success = self.updateDatabaseConnection(usedDatabaseConnectionName)
        if success:
            if self.canUseBecauseDatabase():
                self.hideErrorDatabaseProjectMismatch()
                self.iface.messageBar().pushMessage('Tietokantaan yhdistäminen onnistui ja se vastaa QGIS-työtilaa', Qgis.Info, duration=20)
            else:
                self.showErrorDatabaseProjectMismatch()
        else:
            self.iface.messageBar().pushMessage('Tietokantaan yhdistäminen ei onnistunut', Qgis.Critical, duration=0)
            self.dockWidget.pushButtonSettings.setStyleSheet('QPushButton {background-color: red; color: #white;}')


    def updateDatabaseConnection(self, usedDatabaseConnectionName):
        databaseConnectionParams = None
        success = False

        if usedDatabaseConnectionName != "":
            databaseConnectionParams = self.readDatabaseParamsFromSettings(usedDatabaseConnectionName)

            success = self.yleiskaavaDatabase.setDatabaseConnection(databaseConnectionParams)
            self.yleiskaavaDatabase.monitorCachedLayerChanges()

        return success


    def readDatabaseParamsFromSettings(self, usedDatabaseConnectionName):
        settings = QSettings()
        settings.beginGroup(YleiskaavaSettings.PG_CONNECTIONS + "/" + usedDatabaseConnectionName)
        
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


    def canUseBecauseProject(self):
        if len(QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE)) != 1 or len(QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA)) != 1 or len(QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA)) != 1 or len(QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_PISTE)) != 1:
            return False
        
        return True


    def showErrorBecauseProjectNotRead(self):
        self.openProjectMessageBarItem = QgsMessageBarItem('Yleiskaavan QGIS-työtila pitää käynnistää ennen työkalujen käyttöä', Qgis.Warning, duration=10)
        self.iface.messageBar().pushItem(self.openProjectMessageBarItem)
        self.iface.projectRead.connect(self.handleProjectRead)


    def hideErrorBecauseProjectNotRead(self):
        try:
            self.iface.messageBar().popWidget(self.openProjectMessageBarItem)
            self.openProjectMessageBarItem = None
        except RuntimeError:
            self.openProjectMessageBarItem = None


    def canUseBecauseDatabase(self):
        self.readDatabaseConnectionSettings()
        layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE)[0]
        dataSourceUri = layer.dataProvider().dataSourceUri()
        # QgsMessageLog.logMessage('canUseBecauseDatabase - dataSourceUri: ' + dataSourceUri, 'Yleiskaava-työkalu', Qgis.Info)
        return self.yleiskaavaDatabase.databaseMatchesDataSourceUri(dataSourceUri)


    def showErrorDatabaseProjectMismatch(self):
        self.openDatabaseProjectMismatchMessageBarItem = QgsMessageBarItem('Valittu tietokanta ei vastaa työtilaa', Qgis.Warning, duration=0)
        self.iface.messageBar().pushItem(self.openDatabaseProjectMismatchMessageBarItem)
        self.dockWidget.pushButtonSettings.setStyleSheet('QPushButton {background-color: red; color: #white;}')


    def hideErrorDatabaseProjectMismatch(self):
        try:
            self.iface.messageBar().popWidget(self.openDatabaseProjectMismatchMessageBarItem)
            self.openDatabaseProjectMismatchMessageBarItem = None
        except RuntimeError:
            self.openDatabaseProjectMismatchMessageBarItem = None

        self.dockWidget.pushButtonSettings.setStyleSheet('QPushButton {background-color: #EAF7E8; color: black;}')


    def handleProjectRead(self):
        if self.canUseBecauseProject():
            self.hideErrorBecauseProjectNotRead()
            try:
                self.iface.projectRead.disconnect(self.handleProjectRead)
            except TypeError:
                pass
            except RuntimeError:
                pass
                        
        
        if not self.canUseBecauseDatabase():
            self.showErrorDatabaseProjectMismatch()