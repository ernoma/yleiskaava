

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QVariant

from qgis.core import (Qgis, QgsProject, QgsMessageLog)

import os.path


class UpdateThemesOfGroup:

    def __init__(self, iface, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = os.path.dirname(__file__)

        self.dialogUpdateThemesOfGroup = uic.loadUi(os.path.join(self.plugin_dir, 'yleiskaava_dialog_update_themes_of_group.ui'))


    def setup(self):
        pass


    def openDialogUpdateThemeForGroup(self):
        self.dialogUpdateThemesOfGroup.show()

        

