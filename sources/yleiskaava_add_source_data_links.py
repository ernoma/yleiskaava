
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QVariant, QUrl, QDateTime
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import QLabel, QPushButton

from qgis.core import (Qgis, QgsProject, QgsMessageLog,
    QgsGeometry, QgsCoordinateTransform,
    QgsFeatureRequest, QgsRectangle,
    QgsWkbTypes, QgsLayerTreeLayer,
    QgsTask, QgsApplication)

import os.path
from operator import itemgetter
from functools import partial

from .yleiskaava_source_data_apis import YleiskaavaSourceDataAPIs
from .yleiskaava_source_data_apis import FeatureRequestTask


class AddSourceDataLinks:

    FIELD_USER_FRIENDLY_NAME_INDEX = 0
    INFO_LINK_INDEX = 1
    SOURCE_FEATURE_INDEX = 2
    DISTANCE_INFO_INDEX = 3
    LINKED_FEATURE_INDEX = 4
    LINK_TO_FEATURE_INDEX = 5

    def __init__(self, iface, plugin_dir, yleiskaavaSettings, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.plugin_dir = plugin_dir

        self.yleiskaavaSettings = yleiskaavaSettings
        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.yleiskaavaSourceDataAPIs = YleiskaavaSourceDataAPIs(iface, self.plugin_dir, yleiskaavaDatabase, yleiskaavaUtils)

        self.dialogAddSourceDataLinks = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_add_source_data_links.ui'))

        self.selectedTargetLayer = None
        self.apis = None
        self.shownSourceLayer = None
        self.featureRequestTask = None
        self.originalSourceLayer = None
        self.originalSourceLayerInfo = None


    def setup(self):
        # lisää kohdekarttatasot comboboksiin
        # self.yleiskaavaDatabase.reconnectToDB()
        
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

        self.dialogAddSourceDataLinks.pushButtonClose.clicked.connect(self.handlePushButtonCloseClicked)

        self.setupTableWidgetSourceTargetMatches()

    def reset(self):

        self.setupTableWidgetSourceTargetMatches()

        self.dialogAddSourceDataLinks.comboBoxChooseTargetLayer.setCurrentIndex(0)
        self.dialogAddSourceDataLinks.comboBoxChooseSourceDataAPI.setCurrentIndex(0)
        self.dialogAddSourceDataLinks.comboBoxChooseSourceDataLayer.setCurrentIndex(0)

        self.dialogAddSourceDataLinks.pushButtonChooseFeatures.setEnabled(False)

        self.selectedTargetLayer = None
        # self.apis = None
        self.removeShownSourceLayer()

        self.shownSourceLayer = None
        self.featureRequestTask = None
        self.originalSourceLayer = None
        self.originalSourceLayerInfo = None


    def handlePushButtonCloseClicked(self):
        self.removeShownSourceLayer()
        self.dialogAddSourceDataLinks.hide()


    def openDialogAddSourceDataLinks(self):
        self.reset()
        
        if self.yleiskaavaSettings.shouldKeepDialogsOnTop():
            self.dialogAddSourceDataLinks.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        else:
            self.dialogAddSourceDataLinks.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
            
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
        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setColumnCount(6)
        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setHorizontalHeaderLabels([
            "Lähdenimi / tunniste",
            #"Lähdetietoikkuna",
            "Lähdetietosivu",
            "Lähde kartalla",
            "Etäisyys valitusta kohteesta (m)",
            "Yhdistetty kohde",
            "Yhdistä valittuun kohteeseen"#,
            #"Yhdistetään"#,
            #"Tiedot päivitettävissä"
        ])

        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.resizeColumnsToContents()


    def updateTableWidgetSourceTargetMatches(self):
        self.removeShownSourceLayer()

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
            # QgsMessageLog.logMessage('updateTableWidgetSourceTargetMatches, apiID: ' + str(apiID) + ', name: ' + name, 'Yleiskaava-työkalu', Qgis.Info)
            layer, layerInfo = self.yleiskaavaSourceDataAPIs.getLayerAndLayerInfo(apiID, name)

            # QgsMessageLog.logMessage('updateTableWidgetSourceTargetMatches - layer.geometryType(): ' + str(layer.geometryType()), 'Yleiskaava-työkalu', Qgis.Info)

            # listaa kohteen nimi ja painikkeet, tms. taulukossa
            # listaa myös jo tietokannassa olevat kohteet (lähtöaineistorajapinnan osalta)
            if layer is None:
                self.iface.messageBar().pushMessage('Lähdekarttason kohteiden hakeminen ei onnistunut', Qgis.Critical, duration=0)
            else:
                fields = layer.fields()
                # for field in fields:
                #     QgsMessageLog.logMessage('updateTableWidgetSourceTargetMatches, field.name(): ' + str(field.name()) + ', name: ' + name, 'Yleiskaava-työkalu', Qgis.Info)

                # QgsMessageLog.logMessage('updateTableWidgetSourceTargetMatches, layer.featureCount(): ' + str(layer.featureCount()), 'Yleiskaava-työkalu', Qgis.Info)

                if self.selectedTargetLayer.selectedFeatureCount() > 0:

                    featureRequest = self.createFeatureRequestForSelectedFeatures(layer, layerInfo)
                    if featureRequest != None:

                        self.originalSourceLayer = layer
                        self.originalSourceLayerInfo = layerInfo

                        self.featureRequestTask = FeatureRequestTask(layer, featureRequest)
                        self.featureRequestTask.taskCompleted.connect(self.postFeatureRequestTaskRun)
                        self.featureRequestTask.taskTerminated.connect(self.postFeatureRequestTaskError)
                        QgsApplication.taskManager().addTask(self.featureRequestTask)
                        self.iface.messageBar().pushMessage('Haetaan lähdeaineiston kohteita', Qgis.Info, duration=5)


    def postFeatureRequestTaskError(self):
        self.iface.messageBar().pushMessage('Lähdeaineiston kohteiden hakeminen epäonnistui', Qgis.Critical, duration=0)
        self.reset()


    def postFeatureRequestTaskRun(self):
        try:
            self.iface.messageBar().popWidget()
        except RuntimeError:
            pass
        
        self.iface.messageBar().pushMessage('Lähdeaineiston kohteet haettu', Qgis.Info, duration=5)

        # self.yleiskaavaDatabase.reconnectToDB()

        self.shownSourceLayer = self.yleiskaavaSourceDataAPIs.createMemoryLayer(self.originalSourceLayer, self.originalSourceLayerInfo, self.featureRequestTask.features)
        
        if self.shownSourceLayer is not None and self.shownSourceLayer.featureCount() > 0:
            self.showSourceLayer()

        featureCount = 0
        featureInfos = []

        selectedTargetLayerFeatureRequest = QgsFeatureRequest().setNoAttributes().setLimit(1)
        if self.shownSourceLayer.fields().indexFromName(self.originalSourceLayerInfo["nimi"]) != -1 and self.shownSourceLayer.fields().indexFromName(self.originalSourceLayerInfo["linkki_data"]) != -1:
            for index, feature in enumerate(self.shownSourceLayer.getFeatures()):
                if feature.isValid():
                    featureCount += 1 # layer.featureCount() ei luotettava
                    featureInfos.append({
                        "feature": feature,
                        "distance": self.getDistance(self.shownSourceLayer, feature, self.selectedTargetLayer, list(self.selectedTargetLayer.getSelectedFeatures(selectedTargetLayerFeatureRequest))[0]),
                        "nimi": feature[self.originalSourceLayerInfo["nimi"]],
                        "linkki_data": feature[self.originalSourceLayerInfo["linkki_data"]]
                    })
        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setRowCount(featureCount)
        # QgsMessageLog.logMessage('updateTableWidgetSourceTargetMatches - featureCount: ' + str(featureCount), 'Yleiskaava-työkalu', Qgis.Info)

        if featureCount == 0:
            self.iface.messageBar().pushMessage('Lähdeaineistokarttatasolta ei löytynyt valituista kohteista määritetyn rajaussuorakulmion sisältä kohteita', Qgis.Info, duration=10)

        for index, featureInfo in enumerate(sorted(featureInfos, key=itemgetter("distance"))):
            # lähdeaineiston mukaan nimi/tunniste UI:hin
            # QgsMessageLog.logMessage('updateTableWidgetSourceTargetMatches, nimi: ' + str(featureInfo["nimi"]) + ', linkki_data: ' + str(featureInfo["linkki_data"]), 'Yleiskaava-työkalu', Qgis.Info)
            
            userFriendlyFieldNameLabel = QLabel(str(featureInfo["nimi"]))

            infoLinkButton = QPushButton()
            infoLinkButton.setText("Näytä lähdetietosivu")
            infoLinkButton.clicked.connect(partial(self.showInfoPage, str(featureInfo["linkki_data"])))

            sourceMapButton = QPushButton()
            sourceMapButton.setText("Näytä")
            sourceMapButton.clicked.connect(partial(self.showSourceFeature, self.shownSourceLayer, featureInfo["feature"].id()))

            distanceLabel = QLabel()
            distanceLabel.setAlignment(Qt.AlignCenter)
            distanceLabel.setText(str(featureInfo["distance"]))

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
            self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setCellWidget(index, AddSourceDataLinks.SOURCE_FEATURE_INDEX, sourceMapButton)
            self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setCellWidget(index, AddSourceDataLinks.DISTANCE_INFO_INDEX, distanceLabel)
            self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setCellWidget(index, AddSourceDataLinks.LINKED_FEATURE_INDEX, linkedFeatureWidget)
            self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setCellWidget(index, AddSourceDataLinks.LINK_TO_FEATURE_INDEX, linkToFeatureButton)

        self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.resizeColumnsToContents()


    def showSourceLayer(self):
        QgsProject.instance().addMapLayer(self.shownSourceLayer, False)
        layerTree = self.iface.layerTreeCanvasBridge().rootGroup()
        # the position is a number starting from 0, with -1 an alias for the end
        layerTree.insertChildNode(0, QgsLayerTreeLayer(self.shownSourceLayer))
        self.shownSourceLayer.setOpacity(0.5)
        # self.shownSourceLayer.commitChanges()


    def removeShownSourceLayer(self):
        if self.shownSourceLayer is not None:
            try:
                # self.shownSourceLayer.commitChanges()
                # layerTree = self.iface.layerTreeCanvasBridge().rootGroup()
                # layerTree.removeLayer(self.shownSourceLayer)
                # QgsProject.instance().takeMapLayer(self.shownSourceLayer)
                QgsProject.instance().removeMapLayer(self.shownSourceLayer.id())
            except RuntimeError:
                pass


    def showInfoPage(self, infoPageURL):
        QDesktopServices.openUrl(QUrl(infoPageURL))


    def showLinkedFeature(self, layer, featureID):
        # siiry kohteeseen kartalla, vilkuta kohdetta ja avaa kohteen tietoikkuna
        mapCanvas = self.iface.mapCanvas()
        linkedFeature = None
        for feature in layer.getFeatures():
            if feature["id"] == featureID:
                linkedFeature = feature
                break

        mapCanvas.panToFeatureIds(layer, [linkedFeature.id()])
        mapCanvas.flashGeometries([linkedFeature.geometry()], layer.sourceCrs())
        self.iface.openFeatureForm(layer, linkedFeature)


    def showSourceFeature(self, layer, fid):
        # siiry kohteeseen kartalla, vilkuta kohdetta ja avaa kohteen tietoikkuna
        mapCanvas = self.iface.mapCanvas()
        linkedFeature = None
        for feature in layer.getFeatures():
            if feature.id() == fid:
                linkedFeature = feature
                break

        mapCanvas.panToFeatureIds(layer, [linkedFeature.id()])
        mapCanvas.flashGeometries([linkedFeature.geometry()], layer.sourceCrs())
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
                self.iface.messageBar().pushMessage('' + userFriendlyTableName + ' karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, duration=20)
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
             self.iface.messageBar().pushMessage('' + userFriendlyTableName + ' karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, duration=20)
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
        selectedTargetLayerCRS = self.selectedTargetLayer.sourceCrs()
        if layer.sourceCrs() != selectedTargetLayerCRS:
            transform = QgsCoordinateTransform(selectedTargetLayerCRS, layer.sourceCrs(), QgsProject.instance())

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

        # QgsMessageLog.logMessage('createFeatureRequestForSelectedFeatures - xMin: ' + str(xMin) + ", yMin: " + str(yMin) + ", xMax: " + str(xMax) + ", yMax: " + str(yMax), 'Yleiskaava-työkalu', Qgis.Info)

        if xMin is not None and yMin is not None and xMax is not None and yMax is not None:
            bboxAllFeatures = QgsRectangle(xMin, yMin, xMax, yMax)
            featureRequest = QgsFeatureRequest().setFilterRect(bboxAllFeatures)
            # featureRequest = QgsFeatureRequest().setFilterRect(bboxAllFeatures).setFlags(QgsFeatureRequest.NoGeometry)
            # featureRequest = QgsFeatureRequest().setFilterRect(bboxAllFeatures).setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([layerInfo["nimi"], layerInfo["linkki_data"]], layer.fields())

        return featureRequest

    def addLinkBetweenSourceFeatureAndSelectedTargetFeature(self, tableWidgetSourceTargetMatchesRowIndex, sourceDataFeatureInfo):
        selectedFeatures = self.selectedTargetLayer.selectedFeatures()

        if len(selectedFeatures) == 0:
            self.iface.messageBar().pushMessage('' + userFriendlyTableName + ' karttatasolla ei ole valittua kaavakohdetta, joten linkkiä lähtöaineistoon ei voida listätä', Qgis.Info, duration=20)
        if len(selectedFeatures) > 1:
            self.iface.messageBar().pushMessage('' + userFriendlyTableName + ' karttatasolla on useita valittuja kaavakohteita, joten linkkiä lähtöaineistoon ei voida listätä', Qgis.Info, duration=20)
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
                self.iface.messageBar().pushMessage('Lähdelinkki lisätty', Qgis.Info, duration=20)
                # päivitä käyttöliittymän tauluun "Näytä yhdistetty kohde"-infopainike
                linkedFeatureWidget = QPushButton()
                linkedFeatureWidget.setText("Näytä yhdistetty kohde")
                linkedFeatureWidget.clicked.connect(partial(self.showLinkedFeature, self.selectedTargetLayer, selectedFeatures[0]["id"]))
                self.dialogAddSourceDataLinks.tableWidgetSourceTargetMatches.setCellWidget(tableWidgetSourceTargetMatchesRowIndex, AddSourceDataLinks.LINKED_FEATURE_INDEX, linkedFeatureWidget)
                self.yleiskaavaUtils.refreshTargetLayersInProject()
            else:
                self.iface.messageBar().pushMessage('Lähdelinkin lisääminen epäonnistui', Qgis.Critical, duration=0)


    def getDistance(self, layer1, feature1, layer2, feature2):
        distance = -1

        transform = None
        if layer1.sourceCrs() != layer2.sourceCrs():
            transform = QgsCoordinateTransform(layer1.sourceCrs(), layer2.sourceCrs(), QgsProject.instance())

        geom1 = feature1.geometry()
        geom2 = feature2.geometry()

        if not geom1.isNull() and not geom2.isNull():
            transformedSourceGeom1 = None
            if transform is not None:
                transformedGeom1 = QgsGeometry(geom1)
                transformedGeom1.transform(transform)
            else:
                transformedGeom1 = QgsGeometry(geom)

            distance = int(round(transformedGeom1.distance(geom2)))

        return distance
                