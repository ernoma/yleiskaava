
from PyQt5 import uic
from qgis.PyQt.QtCore import QTimer, Qt, QSize
from qgis.PyQt.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox, QCheckBox

from qgis.core import (
    Qgis, QgsProject, QgsFeature, QgsField, QgsMessageLog, QgsMapLayer, QgsVectorLayer, QgsAuxiliaryLayer, QgsMapLayerProxyModel, QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform)

from qgis.gui import QgsFieldValuesLineEdit, QgsDateTimeEdit

import os.path
from functools import partial
from collections import Counter
import uuid

from .yleiskaava_database import YleiskaavaDatabase
from .yleiskaava_dialog_copy_source_data_to_database import Ui_DialogCopySourceDataToDatabase
#from .yleiskaava_dialog_copy_settings import Ui_DialogCopySettings
from .yleiskaava_utils import YleiskaavaUtils


class DataCopySourceToTarget:
    
    SOURCE_FIELD_NAME_INDEX = 0
    SOURCE_FIELD_TYPE_NAME_INDEX = 1
    TARGET_TABLE_NAME_INDEX = 2
    TARGET_TABLE_FIELD_NAME_INDEX = 3

    DEFAULT_VALUES_GRID_LABEL_INDEX = 0
    DEFAULT_VALUES_GRID_INPUT_INDEX = 1

    SETTINGS_DIALOG_MIN_WIDTH = 1068
    SETTINGS_DIALOG_MIN_HEIGHT = 1182

    COPY_SOURCE_DATA_DIALOG_MIN_WIDTH = 1006
    COPY_SOURCE_DATA_DIALOG_MIN_HEIGHT = 624


    def __init__(self, iface, yleiskaavaDatabase):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = YleiskaavaUtils()

        self.plugin_dir = os.path.dirname(__file__)

        self.dialogCopySourceDataToDatabase = Ui_DialogCopySourceDataToDatabase()
        self.dialogCopySourceDataToDatabaseWidget = QWidget()
        self.dialogCopySourceDataToDatabase.setupUi(self.dialogCopySourceDataToDatabaseWidget)

        self.dialogChooseFeatures = uic.loadUi(os.path.join(self.plugin_dir, 'yleiskaava_dialog_choose_features.ui'))

        self.dialogCopySettings = uic.loadUi(os.path.join(self.plugin_dir, 'yleiskaava_dialog_copy_settings.ui'))
        self.dialogCopySettings.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        self.sourceLayer = None

        self.targetSchemaTableName = None
        self.targetLayer = None

        self.targetTableComboBoxes = []
        self.targetFieldNameComboBoxes = []

        self.gridLayoutDefaultFieldValuesCounter = 0


    def setup(self):
        self.setupDialogCopySourceDataToDatabase()
        self.setupDialogChooseFeatures()
        self.setupDialogCopySettings()


    def setupDialogCopySourceDataToDatabase(self):
        self.dialogCopySourceDataToDatabase.pushButtonCancel.clicked.connect(self.cancelAndHideAllDialogs)
        self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.layerChanged.connect(self.handleMapLayerComboBoxSourceChanged)
        self.dialogCopySourceDataToDatabase.pushButtonNext.clicked.connect(self.chooseSourceFeatures)


    def setupDialogChooseFeatures(self):
        self.dialogChooseFeatures.pushButtonCancel.clicked.connect(self.cancelAndHideAllDialogs)
        self.dialogChooseFeatures.pushButtonPrevious.clicked.connect(self.showDialogCopySourceDataToDatabase)
        self.dialogChooseFeatures.pushButtonNext.clicked.connect(self.chooseCopySettings)


    def setupDialogCopySettings(self):
        self.dialogCopySettings.pushButtonCancel.clicked.connect(self.cancelAndHideAllDialogs)
        self.dialogCopySettings.pushButtonPrevious.clicked.connect(self.chooseSourceFeatures)
        self.dialogCopySettings.pushButtonRun.clicked.connect(self.runCopySourceDataToDatabase)


    def cancelAndHideAllDialogs(self):
        self.dialogCopySourceDataToDatabaseWidget.hide()
        self.dialogChooseFeatures.hide()
        self.dialogCopySettings.hide()


    def openDialogCopySourceDataToDatabase(self):
        # layers = QgsProject.instance().mapLayers()
        # vectorLayers = []

        # for layer_id, layer in layers.items():
        #     # QgsMessageLog.logMessage(layer_id, 'Yleiskaava-työkalu', Qgis.Info)
        #     # QgsMessageLog.logMessage(layer.name(), 'Yleiskaava-työkalu', Qgis.Info)
            
        #     if isinstance(layer, QgsVectorLayer) and not isinstance(layer, QgsAuxiliaryLayer):
        #         vectorLayers.append(layer.name())
        #         #QgsMessageLog.logMessage(layer_id, 'Yleiskaava-työkalu', Qgis.Info)
        #         #QgsMessageLog.logMessage(layer.name(), 'Yleiskaava-työkalu', Qgis.Info)
        #     else:
        #         QgsMessageLog.logMessage(layer_id, 'Yleiskaava-työkalu', Qgis.Info)
        #         QgsMessageLog.logMessage(layer.name(), 'Yleiskaava-työkalu', Qgis.Info)
        # self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.clear()
        # #self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.addItems(sorted(vectorLayers))

        self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.setFilters(QgsMapLayerProxyModel.HasGeometry)
        self.dialogCopySourceDataToDatabaseWidget.resize(QSize(DataCopySourceToTarget.COPY_SOURCE_DATA_DIALOG_MIN_WIDTH, DataCopySourceToTarget.COPY_SOURCE_DATA_DIALOG_MIN_HEIGHT))
        self.dialogCopySourceDataToDatabaseWidget.show()
        self.sourceLayer = self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.currentLayer()
        if self.sourceLayer is not None:
            # QgsMessageLog.logMessage(layer.name(), 'Yleiskaava-työkalu', Qgis.Info)
            self.updateUIBasedOnSourceLayer(self.sourceLayer)


    def showDialogCopySourceDataToDatabase(self):
        #self.dialogCopySourceDataToDatabaseWidget.hide()
        self.dialogChooseFeatures.hide()
        self.dialogCopySettings.hide()
        self.dialogCopySourceDataToDatabaseWidget.resize(QSize(DataCopySourceToTarget.COPY_SOURCE_DATA_DIALOG_MIN_WIDTH, DataCopySourceToTarget.COPY_SOURCE_DATA_DIALOG_MIN_HEIGHT))
        self.dialogCopySourceDataToDatabaseWidget.show()


    def handleMapLayerComboBoxSourceChanged(self, layer):
        # QgsMessageLog.logMessage(layer.name(), 'Yleiskaava-työkalu', Qgis.Info)
        self.sourceLayer = layer
        self.updateUIBasedOnSourceLayer(self.sourceLayer)


    def updateUIBasedOnSourceLayer(self, sourceLayer):

        #self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch = QGridLayout()
        #self.dialogCopySourceDataToDatabasegridLayoutSourceTargetMatch.setObjectName("gridLayoutSourceTargetMatch")
        self.yleiskaavaUtils.emptyGridLayout(self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch)

        self.targetTableComboBoxes = []
        self.targetFieldNameComboBoxes = []

        for index, field in enumerate(sourceLayer.fields().toList()):
            if field.name() != 'id' and self.yleiskaavaUtils.getStringTypeForFeatureField(field) != 'uuid':
                sourceFieldnameLabel = QLabel(field.name())
                sourceFieldtypeLabel = QLabel(self.yleiskaavaUtils.getStringTypeForFeatureField(field))
                
                targetTableComboBox = QComboBox()

                targetTableNames = sorted(self.yleiskaavaDatabase.getTargetSchemaTableNamesShownInCopySourceToTargetUI())
                targetTableNames.insert(0, "Valitse kohdetaulu")

                targetTableComboBox.addItems(targetTableNames)
                self.targetTableComboBoxes.append(targetTableComboBox)
                
                targetFieldNameComboBox = QComboBox()
                self.targetFieldNameComboBoxes.append(targetFieldNameComboBox)
                
                self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.addWidget(sourceFieldnameLabel, index, DataCopySourceToTarget.SOURCE_FIELD_NAME_INDEX, 1, 1)
                self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.addWidget(sourceFieldtypeLabel, index, DataCopySourceToTarget.SOURCE_FIELD_TYPE_NAME_INDEX, 1, 1)
                self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.addWidget(targetTableComboBox, index, DataCopySourceToTarget.TARGET_TABLE_NAME_INDEX, 1, 1)
                self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.addWidget(targetFieldNameComboBox, index, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX, 1, 1)

                targetTableComboBox.currentTextChanged.connect(partial(self.handleTargetTableSelectChanged, index, targetTableComboBox, targetFieldNameComboBox))


    def handleTargetTableSelectChanged(self, rowIndex, targetTableComboBox, targetFieldNameComboBox):

        # TODO: anna valita vain geometrialtaan lähdetason kanssa yhteensopiva kohdetaso

        # TODO: varmista, että kukin kohdekenttä on mahdollista valita vain kerran

        # QgsMessageLog.logMessage('handleTargetTableSelectChanged', 'Yleiskaava-työkalu', Qgis.Info)
        self.targetSchemaTableName = targetTableComboBox.currentText()
        QgsMessageLog.logMessage('targetTableName: ' + self.targetSchemaTableName + ', rowIndex: ' + str(rowIndex), 'Yleiskaava-työkalu', Qgis.Info)

        if self.targetSchemaTableName != "Valitse kohdetaulu":
            self.targetLayer = self.yleiskaavaDatabase.createLayerByTargetSchemaTableName(self.targetSchemaTableName)

            #colnames = [desc.name for desc in curs.description]

            # TODO näytä kohdekentissä vain lähdekentän kanssa tyypiltään yhteensopivat kentät

            targetFieldNames = ['']

            for index, field in enumerate(self.targetLayer.fields().toList()):
                targetFieldName = field.name()
                targetFieldTypeName = self.yleiskaavaUtils.getStringTypeForFeatureField(field)
                targetFieldNames.append('' + targetFieldName + ' (' + targetFieldTypeName + ')')
                #QgsMessageLog.logMessage(targetFieldNames[index], 'Yleiskaava-työkalu', Qgis.Info)

            targetFieldNameComboBox.clear()
            targetFieldNameComboBox.addItems(targetFieldNames)

            sourceFieldName = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(rowIndex, DataCopySourceToTarget.SOURCE_FIELD_NAME_INDEX).widget().text()
            sourceFieldTypeName = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(rowIndex, DataCopySourceToTarget.SOURCE_FIELD_TYPE_NAME_INDEX).widget().text()

            self.selectBestFittingTargetField(sourceFieldName, sourceFieldTypeName, self.targetLayer.fields(), targetFieldNameComboBox)

            #
            # Helpfully guess values for other widgets
            #
            for index, tempTargetTableComboBox in enumerate(self.targetTableComboBoxes):
                tempTargetTableName = tempTargetTableComboBox.currentText()
                #if tempTargetTableName == "Valitse kohdetaulu":
                tempTargetTableComboBox.setCurrentText(self.targetSchemaTableName)
                # self.targetFieldNameComboBoxes[index].clear()
                # self.targetFieldNameComboBoxes[index].addItems(targetFieldNames)

                # tempSourceFieldName = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(index, DataCopySourceToTarget.SOURCE_FIELD_NAME_INDEX).widget().text()
                # tempSourceFieldTypeName = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(index, DataCopySourceToTarget.SOURCE_FIELD_TYPE_NAME_INDEX).widget().text()
                # self.selectBestFittingTargetField(tempSourceFieldName, tempSourceFieldTypeName, targetLayer.fields(), self.targetFieldNameComboBoxes[index])
                # self.selectBestFittingTargetField(sourceFieldName, sourceFieldTypeName, targetLayer.fields(),  self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(index, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).widget())
        else:
            targetFieldNameComboBox.clear()


    def selectBestFittingTargetField(self, sourceFieldName, sourceFieldTypeName, targetFields, targetFieldNameComboBox):
        
        max_levenshtein_ratio = 0

        for index, field in enumerate(targetFields.toList()):
            targetFieldName = field.name()
            targetFieldTypeName = self.yleiskaavaUtils.getStringTypeForFeatureField(field)

            levenshtein_ratio = self.yleiskaavaUtils.levenshteinRatioAndDistance(sourceFieldName.lower(), targetFieldName)

            if sourceFieldName.lower() == targetFieldName and sourceFieldTypeName == targetFieldTypeName:
                targetFieldNameComboBox.setCurrentIndex(index + 1)
                QgsMessageLog.logMessage('foundMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
                break
            elif sourceFieldName.lower() == targetFieldName and sourceFieldName.lower() != 'id':
                targetFieldNameComboBox.setCurrentIndex(index + 1)
                QgsMessageLog.logMessage('foundMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
                break # should not be possible to have many cols with the same name
            elif sourceFieldName.lower() != 'id' and targetFieldTypeName != 'uuid' and levenshtein_ratio > max_levenshtein_ratio and levenshtein_ratio > 0.5:
                #QgsMessageLog.logMessage('Levenshtein_ratio : ' + str(levenshtein_ratio), 'Yleiskaava-työkalu', Qgis.Info)
                max_levenshtein_ratio = levenshtein_ratio
                targetFieldNameComboBox.setCurrentIndex(index + 1)
                QgsMessageLog.logMessage('foundLevenshtein_ratioMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
            elif (sourceFieldName.lower() in targetFieldName or targetFieldName in sourceFieldName.lower()) and sourceFieldName.lower() != 'id' and targetFieldTypeName != 'uuid':
                #foundMatch = True
                targetFieldNameComboBox.setCurrentIndex(index + 1)
                QgsMessageLog.logMessage('foundPartialNameMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
            # elif sourceFieldTypeName == targetFieldTypeName and not foundMatch:
            #     foundMatch = True
            #     targetFieldNameComboBox.setCurrentIndex(index + 1)
            #     QgsMessageLog.logMessage('foundTypeMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)


    def chooseSourceFeatures(self):
        # TODO varmista, että self.targetSchemaTableName != None ja tarvittaessa ilmoita käyttäjälle
        self.dialogCopySourceDataToDatabaseWidget.hide()
        self.dialogCopySettings.hide()
        self.dialogChooseFeatures.show()
        self.iface.showAttributeTable(self.sourceLayer)


    def chooseCopySettings(self):
        # TODO varmista, että ainakin yksi lähde-feature on valittuna ja tarvittaessa ilmoita käyttäjälle
        self.dialogCopySourceDataToDatabaseWidget.hide()
        self.dialogChooseFeatures.hide()
        self.showDialogCopySettings()


    def showDialogCopySettings(self):
        
        # hae kaikki yleiskaavataulun yleiskaavojen nimet, täytä comboBoxSpatialPlanName ja valitse tyypillisin nimi
        layer = self.yleiskaavaDatabase.createLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
        features = layer.getFeatures()
        planNames = []
        for index, feature in enumerate(features):
            planNames.append(feature['nimi'])

        planNameCounter = Counter(planNames)

        planNamesOrderedWithCount = planNameCounter.most_common()

        planNamesOrdered = [item[0] for item in planNamesOrderedWithCount]

        self.dialogCopySettings.comboBoxSpatialPlanName.clear()
        if len(planNamesOrdered) > 0:
            self.dialogCopySettings.comboBoxSpatialPlanName.addItems(sorted(planNamesOrdered))
            self.dialogCopySettings.comboBoxSpatialPlanName.setCurrentText(planNamesOrdered[0])

        # hae kaikki kaavatasot, täytä comboBoxLevelOfSpatialPlan niiden nimillä ja valitse sopiva yleiskaavataso
        planLevelList = self.yleiskaavaDatabase.getYleiskaavaPlanLevelList()

        planLevelNames = [item["koodi"] for item in planLevelList]

        # TODO kun käyttäjä vaihtaa yleiskaavan, niin vaihda automaattisesti kaavataso (tarvittaessa)

        self.dialogCopySettings.comboBoxLevelOfSpatialPlan.addItems(sorted(planLevelNames))
        self.dialogCopySettings.comboBoxLevelOfSpatialPlan.setCurrentText("paikallinen")

        # 
        # TODO esitä dialogissa sellaiset kohdekentät, joilla ei ole vielä arvoa tauluissa
        # yleiskaava, kaavaobjekti_*, kaavamaarays. Hae oletusarvot, jos mahdollista,
        # käyttäjän jo tekemien valintojen muukaan, esim. yleiskaavan nro nimen mukaan
        # Käsittele id_* kentät ja eri tyyppiset kentät jotenkin järkevästi
        #
        self.yleiskaavaUtils.emptyGridLayout(self.dialogCopySettings.gridLayoutDefaultFieldValues)
        self.gridLayoutDefaultFieldValuesCounter = 0

        # spatialPlanLayer = self.yleiskaavaDatabase.createLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
        spatialTargetTableLayer = self.yleiskaavaDatabase.createLayerByTargetSchemaTableName(self.targetSchemaTableName)
        # regulationLayer =  self.yleiskaavaDatabase.createLayerByTargetSchemaTableName("yk_yleiskaava.kaavamaarays")

        # spatialPlanFields = self.yleiskaavaDatabase.getSchemaTableFields("yk_yleiskaava.yleiskaava")
        spatialTargetTableFields = self.yleiskaavaDatabase.getSchemaTableFields(self.targetSchemaTableName)
        # regulationFields = self.yleiskaavaDatabase.getSchemaTableFields("yk_yleiskaava.kaavamaarays")

        # spatialPlanFieldsToGetDefaults = []
        spatialTargetTableFieldsToGetDefaults = []
        # regulationFieldsToGetDefaults = []

        #self.chosenTargetFieldNames = self.getChosenTargetFieldNames()

        # for index, field in enumerate(spatialPlanFields):
        #     if field.name() != "id" and field.name() != "nimi" and field.name() != "id_kaavan_taso":
        #         spatialPlanFieldsToGetDefaults.append(field)
        #         self.showFieldInSettingsDialogDefaults("yk_yleiskaava.yleiskaava", spatialPlanLayer, index, field)

        for index, field in enumerate(spatialTargetTableFields):
            if field.name() != "id": # and field.name() not in self.chosenTargetFieldNames:
                spatialTargetTableFieldsToGetDefaults.append(field)
                self.showFieldInSettingsDialogDefaults(self.targetSchemaTableName, spatialTargetTableLayer, index, field)

        # for index, field in enumerate(regulationFields):
        #     if field.name() != "id" and field.name() != "kaavamaarays_otsikko":
        #         regulationFieldsToGetDefaults.append(field)
        #         self.showFieldInSettingsDialogDefaults("yk_yleiskaava.kaavamaarays", regulationLayer, index, field)

        self.dialogCopySettings.resize(QSize(DataCopySourceToTarget.SETTINGS_DIALOG_MIN_WIDTH, DataCopySourceToTarget.SETTINGS_DIALOG_MIN_HEIGHT))
        self.dialogCopySettings.show()
        

    def getChosenTargetFieldNames(self):
        # TODO hae valittujen kohdekenttien nimet dialogin gridistä
        names = []
        index = 0
        for field in self.sourceLayer.fields().toList():
            if field.name() != 'id' and self.yleiskaavaUtils.getStringTypeForFeatureField(field) != 'uuid':
                name = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(index, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).widget().currentText()
                if len(name) > 0:
                    names.append(name.split(' ')[0]) # Remove type and append
                index += 1
        return names


    def showFieldInSettingsDialogDefaults(self, schemaTableName, layer, fieldIndex, field):
        # targetSchemaTableLabel = QLabel(schemaTableName)
        # targetFieldLabel = QLabel(field.name())

        targetFieldName = field.name()
        targetFieldTypeName = self.yleiskaavaUtils.getStringTypeForFeatureField(field)

        if targetFieldName != 'id_yleiskaava' and targetFieldName != 'kayttotarkoitus_lyhenne' and targetFieldName != 'kansallinen_laillinen_sitovuus'  and targetFieldName != 'kohde_periytyy_muualta' and targetFieldName != 'pinta_ala_ha' and targetFieldName != 'pituus_km' and targetFieldName != 'rakennusoikeus_kem' and targetFieldName != 'rakennusoikeus_lkm' and targetFieldName != 'id_kaavakohteen_olemassaolo' and targetFieldName != 'id_kansallisen_kaavakohteen_olemassaolo':

            userFriendlyTableName = self.yleiskaavaDatabase.getUserFriendlyschemaTableName(schemaTableName)
            userFriendlyFieldName = self.yleiskaavaDatabase.getUserFriendlytargetFieldName(targetFieldName)

            # targetFieldLabel = QLabel('' + targetFieldName + ' (' + targetFieldTypeName + ')')
            # targetSchemaTableFieldLabel = QLabel(schemaTableName + '.' + targetFieldName + ' (' + targetFieldTypeName + ')')
            targetSchemaTableFieldLabel = QLabel(userFriendlyTableName + ' - ' + userFriendlyFieldName)
            self.dialogCopySettings.gridLayoutDefaultFieldValues.addWidget(targetSchemaTableFieldLabel, self.gridLayoutDefaultFieldValuesCounter, DataCopySourceToTarget.DEFAULT_VALUES_GRID_LABEL_INDEX, 1, 1)
            # self.dialogCopySettings.gridLayoutDefaultFieldValues.addWidget(targetFieldLabel, self.gridLayoutDefaultFieldValuesCounter, 1, 1, 1)

            if targetFieldTypeName == 'String' or targetFieldTypeName == 'Int' or targetFieldTypeName == 'Double':
                lineEdit = QgsFieldValuesLineEdit()
                lineEdit.setLayer(layer)
                lineEdit.setAttributeIndex(fieldIndex)

                self.dialogCopySettings.gridLayoutDefaultFieldValues.addWidget(lineEdit, self.gridLayoutDefaultFieldValuesCounter, DataCopySourceToTarget.DEFAULT_VALUES_GRID_INPUT_INDEX, 1, 1)
            elif targetFieldTypeName == 'Date':
                dateEdit = QgsDateTimeEdit()
                dateEdit.setAllowNull(True)
                dateEdit.clear()

                self.dialogCopySettings.gridLayoutDefaultFieldValues.addWidget(dateEdit, self.gridLayoutDefaultFieldValuesCounter, DataCopySourceToTarget.DEFAULT_VALUES_GRID_INPUT_INDEX, 1, 1)
            elif targetFieldTypeName == 'Bool':
                comboBox = QComboBox()
                values = ["", "Kyllä", "Ei"]
                comboBox.addItems(values)
                #checkBox = QCheckBox("Kyllä / ei")

                self.dialogCopySettings.gridLayoutDefaultFieldValues.addWidget(comboBox, self.gridLayoutDefaultFieldValuesCounter, DataCopySourceToTarget.DEFAULT_VALUES_GRID_INPUT_INDEX, 1, 1)
            elif targetFieldTypeName == 'uuid':
                values = self.yleiskaavaDatabase.getCodeListValuesForSchemaTable(targetFieldName)
                values.insert(0, "")
                comboBox = QComboBox()
                comboBox.addItems(values)

                self.dialogCopySettings.gridLayoutDefaultFieldValues.addWidget(comboBox, self.gridLayoutDefaultFieldValuesCounter, DataCopySourceToTarget.DEFAULT_VALUES_GRID_INPUT_INDEX, 1, 1)

            self.gridLayoutDefaultFieldValuesCounter += 1


    def runCopySourceDataToDatabase(self):
        # TODO Lisää lähdeaineiston valittujen rivien tiedot kohdetauluun ja huomioi myös oletusarvot, puuttuvat arvot, yhteydet yleiskaava-, kaavamääräys- ja koodi-tauluihin sekä tarvittaessa tee uudet kaavamääräykset

        self.copySourceFeaturesToTargetLayer()


    def copySourceFeaturesToTargetLayer(self):

        self.targetLayer.startEditing()

        sourceCRS = self.sourceLayer.crs()
        targetCRS = self.targetLayer.crs()
        transform = None
        if sourceCRS != targetCRS:
            transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())

        sourceFeatures = self.sourceLayer.getSelectedFeatures()

        targetLayerFeatures = []

        for sourceFeature in sourceFeatures:
            sourceGeom = sourceFeature.geometry()

            if not sourceGeom.isNull() and transform is not None:
                transformedSourceGeom = sourceGeom.transform(transform)
            else:
                transformedSourceGeom = sourceGeom

            targetLayerFeature = QgsFeature()
            targetLayerFeature.setAttribute("uuid", str(uuid.uuid4()))
            targetLayerFeature.setGeometry(transformedSourceGeom)

            self.setTargetFeatureValues(sourceFeature, targetLayerFeature)

            self.handleRegulationInSourceToTargetCopy()

            # TODO yleiskaavaan yhdistäminen, jos asetus "Yhdistä kaavakohteet yleiskaavaan"

            self.handleSpatialPlanRelationInSourceToTargetCopy()

            targetLayerFeatures.append(targetLayerFeature)
        
        # provider.addFeatures(targetLayerFeatures)
        # layer.commitChanges()


    def handleRegulationInSourceToTargetCopy(self):
            # TODO kaavamääräys ja huomioi asetukset "Luo tarvittaessa uudet kaavamääräykset" ja "Täytä kaavakohteiden käyttötarkoitus kaavamääräyksen mukaan"
            # TODO huomioi, että kaavamääräys voi tulla lähteen käyttötarkoituksen kautta (muokkaa myös asetus-dialogia, jotta ko. asia on mahdollista)


    def handleSpatialPlanRelationInSourceToTargetCopy(self):
        pass


    def setTargetFeatureValues(sourceFeature, targetFeature):
        #self.yleiskaavaDatabase.getTargetTableFields(self.targetSchemaTableName)

        fieldMatches = self.getSourceTargetFieldMatches()
        # for fieldMatch in fieldMatches:
        #     targetLayerFeature.setAttribute(fieldMatch["target"], sourceFeature.attribute(fieldMatch["source"]))

        fieldMatchTargetNames = [fieldMatch["target"] for fieldMatch in fieldMatches]

        defaultFieldNameValueTuples = self.getDefaultFieldNameValueTuples()

        for defaultFieldNameValueTuple in defaultFieldNameValueTuples:
            if defaultFieldNameValueTuple["name"] in fieldMatchTargetNames: # Jos käyttäjä täsmännyt lähdekentän ja lähdekentässä on arvo, niin käytä sitä, muuten oletusarvoa, jos käyttäjä antanut sen
                sourceAttribute = None
                for fieldMatch in fieldMatches:
                    if defaultFieldNameValueTuple["name"] == fieldMatch["target"]:
                        sourceAttribute = sourceFeature.attribute(foundFieldMatch["source"])
                        break
                if not sourceAttribute.isNull():
                    targetLayerFeature.setAttribute(fieldMatch["target"], sourceAttribute)
                elif defaultFieldNameValueTuple["value"] is not None:
                    targetLayerFeature.setAttribute(fieldMatch["target"], defaultValue)
            elif defaultFieldNameValueTuple["value"] is not None:
                targetLayerFeature.setAttribute(fieldMatch["target"], defaultValue)
    

    def getDefaultFieldNameValueTuples(self):
        defaultFieldNameValueTuples = []

        for i in range(self.dialogCopySettings.gridLayoutDefaultFieldValues.rowCount()):
            widget = self.dialogCopySettings.gridLayoutDefaultFieldValues.itemAtPosition(i, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).widget()
            text = widget.text()

            userFriendlyTableName = text.split('-')[0][:-1]
            userFriendlytargetFieldName = text.split('-')[1][:1]

            targetSchemaTableName = self.yleiskaavaDatabase.getTableNameForUserFriendlyschemaTableName( userFriendlyTableName)
            targetFieldName = self.yleiskaavaDatabase.getFieldNameForUserFriendlytargetFieldName(userFriendlytargetFieldName)

            targetFieldType = self.yleiskaavaDatabase.getTypeOftargetField(targetFieldName)

            value = self.getValueOfWidgetForTYpe(widget, targetFieldType)

            targetFieldValueTypeWidgetTriple = { "name": targetFieldName, "value": value } #"type": targetFieldType, "widget": widget }
            defaultFieldNameValueTuples.append(targetFieldValueTypeWidgetTriple)

        return defaultFieldNameValueTuples

    def getValueOfWidgetForTYpe(self, widget, targetFieldType):
        if targetFieldType == "String": # QgsFieldValuesLineEdit
            text = widget.text()
            if text == "":
                return None
            else:
                return text
        elif targetFieldType == "Int": # QgsFieldValuesLineEdit
            text = widget.text()
            if text == "":
                return None
            else:
                return int(text)
        elif targetFieldType == "Double": # QgsFieldValuesLineEdit
           text = widget.text()
            if text == "":
                return None
            else:
                return float(text)
        elif targetFieldType == "Date": # QgsDateTimeEdit
            dateValue = widget.date()
            if dateValue.isNull():
                return None
            else:
                return dateValue
        elif targetFieldType == "Bool": # QComboBox
            text = widget.text()
            if text == "":
                return None
            elif text == "Ei":
                return False
            else: # Kyllä
                return True
        else: #elif targetFieldType == "uuid": # QCommboBox
            text = widget.currentText()
            if text == "":
                return None
            else:
                return text


    def getSourceTargetFieldMatches(self):
        fieldMatches = []

        for i in range(self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.rowCount()):
            sourceFieldName = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(i, DataCopySourceToTarget.SOURCE_FIELD_NAME_INDEX).widget().text()
            targetFieldName = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(i, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).widget().text().split(' ')[0]

            if targetFieldName != "":
                fieldMatches.append({"source": sourceFieldName, "target": targetFieldName})
            
            return fieldMatches


