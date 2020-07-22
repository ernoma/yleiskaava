
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

        self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.currentIndexChanged.connect(self.handleComboBoxChooseSourceDataLayerIndexChanged)

        self.dialogAddSourceDataLinks.pushButtonCancel.clicked.connect(self.dialogAddSourceDataLinks.hide)

        self.setupTableWidgetSourceTargetMatches()


    def setupTableWidgetSourceTargetMatches(self):
        
        # TODO Kun käyttäjä valitsee lähdetason, niin lisää taulukkoon
        #  * painike kohteen kaikkien tietojen katsomiseen dialogista,
        #  * painike kohdesivun avaamiseen ja
        #  * perustiedot sekä
        #  * painike kohdetason kohteen valintaan
        # ? miten jo tietokannassa ko. rajapinnan kohteet huomioidaan?

        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.clearContents()
        # self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setRowCount(self.getSourceTargetMatchRowCount())
        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setColumnCount(4)
        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setHorizontalHeaderLabels([
            "Lähdenimi / tunniste",
            "Lähdetietoikkuna",
            "Lähdetietosivu",
            "Kohde"
        ])


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
            availableLayerNames, availableLayerTitles = self.yleiskaavaSourceDataAPIs.getSourceDataAPILayerNamesAndTitles(self.apis[index - 1]['id'])
            comboBoxTexts = []
            for index, availableLayerName in enumerate(availableLayerNames):
                text = self.getLayerTitleNameComboBoxText(availableLayerName, availableLayerTitles[index])
                comboBoxTexts.append(text)
            self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.addItems(comboBoxTexts)


    def getLayerTitleNameComboBoxText(self, availableLayerName, availableLayerTitle):
        return '' + availableLayerTitle + ' (' + availableLayerName + ')'


    def getLayerTitleAndNameFromComboBoxText(self, text):
        # QgsMessageLog.logMessage('getLayerTitleAndNameFromComboBoxText, text: ' + str(text), 'Yleiskaava-työkalu', Qgis.Info)
        title, namePart = text.rsplit(' (', 1)
        name = namePart[0:-1]
        return title, name


    def handleComboBoxChooseSourceDataLayerIndexChanged(self, index):
        apiIndex = self.dialogAddSourceDataLinks.comboBoxChooseSourceDataAPI.currentIndex() - 1

        if apiIndex > 0:

            text = self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.itemText(index)
            title, name = self.getLayerTitleAndNameFromComboBoxText(text)

            apiID = self.apis[apiIndex]["id"]

            features = self.yleiskaavaSourceDataAPIs.getFeatures(apiID, name)

            # TODO listaa kohteen nimi ja painikkeet, tms. taulukossa
            