
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QVariant, QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import QLabel, QPushButton

from qgis.core import (Qgis, QgsProject, QgsMessageLog,
    QgsGeometry, QgsCoordinateTransform, QgsFeatureRequest, QgsRectangle)

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

        self.selectedTargetLayer = None
        self.apis = None


    def setup(self):
        # lisää kohdekarttatasot comboboksiin
        targetTableNames = sorted(self.yleiskaavaDatabase.getAllTargetSchemaTableNamesShownInCopySourceToTargetUI())
        targetTableNames.insert(0, "Valitse kohdekarttataso")
        self.dialogAddSourceDataLinks.comboBoxChooseTargetLayer.addItems(targetTableNames)
        self.dialogAddSourceDataLinks.comboBoxChooseTargetLayer.currentIndexChanged.connect(self.handleComboBoxChooseTargetLayerIndexChanged)

        self.dialogAddSourceDataLinks.pushButtonChooseFeatures.clicked.connect(self.handlePushButtonChooseFeatureClicked)

        self.apis = sorted(self.yleiskaavaSourceDataAPIs.getSourceDataAPIs(), key=itemgetter('name'))
        names = [api['name'] for api in self.apis]
        names.insert(0, "Valitse rajapinta")
        self.dialogAddSourceDataLinks.comboBoxChooseSourceDataAPI.addItems(names)
        self.dialogAddSourceDataLinks.comboBoxChooseSourceDataAPI.currentIndexChanged.connect(self.handleComboBoxChooseSourceDataAPIIndexChanged)

        self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.currentIndexChanged.connect(self.handleComboBoxChooseSourceDataLayerIndexChanged)

        self.dialogAddSourceDataLinks.spinBoxMaxSearchDistance.valueChanged.connect(self.handleSpinBoxMaxSearchDistanceChanged)

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
        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.clearContents()

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

                if self.selectedTargetLayer.selectedFeatureCount() > 0:
                    featureRequest = self.createFeatureRequestForSelectedFeatures(layer.crs())
                    if featureRequest != None:

                        featureCount = 0
                        for index, feature in enumerate(layer.getFeatures(featureRequest)):
                            featureCount += 1 # layer.featureCount() ei luotettava
                        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setRowCount(featureCount)
                        QgsMessageLog.logMessage('handleComboBoxChooseSourceDataLayerIndexChanged - featureCount: ' + str(featureCount), 'Yleiskaava-työkalu', Qgis.Info)

                        if featureCount == 0:
                            self.iface.messageBar().pushMessage('Lähdeaineistokarttatasolta ei löytynyt valittuista kohteista määritetyn rajaussuorakulmion sisältä kohteita', Qgis.Info, 10)

                        for index, feature in enumerate(layer.getFeatures(featureRequest)):
                            # TODO lähdeaineiston mukaan nimi/tunniste UI:hin
                            QgsMessageLog.logMessage('handleComboBoxChooseSourceDataLayerIndexChanged, feature_user_friendly_identifier_field: ' + str(feature[layerInfo["feature_user_friendly_identifier_field"]]) + ', feature_info_url_field: ' + feature[layerInfo["feature_info_url_field"]], 'Yleiskaava-työkalu', Qgis.Info)
                            

                            userFriendlyFieldNameLabel = QLabel(str(feature[layerInfo["feature_user_friendly_identifier_field"]]))

                            infoLinkButton = QPushButton()
                            infoLinkButton.setText("Näytä lähdetietosivu")
                            infoLinkButton.clicked.connect(partial(self.showInfoPage, feature[layerInfo["feature_info_url_field"]]))

                            linkedFeatureWidget = None
                            # TODO yhdistä tietokannan data
                            linkedFeature, linkData = self.yleiskaavaSourceDataAPIs.getLinkedDatabaseFeature(feature)
                            if linkedFeature != None:
                                linkedFeatureWidget = QPushButton()
                                linkedFeatureWidget.setText("Näytä yhdistetty kohde")
                                linkedFeatureWidget.clicked.connect(partial(self.showLinkedFeature, linkedFeature, linkData))
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


    def showLinkedFeature(self, linkedFeature, linkData):
        pass


    def handleComboBoxChooseTargetLayerIndexChanged(self, index):
        if self.selectedTargetLayer is not None:
            try:
                self.selectedTargetLayer.selectionChanged.disconnect(self.handleFeatureSelectionChanged)
            except TypeError:
                pass
            except RuntimeError:
                pass
        if index == 0:
            self.dialogAddSourceDataLinks.pushButtonChooseFeatures.setEnabled(False)
            self.selectedTargetLayer = None
        else:
            self.dialogAddSourceDataLinks.pushButtonChooseFeatures.setEnabled(True)

            userFriendlyTableName = self.dialogAddSourceDataLinks.comboBoxChooseTargetLayer.currentText()
            self.selectedTargetLayer = QgsProject.instance().mapLayersByName(userFriendlyTableName)[0]
            if self.selectedTargetLayer.selectedFeatureCount() > 0:
                self.iface.messageBar().pushMessage('' + userFriendlyTableName + ' karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
            self.selectedTargetLayer.selectionChanged.connect(self.handleFeatureSelectionChanged)


    def handlePushButtonChooseFeatureClicked(self):
        self.iface.showAttributeTable(self.selectedTargetLayer)


    def handleFeatureSelectionChanged(self):
        index = self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.currentIndex()
        self.handleComboBoxChooseSourceDataLayerIndexChanged(index)


    def handleSpinBoxMaxSearchDistanceChanged(self, value):
        index = self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.currentIndex()
        self.handleComboBoxChooseSourceDataLayerIndexChanged(index)


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

    def createFeatureRequestForSelectedFeatures(self, CRS):
        featureRequest = None

        transform = None
        selectedTargetLayerCRS = self.selectedTargetLayer.crs()
        if CRS != selectedTargetLayerCRS:
            transform = QgsCoordinateTransform(selectedTargetLayerCRS, CRS, QgsProject.instance())
        

        features = self.selectedTargetLayer.selectedFeatures()

        maxSearchDistance = self.dialogAddSourceDataLinks.spinBoxMaxSearchDistance.value()
        
        xMin = None
        yMin = None
        xMax = None
        yMax = None

        for feature in features:
            geom = feature.geometry()

            if not geom.isNull():
                transformedSourceGeom = None
                if transform is not None:
                    transformedGeom = QgsGeometry(geom)
                    transformedGeom.transform(transform)
                else:
                    transformedGeom = QgsGeometry(geom)

                bufferGeom = transformedGeom.buffer(maxSearchDistance,5)
                bbox = bufferGeom.boundingBox()
                if xMin is None or bbox.xMinimum() < xMin:
                    xMin = bbox.xMinimum()
                if yMin is None or bbox.yMinimum() < yMin:
                    yMin = bbox.yMinimum()
                if xMax is None or bbox.xMaximum() > xMax:
                    xMax = bbox.xMaximum()
                if yMax is None or bbox.yMaximum() < yMax:
                    yMax = bbox.yMaximum()

        QgsMessageLog.logMessage('createFeatureRequestForSelectedFeatures - xMin: ' + str(xMin) + ", yMin: " + str(yMin) + ", yMin: " + str(xMax) + ", yMax: " + str(yMax), 'Yleiskaava-työkalu', Qgis.Info)

        if xMin is not None and yMin is not None and xMax is not None and yMax is not None:
            bboxAllFeatures = QgsRectangle(xMin, yMin, xMax, yMax)
            featureRequest = QgsFeatureRequest(bboxAllFeatures)

        return featureRequest