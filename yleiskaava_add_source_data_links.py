
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QVariant

from qgis.core import (Qgis, QgsProject, QgsMessageLog)

import os.path
from operator import itemgetter

from .yleiskaava_source_data_apis import YleiskaavaSourceDataAPIs


class AddSourceDataLinks:

    def __init__(self, iface, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.yleiskaavaSourceDataAPIs = YleiskaavaSourceDataAPIs(iface, yleiskaavaDatabase, yleiskaavaUtils)

        self.plugin_dir = os.path.dirname(__file__)

        self.dialogAddSourceDataLinks = uic.loadUi(os.path.join(self.plugin_dir, 'yleiskaava_dialog_add_source_data_links.ui'))

        self.apis = None


    def setup(self):
        # lisää kohdekarttatasot comboboksiin
        targetTableNames = sorted(self.yleiskaavaDatabase.getAllTargetSchemaTableNamesShownInCopySourceToTargetUI())
        targetTableNames.insert(0, "Valitse kohdekarttataso")
        self.dialogAddSourceDataLinks.comboBoxChooseTargetLayer.addItems(targetTableNames)
        self.dialogAddSourceDataLinks.comboBoxChooseTargetLayer.currentIndexChanged.connect(self.handleComboBoxChooseTargetLayerIndexChanged)

        self.apis = sorted(self.yleiskaavaSourceDataAPIs.getSourceDataAPIs(), key=itemgetter('name'))
        names = [api['name'] for api in self.apis]
        names.insert(0, "Valitse rajapinta")
        self.dialogAddSourceDataLinks.comboBoxChooseSourceDataAPI.addItems(names)
        self.dialogAddSourceDataLinks.comboBoxChooseSourceDataAPI.currentIndexChanged.connect(self.handleComboBoxChooseSourceDataAPIIndexChanged)

        self.dialogAddSourceDataLinks.pushButtonCancel.clicked.connect(self.dialogAddSourceDataLinks.hide)


    def openDialogAddSourceDataLinks(self):
        self.dialogAddSourceDataLinks.show()


    def handleComboBoxChooseTargetLayerIndexChanged(self, index):
        if index == 0:
            self.dialogAddSourceDataLinks.pushButtonChooseFeatures.setEnabled(False)
        else:
            self.dialogAddSourceDataLinks.pushButtonChooseFeatures.setEnabled(True)


    def handleComboBoxChooseSourceDataAPIIndexChanged(self, index):
        if index == 0:
            pass
        else:
            availableLayerNames, availableLayerTtitles = self.yleiskaavaSourceDataAPIs.getSourceDataAPILayerNamesAndTitles(self.apis[index - 1]['id'])
