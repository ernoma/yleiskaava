
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QVariant

from qgis.core import (Qgis, QgsProject, QgsMessageLog)

import os.path


class AddSourceDataLinks:

    def __init__(self, iface, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = os.path.dirname(__file__)

        self.dialogAddSourceDataLinks = uic.loadUi(os.path.join(self.plugin_dir, 'yleiskaava_dialog_add_source_data_links.ui'))


    def setup(self):
        pass


    def openDialogAddSourceDataLinks(self):
        self.dialogAddSourceDataLinks.show()

