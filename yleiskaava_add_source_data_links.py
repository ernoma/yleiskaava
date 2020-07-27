
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QVariant, QUrl, QDateTime
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

    def reset(self):

        self.setupTableWidgetSourceTargetMatches()

        self.dialogAddSourceDataLinks.comboBoxChooseTargetLayer.setCurrentIndex(0)
        self.dialogAddSourceDataLinks.comboBoxChooseSourceDataAPI.setCurrentIndex(0)
        self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.setCurrentIndex(0)

        self.dialogAddSourceDataLinks.pushButtonChooseFeatures.setEnabled(False)

        self.selectedTargetLayer = None
        # self.apis = None


    def openDialogAddSourceDataLinks(self):
        self.reset()
        self.dialogAddSourceDataLinks.show()


    def setupTableWidgetSourceTargetMatches(self):
        
        # Kun käyttäjä valitsee lähdetasolta kohteen, niin lisää taulukkoon
        #  * lähdeaineiston nimi,
        #  * painike lähdetietosivun avaamiseen ja
        #  * painike lähdetason tietojen yhdistämiseen kohdetason kohteeseen
        # ? miten jo tietokannassa ko. rajapinnan kohteet huomioidaan?
        #   - voisi olla taulukossa jokin täppä, joka kertoo, että on jo tietokannassa eli
        #     kuitenkin samaan taulukkoon rajapinnalta jo tuodut tiedot ja tuomattomat tiedot
        #     -> itseasiassa kohde-tieto kertoo onko jo tietokannassa

        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.clearContents()
        # self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setRowCount(self.getSourceTargetMatchRowCount())
        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setColumnCount(4)
        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setHorizontalHeaderLabels([
            "Lähdenimi / tunniste",
            #"Lähdetietoikkuna",
            "Lähdetietosivu",
            "Yhdistetty kohde",
            "Yhdistä valittuun kohteeseen"#,
            #"Yhdistetään"#,
            #"Tiedot päivitettävissä"
        ])

        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.resizeColumnsToContents()


    def updateTableWidgetSourceTargetMatches(self):
        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.clearContents()

        comboBoxChooseSourceDataLayerIndex = self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.currentIndex()

        selectedFeatureCount = 0
        if self.selectedTargetLayer is not None:
            selectedFeatureCount = self.selectedTargetLayer.selectedFeatureCount()

        if comboBoxChooseSourceDataLayerIndex > 0 and selectedFeatureCount > 0:

            text = self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.itemText(comboBoxChooseSourceDataLayerIndex)
            title, name = self.getLayerTitleAndNameFromComboBoxText(text)

            apiIndex = self.dialogAddSourceDataLinks.comboBoxChooseSourceDataAPI.currentIndex() - 1
            apiID = self.apis[apiIndex]["id"]
            QgsMessageLog.logMessage('updateTableWidgetSourceTargetMatches, apiID: ' + str(apiID) + ', name: ' + name, 'Yleiskaava-työkalu', Qgis.Info)
            layer, layerInfo = self.yleiskaavaSourceDataAPIs.getLayerAndLayerInfo(apiID, name)

            # listaa kohteen nimi ja painikkeet, tms. taulukossa
            # listaa myös jo tietokannassa olevat kohteet (lähtöaineistorajapinnan osalta)
            if layer is None:
                self.iface.messageBar().pushMessage('Lähdekarttason kohteiden hakeminen ei onnistunut', Qgis.Critical)
            else:
                fields = layer.fields()
                for field in fields:
                    QgsMessageLog.logMessage('updateTableWidgetSourceTargetMatches, field.name(): ' + str(field.name()) + ', name: ' + name, 'Yleiskaava-työkalu', Qgis.Info)

                QgsMessageLog.logMessage('updateTableWidgetSourceTargetMatches, layer.featureCount(): ' + str(layer.featureCount()), 'Yleiskaava-työkalu', Qgis.Info)

                if self.selectedTargetLayer.selectedFeatureCount() > 0:
                    featureRequest = self.createFeatureRequestForSelectedFeatures(layer, layerInfo)
                    if featureRequest != None:

                        featureCount = 0
                        featureInfos = []
                        for index, feature in enumerate(layer.getFeatures(featureRequest)):
                            featureCount += 1 # layer.featureCount() ei luotettava
                            featureInfos.append({
                                "feature": feature,
                                "nimi": feature[layerInfo["nimi"]],
                                "linkki_data": feature[layerInfo["linkki_data"]]
                            })
                        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setRowCount(featureCount)
                        QgsMessageLog.logMessage('updateTableWidgetSourceTargetMatches - featureCount: ' + str(featureCount), 'Yleiskaava-työkalu', Qgis.Info)

                        if featureCount == 0:
                            self.iface.messageBar().pushMessage('Lähdeaineistokarttatasolta ei löytynyt valituista kohteista määritetyn rajaussuorakulmion sisältä kohteita', Qgis.Info, 10)

                        for index, featureInfo in enumerate(featureInfos):
                            # lähdeaineiston mukaan nimi/tunniste UI:hin
                            QgsMessageLog.logMessage('updateTableWidgetSourceTargetMatches, nimi: ' + str(featureInfo["nimi"]) + ', linkki_data: ' + str(featureInfo["linkki_data"]), 'Yleiskaava-työkalu', Qgis.Info)
                            
                            userFriendlyFieldNameLabel = QLabel(str(featureInfo["nimi"]))

                            infoLinkButton = QPushButton()
                            infoLinkButton.setText("Näytä lähdetietosivu")
                            infoLinkButton.clicked.connect(partial(self.showInfoPage, str(featureInfo["linkki_data"])))

                            linkedFeatureWidget = None
                            # yhdistä tietokannan data
                            linkedFeatureID, linkedSourceDataFeature = self.yleiskaavaSourceDataAPIs.getLinkedDatabaseFeatureIDAndSourceDataFeature(self.selectedTargetLayer, featureInfo)
                            if linkedFeatureID != None:
                                linkedFeatureWidget = QPushButton()
                                linkedFeatureWidget.setText("Näytä yhdistetty kohde")
                                linkedFeatureWidget.clicked.connect(partial(self.showLinkedFeature, self.selectedTargetLayer, linkedFeatureID))
                            else:
                                linkedFeatureWidget = QLabel()
                                linkedFeatureWidget.setAlignment(Qt.AlignCenter)
                                linkedFeatureWidget.setText("-")

                            linkToFeatureButton = QPushButton()
                            linkToFeatureButton.setText("Yhdistä")
                            linkToFeatureButton.clicked.connect(partial(self.addLinkBetweenSourceFeatureAndSelectedTargetFeature, index, featureInfo))

                            self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setCellWidget(index, AddSourceDataLinks.FIELD_USER_FRIENDLY_NAME_INDEX, userFriendlyFieldNameLabel)
                            self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setCellWidget(index, AddSourceDataLinks.INFO_LINK_INDEX, infoLinkButton)
                            self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setCellWidget(index, AddSourceDataLinks.LINKED_FEATURE_INDEX, linkedFeatureWidget)
                            self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setCellWidget(index, AddSourceDataLinks.LINK_TO_FEATURE_INDEX, linkToFeatureButton)

                self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.resizeColumnsToContents()


    def showInfoPage(self, infoPageURL):
        QDesktopServices.openUrl(QUrl(infoPageURL))


    def showLinkedFeature(self, layer, linkedFeatureID):
        # siiry kohteeseen kartalla, vilkuta kohdetta ja avaa kohteen tietoikkuna
        mapCanvas = self.iface.mapCanvas()
        linkedFeature = None
        for feature in layer.getFeatures():
            if feature["id"] == linkedFeatureID:
                linkedFeature = feature
                break

        mapCanvas.panToFeatureIds(layer, [linkedFeature.id()])
        mapCanvas.flashGeometries([linkedFeature.geometry()], layer.crs())
        self.iface.openFeatureForm(layer, linkedFeature)


    def handleComboBoxChooseTargetLayerIndexChanged(self, index):
        # if self.selectedTargetLayer is not None:
        #     try:
        #         self.selectedTargetLayer.selectionChanged.disconnect(self.handleFeatureSelectionChanged)
        #     except TypeError:
        #         pass
        #     except RuntimeError:
        #         pass

        self.setupTableWidgetSourceTargetMatches()
        self.dialogAddSourceDataLinks.comboBoxChooseSourceDataAPI.setCurrentIndex(0)
        self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.setCurrentIndex(0)
        self.dialogAddSourceDataLinks.pushButtonChooseFeatures.setEnabled(False)
        self.selectedTargetLayer = None

        if index > 0:
            self.dialogAddSourceDataLinks.pushButtonChooseFeatures.setEnabled(True)

            userFriendlyTableName = self.dialogAddSourceDataLinks.comboBoxChooseTargetLayer.currentText()
            self.selectedTargetLayer = QgsProject.instance().mapLayersByName(userFriendlyTableName)[0]
            if self.selectedTargetLayer.selectedFeatureCount() > 0:
                self.iface.messageBar().pushMessage('' + userFriendlyTableName + ' karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
            # self.selectedTargetLayer.selectionChanged.connect(self.handleFeatureSelectionChanged)

            self.updateTableWidgetSourceTargetMatches()


    def handlePushButtonChooseFeatureClicked(self):
        userFriendlyTableName = self.dialogAddSourceDataLinks.comboBoxChooseTargetLayer.currentText()
        if self.selectedTargetLayer is not None:
            try:
                self.selectedTargetLayer.selectionChanged.disconnect(self.handleFeatureSelectionChanged)
            except TypeError:
                pass
            except RuntimeError:
                pass
        self.selectedTargetLayer = QgsProject.instance().mapLayersByName(userFriendlyTableName)[0]
        if self.selectedTargetLayer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('' + userFriendlyTableName + ' karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.selectedTargetLayer.selectionChanged.connect(self.handleFeatureSelectionChanged)
        
        if self.selectedTargetLayer.selectedFeatureCount() == 1:
            self.handleFeatureSelectionChanged()

        self.iface.showAttributeTable(self.selectedTargetLayer)


    def handleFeatureSelectionChanged(self):
        self.updateTableWidgetSourceTargetMatches()


    def handleSpinBoxMaxSearchDistanceChanged(self, value):
        self.updateTableWidgetSourceTargetMatches()


    def handleComboBoxChooseSourceDataLayerIndexChanged(self, index):
        if index == 0:
            self.setupTableWidgetSourceTargetMatches()
        else:
            self.updateTableWidgetSourceTargetMatches()


    def handleComboBoxChooseSourceDataAPIIndexChanged(self, index):
        if index == 0:
            self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.setCurrentIndex(0)
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

    def createFeatureRequestForSelectedFeatures(self, layer, layerInfo):
        featureRequest = None

        transform = None
        selectedTargetLayerCRS = self.selectedTargetLayer.crs()
        if layer.crs() != selectedTargetLayerCRS:
            transform = QgsCoordinateTransform(selectedTargetLayerCRS, layer.crs(), QgsProject.instance())
        

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

        QgsMessageLog.logMessage('createFeatureRequestForSelectedFeatures - xMin: ' + str(xMin) + ", yMin: " + str(yMin) + ", xMax: " + str(xMax) + ", yMax: " + str(yMax), 'Yleiskaava-työkalu', Qgis.Info)

        if xMin is not None and yMin is not None and xMax is not None and yMax is not None:
            bboxAllFeatures = QgsRectangle(xMin, yMin, xMax, yMax)
            featureRequest = QgsFeatureRequest().setFilterRect(bboxAllFeatures).setFlags(QgsFeatureRequest.NoGeometry)
            # featureRequest = QgsFeatureRequest().setFilterRect(bboxAllFeatures).setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([layerInfo["nimi"], layerInfo["linkki_data"]], layer.fields())

        return featureRequest

    def addLinkBetweenSourceFeatureAndSelectedTargetFeature(self, tableWidgetSourceTargetMatchesRowIndex, sourceDataFeatureInfo):
        selectedFeatures = self.selectedTargetLayer.selectedFeatures()

        if len(selectedFeatures) == 0:
            self.iface.messageBar().pushMessage('' + userFriendlyTableName + ' karttatasolla ei ole valittua kaavakohdetta, joten linkkiä lähtöaineistoon ei voida listätä', Qgis.Info, 20)
        if len(selectedFeatures) > 1:
            self.iface.messageBar().pushMessage('' + userFriendlyTableName + ' karttatasolla on useita valittuja kaavakohteita, joten linkkiä lähtöaineistoon ei voida listätä', Qgis.Info, 20)
        else:
            # lisää tarvittaessa uusi lähdeaineistorivi tietokantaan,
            # lisää relaatio kaavakohteen ja lähdeaineistorivin välille ja
            # päivitä käyttöliittymän tauluun "Näytä yhdistetty kohde"-infopainike

            selectedFeatureID = selectedFeatures[0]["id"]

            apiIndex = self.dialogAddSourceDataLinks.comboBoxChooseSourceDataAPI.currentIndex() - 1
            sourceName = sourceDataFeatureInfo["nimi"]
            sourceReferenceAPIName = self.apis[apiIndex]["name"]
            #QgsMessageLog.logMessage('addLinkBetweenSourceFeatureAndSelectedTargetFeature, field.name(): ' + str(field.name()) + ', name: ' + name, 'Yleiskaava-työkalu', Qgis.Info)
            sourceDescription = ""
            for field in sourceDataFeatureInfo["feature"].fields():
                fieldName = field.name()
                fieldTypeName = self.yleiskaavaUtils.getStringTypeForFeatureField(field)
                if fieldTypeName != "uuid" and fieldTypeName != "Bool":
                    value = sourceDataFeatureInfo["feature"][fieldName]
                    if value is not None:
                        sourceDescription += fieldName.lower() + ": "
                        if (fieldTypeName == "Date" or fieldTypeName == "DateTime") and not QVariant(value).isNull():
                            sourceDescription += QDateTime(QVariant(value).value()).toString("dd.MM.yyyy")
                        else:
                            sourceDescription += str(value)
                        
                        sourceDescription += "; "
            if sourceDescription != "":
                sourceDescription = sourceDescription[:-2]
            sourceLinkType = self.apis[apiIndex]["linkitys_tyyppi"]
            sourceLinkData = sourceDataFeatureInfo["linkki_data"]

            sourceData = {
                "nimi": sourceName,
                "lahde": sourceReferenceAPIName,
                "kuvaus": sourceDescription,
                "linkitys_tyyppi": sourceLinkType,
                "linkki_data": sourceLinkData
            }

            success = self.yleiskaavaDatabase.createSourceDataFeatureAndRelationToSpatialFeature(sourceData, self.selectedTargetLayer, selectedFeatureID)

            if success:
                self.iface.messageBar().pushMessage('Lähdelinkki lisätty', Qgis.Info, 20)
                # päivitä käyttöliittymän tauluun "Näytä yhdistetty kohde"-infopainike
                linkedFeatureWidget = QPushButton()
                linkedFeatureWidget.setText("Näytä yhdistetty kohde")
                linkedFeatureWidget.clicked.connect(partial(self.showLinkedFeature, self.selectedTargetLayer, selectedFeatureID))
                self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setCellWidget(tableWidgetSourceTargetMatchesRowIndex, AddSourceDataLinks.LINKED_FEATURE_INDEX, linkedFeatureWidget)
                self.yleiskaavaUtils.refreshTargetLayersInProject()
            else:
                self.iface.messageBar().pushMessage('Lähdelinkin lisääminen epäonnistui', Qgis.Critical)