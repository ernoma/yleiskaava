
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QVariant, QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import QLabel, QPushButton

from qgis.core import (Qgis, QgsProject, QgsMessageLog)

import os.path
from operator import itemgetter
from functools import partial

from .yleiskaava_source_data_apis import YleiskaavaSourceDataAPIs


class AddSourceDataLinks:

    FIELD_USER_FRIENDLY_NAME_INDEX = 0
    INFO_LINK_INDEX = 1
    LINKED_FEATURE_INDEX = 2
    LINK_TO_FEATURE_INDEX = 3

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


    def openDialogAddSourceDataLinks(self):
        self.dialogAddSourceDataLinks.show()


    def setupTableWidgetSourceTargetMatches(self):
        
        # TODO Kun käyttäjä valitsee lähdetason, niin lisää taulukkoon
        #  * painike kohteen kaikkien tietojen katsomiseen dialogista,
        #  * painike kohdesivun avaamiseen ja
        #  * perustiedot sekä
        #  * painike kohdetason kohteen valintaan
        # ? miten jo tietokannassa ko. rajapinnan kohteet huomioidaan?
        #   - voisi olla taulukossa jokin täppä, joka kertoo, että on jo tietokannassa eli
        #     kuitenkin samaan taulukkoon rajapinnalta jo tuodut tiedot ja tuomattomat tiedot
        #     -> itseasiassa kohde-tieto kertoo onko jo tietokannassa
        # TODO tuotujen tietojen osalta olisi hyvä olla päivitys mahdollisuus

        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.clearContents()
        # self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setRowCount(self.getSourceTargetMatchRowCount())
        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setColumnCount(4)
        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setHorizontalHeaderLabels([
            "Lähdenimi / tunniste",
            #"Lähdetietoikkuna",
            "Lähdetietosivu",
            "Yhdistetty kohde",
            "Yhdistä kohteeseen"#,
            #"Tiedot päivitettävissä"
        ])

        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.resizeColumnsToContents()


    def handleComboBoxChooseSourceDataLayerIndexChanged(self, index):
        if index > 0:

            text = self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.itemText(index)
            title, name = self.getLayerTitleAndNameFromComboBoxText(text)

            apiIndex = self.dialogAddSourceDataLinks.comboBoxChooseSourceDataAPI.currentIndex() - 1
            apiID = self.apis[apiIndex]["id"]
            QgsMessageLog.logMessage('handleComboBoxChooseSourceDataLayerIndexChanged, apiID: ' + str(apiID) + ', name: ' + name, 'Yleiskaava-työkalu', Qgis.Info)
            layer, layerInfo = self.yleiskaavaSourceDataAPIs.getLayerAndLayerInfo(apiID, name)

            # TODO listaa kohteen nimi ja painikkeet, tms. taulukossa
            # TODO listaa myös jo tietokannassa olevat kohteet
            if layer is None:
                self.iface.messageBar().pushMessage('Lähdekarttason kohteiden hakeminen ei onnistunut', Qgis.Critical)
            else:
                fields = layer.fields()
                for field in fields:
                    QgsMessageLog.logMessage('handleComboBoxChooseSourceDataLayerIndexChanged, field.name(): ' + str(field.name()) + ', name: ' + name, 'Yleiskaava-työkalu', Qgis.Info)

                QgsMessageLog.logMessage('handleComboBoxChooseSourceDataLayerIndexChanged, layer.featureCount(): ' + str(layer.featureCount()), 'Yleiskaava-työkalu', Qgis.Info)

                featureCount = 0
                for index, feature in enumerate(layer.getFeatures()):
                    featureCount += 1 # layer.featureCount() ei luotettava
                self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setRowCount(featureCount)

                for index, feature in enumerate(layer.getFeatures()):
                    # TODO lähdeaineiston mukaan nimi/tunniste UI:hin
                    QgsMessageLog.logMessage('handleComboBoxChooseSourceDataLayerIndexChanged, feature_user_friendly_identifier_field: ' + str(feature[layerInfo["feature_user_friendly_identifier_field"]]) + ', feature_info_url_field: ' + feature[layerInfo["feature_info_url_field"]], 'Yleiskaava-työkalu', Qgis.Info)

                    userFriendlyFieldNameLabel = QLabel(str(feature[layerInfo["feature_user_friendly_identifier_field"]]))

                    infoLinkButton = QPushButton()
                    infoLinkButton.setText("Näytä lähdetietosivu")
                    infoLinkButton.clicked.connect(partial(self.showInfoPage, feature[layerInfo["feature_info_url_field"]]))

                    linkedFeatureWidget = None
                    # TODO yhdistä tietokannan data
                    linkedFeature = self.yleiskaavaSourceDataAPIs.getLinkedDatabaseFeature(feature)
                    if linkedFeature != None:
                        linkedFeatureWidget = QPushButton()
                        linkedFeatureWidget.setText("Näytä yhdistetty kohde")
                    else:
                        linkedFeatureWidget = QLabel()
                        linkedFeatureWidget.setText("-")

                    linkToFeatureButton = QPushButton()
                    linkToFeatureButton.setText("Yhdistä")
                    # linkToFeatureButton.clicked.connect(partial(self.showInfoPage, feature[layerInfo["feature_info_url_field"]]))

                    self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setCellWidget(index, AddSourceDataLinks.FIELD_USER_FRIENDLY_NAME_INDEX, userFriendlyFieldNameLabel)
                    self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setCellWidget(index, AddSourceDataLinks.INFO_LINK_INDEX, infoLinkButton)
                    self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setCellWidget(index, AddSourceDataLinks.LINKED_FEATURE_INDEX, linkedFeatureWidget)
                    self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setCellWidget(index, AddSourceDataLinks.LINK_TO_FEATURE_INDEX, linkToFeatureButton)

                self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.resizeColumnsToContents()


    def showInfoPage(self, infoPageURL):
        QDesktopServices.openUrl(QUrl(infoPageURL))


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
            comboBoxTexts.insert(0, 'Valitse')
            self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.clear()
            self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.addItems(comboBoxTexts)


    def getLayerTitleNameComboBoxText(self, availableLayerName, availableLayerTitle):
        return '' + availableLayerTitle + ' (' + availableLayerName + ')'


    def getLayerTitleAndNameFromComboBoxText(self, text):
        # QgsMessageLog.logMessage('getLayerTitleAndNameFromComboBoxText, text: ' + str(text), 'Yleiskaava-työkalu', Qgis.Info)
        title, namePart = text.rsplit(' (', 1)
        name = namePart[0:-1]
        return title, name
