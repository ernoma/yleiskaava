
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QSettings

from qgis.core import (Qgis, QgsMessageLog)

import os.path

class YleiskaavaSettings:
    def __init__(self, iface, plugin_dir):
        self.iface = iface
        self.plugin_dir = plugin_dir

        self.dialogSettings = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_settings.ui'))


    def setupDialog(self):
        self.dialogSettings.checkBoxKeepDialogsOnTop.stateChanged.connect(self.handleCheckBoxKeepDialogsOnTopStateChanged)
        self.dialogSettings.pushButtonClose.clicked.connect(self.dialogSettings.hide)


    def openDialogSettings(self):
        self.readSettings()

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


    def handleCheckBoxKeepDialogsOnTopStateChanged(self):
        QgsMessageLog.logMessage('handleCheckBoxKeepDialogsOnTopStateChanged', 'Yleiskaava-työkalu', Qgis.Info)
        if self.dialogSettings.checkBoxKeepDialogsOnTop.isChecked():
            QSettings().setValue("/yleiskaava_tyokalu/keepDialogsOnTop", True)
        else:
            QSettings().setValue("/yleiskaava_tyokalu/keepDialogsOnTop", False)


    def shouldKeepDialogsOnTop(self):
        return QSettings().value("/yleiskaava_tyokalu/keepDialogsOnTop", True, type=bool)

