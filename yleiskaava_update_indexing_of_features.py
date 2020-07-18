

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QVariant

from qgis.core import (Qgis, QgsProject, QgsMessageLog)

import os.path


class UpdateIndexingOfFeatures:

    def __init__(self, iface, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = os.path.dirname(__file__)

        self.dialogUpdateIndexingOfFeatures = uic.loadUi(os.path.join(self.plugin_dir, 'yleiskaava_dialog_update_indexing_of_features.ui'))


    def setup(self):
        pass


    def openDialogUpdateIndexingOfFeatures(self):
        self.dialogUpdateIndexingOfFeatures.show()

        

