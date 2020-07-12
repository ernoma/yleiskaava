
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

        self.planNumber = None


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
                sourceFieldTypeName = self.yleiskaavaUtils.getStringTypeForFeatureField(field)
                sourceFieldtypeLabel = QLabel(sourceFieldTypeName)
                
                targetTableComboBox = QComboBox()

                # anna valita vain geometrialtaan lähdetason kanssa yhteensopiva kohdetaso
                targetTableNames = sorted(self.yleiskaavaDatabase.getTargetSchemaTableNamesShownInCopySourceToTargetUI(geometry_type = sourceLayer.geometryType()))
                targetTableNames.insert(0, "Valitse kohdekarttataso")

                targetTableComboBox.addItems(targetTableNames)
                self.targetTableComboBoxes.append(targetTableComboBox)
                
                targetFieldNameComboBox = QComboBox()
                self.targetFieldNameComboBoxes.append(targetFieldNameComboBox)
                
                self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.addWidget(sourceFieldnameLabel, index, DataCopySourceToTarget.SOURCE_FIELD_NAME_INDEX, 1, 1)
                self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.addWidget(sourceFieldtypeLabel, index, DataCopySourceToTarget.SOURCE_FIELD_TYPE_NAME_INDEX, 1, 1)
                self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.addWidget(targetTableComboBox, index, DataCopySourceToTarget.TARGET_TABLE_NAME_INDEX, 1, 1)
                self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.addWidget(targetFieldNameComboBox, index, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX, 1, 1)

                targetTableComboBox.currentTextChanged.connect(partial(self.handleTargetTableSelectChanged, index, sourceFieldTypeName, targetTableComboBox, targetFieldNameComboBox))


    def handleTargetTableSelectChanged(self, rowIndex, sourceFieldTypeName, targetTableComboBox, targetFieldNameComboBox):

        # QgsMessageLog.logMessage('handleTargetTableSelectChanged', 'Yleiskaava-työkalu', Qgis.Info)
        self.targetSchemaTableName = self.yleiskaavaDatabase.getTargetSchemaTableNameForUserFriendlyTableName(targetTableComboBox.currentText())
        QgsMessageLog.logMessage('targetTableName: ' + self.targetSchemaTableName + ', rowIndex: ' + str(rowIndex), 'Yleiskaava-työkalu', Qgis.Info)

        if self.targetSchemaTableName != "Valitse kohdekarttataso":
            self.targetLayer = self.yleiskaavaDatabase.createLayerByTargetSchemaTableName(self.targetSchemaTableName)

            #colnames = [desc.name for desc in curs.description]

            # TODO näytä kohdekentissä vain lähdekentän kanssa tyypiltään yhteensopivat kentät

            targetFieldComboBoxTexts = ['']

            for index, field in enumerate(self.targetLayer.fields().toList()):
                targetFieldName = field.name()
                targetFieldTypeName = self.yleiskaavaUtils.getStringTypeForFeatureField(field)
                if self.yleiskaavaUtils.compatibleTypes(sourceFieldTypeName, targetFieldTypeName):
                    targetFieldComboBoxTexts.append(self.getTargetFieldComboBoxText(targetFieldName, targetFieldTypeName))
                    #QgsMessageLog.logMessage(targetFieldNames[index], 'Yleiskaava-työkalu', Qgis.Info)

            targetFieldNameComboBox.clear()
            targetFieldNameComboBox.addItems(targetFieldComboBoxTexts)

            sourceFieldName = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(rowIndex, DataCopySourceToTarget.SOURCE_FIELD_NAME_INDEX).widget().text()
            sourceFieldTypeName = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(rowIndex, DataCopySourceToTarget.SOURCE_FIELD_TYPE_NAME_INDEX).widget().text()

            self.selectBestFittingTargetField(sourceFieldName, sourceFieldTypeName, self.targetLayer.fields(), targetFieldNameComboBox)

            #
            # Helpfully guess values for other widgets
            #
            for index, tempTargetTableComboBox in enumerate(self.targetTableComboBoxes):
                #tempTargetTableName = tempTargetTableComboBox.currentText()
                #if tempTargetTableName == "Valitse kohdekarttataso":
                tempTargetTableComboBox.setCurrentText(self.yleiskaavaDatabase.getUserFriendlyTableNameForTargetSchemaTableName(self.targetSchemaTableName))
                # self.targetFieldNameComboBoxes[index].clear()
                # self.targetFieldNameComboBoxes[index].addItems(targetFieldNames)

                # tempSourceFieldName = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(index, DataCopySourceToTarget.SOURCE_FIELD_NAME_INDEX).widget().text()
                # tempSourceFieldTypeName = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(index, DataCopySourceToTarget.SOURCE_FIELD_TYPE_NAME_INDEX).widget().text()
                # self.selectBestFittingTargetField(tempSourceFieldName, tempSourceFieldTypeName, targetLayer.fields(), self.targetFieldNameComboBoxes[index])
                # self.selectBestFittingTargetField(sourceFieldName, sourceFieldTypeName, targetLayer.fields(),  self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(index, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).widget())
        else:
            targetFieldNameComboBox.clear()


    def getTargetFieldComboBoxText(self, targetFieldName, targetFieldTypeName):
        return '' + targetFieldName + ' (' + targetFieldTypeName + ')'


    def selectBestFittingTargetField(self, sourceFieldName, sourceFieldTypeName, targetFields, targetFieldNameComboBox):
        
        max_levenshtein_ratio = 0

        for index, field in enumerate(targetFields.toList()):
            targetFieldName = field.name()
            targetFieldTypeName = self.yleiskaavaUtils.getStringTypeForFeatureField(field)
            targetFieldComboBoxText = self.getTargetFieldComboBoxText(targetFieldName, targetFieldTypeName)

            levenshtein_ratio = self.yleiskaavaUtils.levenshteinRatioAndDistance(sourceFieldName.lower(), targetFieldName)

            if sourceFieldName.lower() == targetFieldName and sourceFieldTypeName == targetFieldTypeName:
                targetFieldNameComboBox.setCurrentText(targetFieldComboBoxText)
                QgsMessageLog.logMessage('foundMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
                break
            elif sourceFieldName.lower() == targetFieldName and sourceFieldName.lower() != 'id':
                targetFieldNameComboBox.setCurrentText(targetFieldComboBoxText)
                QgsMessageLog.logMessage('foundMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
                break # should not be possible to have many cols with the same name
            elif sourceFieldName.lower() != 'id' and targetFieldTypeName != 'uuid' and levenshtein_ratio > max_levenshtein_ratio and levenshtein_ratio > 0.5:
                #QgsMessageLog.logMessage('Levenshtein_ratio : ' + str(levenshtein_ratio), 'Yleiskaava-työkalu', Qgis.Info)
                max_levenshtein_ratio = levenshtein_ratio
                targetFieldNameComboBox.setCurrentText(targetFieldComboBoxText)
                QgsMessageLog.logMessage('foundLevenshtein_ratioMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
            elif (sourceFieldName.lower() in targetFieldName or targetFieldName in sourceFieldName.lower()) and sourceFieldName.lower() != 'id' and targetFieldTypeName != 'uuid':
                #foundMatch = True
                targetFieldNameComboBox.setCurrentText(targetFieldComboBoxText)
                QgsMessageLog.logMessage('foundPartialNameMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
            # elif sourceFieldTypeName == targetFieldTypeName and not foundMatch:
            #     foundMatch = True
            #     targetFieldNameComboBox.setCurrentText(targetFieldComboBoxText)
            #     QgsMessageLog.logMessage('foundTypeMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)


    def checkThatCopyCanBeDone(self):
        # TODO

        # varmista, että self.targetSchemaTableName != None ja tarvittaessa ilmoita käyttäjälle
        if self.targetTableNotSelected():
            pass

        # varmista, että kukin kohdekenttä on mahdollista valita vain kerran
        fieldName = self.getTargetFieldSelectedMoreThanOneTime()
        if fieldName != None:
            pass

    
    def targetTableNotSelected(self):
        if self.targetSchemaTableName == None:
            return True
        else:
            return False


    def getTargetFieldSelectedMoreThanOneTime(self):
        targetFieldNames = []

        for i in range(self.getGridLayoutSourceTargetMatchRowCount()):
            QgsMessageLog.logMessage("rowCount: " + str(self.getGridLayoutSourceTargetMatchRowCount()) + ", i: " + str(i), 'Yleiskaava-työkalu', Qgis.Info)

            targetFieldName = None
            targetFieldTypeName = None
            text = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(i, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).widget().currentText()
            if text != '':
                targetFieldName, targetFieldTypeName = text.split(' ')
                targetFieldTypeName = targetFieldTypeName[1:-1]

            if targetFieldName in targetFieldNames:
                return targetFieldName
            else:
                targetFieldNames.append(targetFieldName)

        return None


    def chooseSourceFeatures(self):
        # varmista, että self.targetSchemaTableName != None ja tarvittaessa ilmoita käyttäjälle
        if self.targetTableNotSelected():
            self.iface.messageBar().pushMessage('Kopioinnin kohdekarttatasoa ei valittu', Qgis.Warning, duration=10)

        # varmista, että kukin kohdekenttä on mahdollista valita vain kerran
        fieldName = self.getTargetFieldSelectedMoreThanOneTime()
        if fieldName != None:
            self.iface.messageBar().pushMessage('Sama kohdekenttä valittu usealla lähdekentälle: ' + fieldName, Qgis.Warning, duration=10)

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

        # jos "Luo tarvittaessa uudet kaavamääräykset" / "Täytä kaavakohteiden käyttötarkoitus kaavamääräyksen mukaan tai päinvastoin" eivät relevantteja lähdeaineiston täysmäysten perusteella, niin näytä ko. elementit dialogissa disabloituna ja ilman valintaa
        if not self.targetFieldsHaveRegulation() and not self.targetFieldsHaveLandUseClassification():
            self.dialogCopySettings.checkBoxCreateRegulations.setChecked(False)
            self.dialogCopySettings.checkBoxCreateRegulations.setEnabled(False)
        else:
            self.dialogCopySettings.checkBoxCreateRegulations.setChecked(True)
            self.dialogCopySettings.checkBoxCreateRegulations.setEnabled(True)
        # Huomioi, että jos käyttötarkoitus ja kaavamääräys molemmat lähdekohde-matchissä tai ei kumpaakaan, niin ei ruksia asetusdialogissa "Täytä kaavakohteiden käyttötarkoitus kaavamääräyksen mukaan tai päinvastoin"-kohtaan
        if (not self.targetFieldsHaveRegulation() and not self.targetFieldsHaveLandUseClassification()) or (self.targetFieldsHaveRegulation() and self.targetFieldsHaveLandUseClassification()):
            self.dialogCopySettings.checkBoxFillLandUseClassificationWithRegulation.setChecked(False)
            self.dialogCopySettings.checkBoxFillLandUseClassificationWithRegulation.setEnabled(False)
        else:
            self.dialogCopySettings.checkBoxFillLandUseClassificationWithRegulation.setChecked(True)
            self.dialogCopySettings.checkBoxFillLandUseClassificationWithRegulation.setEnabled(True)
            


        self.initializeDialogCopySettingsPlanPart()

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
        

    def initializeDialogCopySettingsPlanPart(self):

        # hae kaikki yleiskaavataulun yleiskaavojen nimet, täytä comboBoxSpatialPlanName ja valitse tyypillisin nimi
        plans = self.yleiskaavaDatabase.getSpatialPlans()

        planNames = [plan["nimi"] for plan in plans]

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
        if len(planNamesOrdered) > 0:
            self.dialogCopySettings.comboBoxLevelOfSpatialPlan.setCurrentText(self.yleiskaavaDatabase.getYleiskaavaPlanLevelCodeWithPlanName(self.dialogCopySettings.comboBoxSpatialPlanName.currentText()))

        self.dialogCopySettings.comboBoxSpatialPlanName.currentTextChanged.connect(self.comboBoxSpatialPlanNameCurrentTextChanged)
        #self.dialogCopySettings.comboBoxSpatialPlanName.currentTextChanged.connect(self.comboBoxSpatialPlanName)

        # disabloi ja ruksi pois self.dialogCopySettings.checkBoxLinkToSpatialPlan, jos ei kaavoja
        if len(planNames) == 0:
            self.dialogCopySettings.checkBoxLinkToSpatialPlan.setChecked(False)
            self.dialogCopySettings.checkBoxLinkToSpatialPlan.setEnabled(False)
            self.dialogCopySettings.comboBoxSpatialPlanName.setEnabled(False)
            #self.dialogCopySettings.comboBoxLevelOfSpatialPlan.setEnabled(False)
        else:
            self.dialogCopySettings.checkBoxLinkToSpatialPlan.setChecked(True)
            self.dialogCopySettings.checkBoxLinkToSpatialPlan.setEnabled(True)
            self.dialogCopySettings.comboBoxSpatialPlanName.setEnabled(True)
            #self.dialogCopySettings.comboBoxLevelOfSpatialPlan.setEnabled(True)

        # lisää signaali self.dialogCopySettings.checkBoxLinkToSpatialPlan checked muutokselle 
        self.dialogCopySettings.checkBoxLinkToSpatialPlan.stateChanged.connect(self.checkBoxLinkToSpatialPlanStateChanged)


    #def comboBoxLevelOfSpatialPlanCurrentTextChanged(self):
    def comboBoxSpatialPlanNameCurrentTextChanged(self):
        self.dialogCopySettings.comboBoxLevelOfSpatialPlan.setCurrentText(self.yleiskaavaDatabase.getYleiskaavaPlanLevelCodeWithPlanName(self.dialogCopySettings.comboBoxSpatialPlanName.currentText()))


    def checkBoxLinkToSpatialPlanStateChanged(self):
        if self.dialogCopySettings.checkBoxLinkToSpatialPlan.isChecked():
            self.dialogCopySettings.comboBoxSpatialPlanName.setEnabled(True)
        else:
            self.dialogCopySettings.comboBoxSpatialPlanName.setEnabled(False)


    def getChosenTargetFieldNames(self):
        # hae valittujen kohdekenttien nimet dialogin gridistä
        names = []
        for i in range(self.getGridLayoutSourceTargetMatchRowCount()):
            name = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(i, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).widget().currentText()
            if len(name) > 0:
                names.append(name.split(' ')[0]) # Remove type and append
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

            if targetFieldTypeName == 'String' or targetFieldTypeName == 'Int' or targetFieldTypeName == 'Double' or targetFieldTypeName == 'LongLong':
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

        # TODO päivitä lopuksi työtilan karttatasot, jotka liittyvät T1:n ajoon


    def copySourceFeaturesToTargetLayer(self):

        self.planNumber = self.yleiskaavaDatabase.getPlanNumberForName(self.getPlanNameFromCopySettings())

        # self.targetLayer.startEditing()

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
            targetLayerFeature.setAttribute("id", str(uuid.uuid4()))
            targetLayerFeature.setGeometry(transformedSourceGeom)

            self.setTargetFeatureValues(sourceFeature, targetLayerFeature)

            self.handleRegulationInSourceToTargetCopy(sourceFeature, targetLayerFeature)

            self.handleSpatialPlanRelationInSourceToTargetCopy(targetLayerFeature)

            targetLayerFeatures.append(targetLayerFeature)
        
        # provider = self.targetLayer.dataProvider()
        # provider.addFeatures(targetLayerFeatures)
        # self.targetLayer.commitChanges()

    def getPlanNameFromCopySettings(self):
        return self.dialogCopySettings.comboBoxSpatialPlanName.currentText()


    def handleRegulationInSourceToTargetCopy(self, sourceFeature, targetFeature):
        # Tee tarvittaessa linkki olemassa olevaan tai uuteen kaavamääräykseen. Huomioi asetukset "Luo tarvittaessa uudet kaavamääräykset" ja "Täytä kaavakohteiden käyttötarkoitus kaavamääräyksen mukaan tai päinvastoin"
        # Huomioi, että kaavamääräys voi tulla lähteen käyttötarkoituksen kautta (muokkaa myös asetus-dialogia, jotta ko. asia on mahdollista)
        # muuttaa lähdekaavamääräyksen isoihin kirjaimiin, jos ei ole valmiiksi
        # TODO huomioi, että kaavamääräys ja/tai käyttötarkoitus ovat voineet tulla oletusarvojen kautta

        fieldMatches = self.getSourceTargetFieldMatches()
        fieldMatchTargetNames = [fieldMatch["target"] for fieldMatch in fieldMatches]

        if "kaavamaaraysotsikko" in fieldMatchTargetNames:
            sourceRegulationName = self.getSourceFeatureValueForSourceTargetFieldMatch(fieldMatches, sourceFeature, "kaavamaaraysotsikko").toupper()

            if sourceRegulationName != "":
                regulationList = self.yleiskaavaDatabase.getSpecificRegulations(upperCase=True)
                regulationNames = [regulation["kaavamaarays_otsikko"] for regulation in regulationList]

                if sourceRegulationName in regulationNames:
                    self.yleiskaavaDatabase.createFeatureRegulationRelation(self.targetSchemaTableName, targetFeature.attribute["id"], sourceRegulationName)
                elif self.shouldCreateNewRegulation(): # uusi otsikko & kaavamääräys (tai muuten virhe otsikon oikeinkirjoituksessa, tms)
                    self.yleiskaavaDatabase.createSpecificRegulationAndFeatureRegulationRelation(self.targetSchemaTableName, targetFeature.attribute["id"], sourceRegulationName)

                if self.shouldFillLandUseClassificationWithRegulation():
                    self.fillLandUseClassificationWithRegulation(sourceRegulationName, targetFeature)

        elif "kayttotarkoitus_lyhenne" in fieldMatchTargetNames:
            sourceLandUseClassificationName = self.getSourceFeatureValueForSourceTargetFieldMatch(fieldMatches, sourceFeature, "kayttotarkoitus_lyhenne").toupper()

            if sourceLandUseClassificationName != "":

                regulationName = self.yleiskaavaUtils.getRegulationNameForLandUseClassification(self.planNumber, targetSchemaTableName, sourceLandUseClassificationName)

                regulationList = self.yleiskaavaDatabase.getSpecificRegulations(upperCase=True)
                regulationNames = [regulation["kaavamaarays_otsikko"] for regulation in regulationList]

                if regulationName in regulationNames:
                    self.yleiskaavaDatabase.createFeatureRegulationRelation(self.targetSchemaTableName, targetFeature.attribute["id"], regulationName)
                elif self.shouldCreateNewRegulation(): # uusi otsikko & kaavamääräys (tai muuten virhe otsikon oikeinkirjoituksessa, tms)
                    self.yleiskaavaDatabase.createSpecificRegulationAndFeatureRegulationRelation(self.targetSchemaTableName, targetFeature.attribute["id"], regulationName)

                if self.shouldFillLandUseClassificationWithRegulation():
                    self.fillRegulationWithLandUseClassification(sourceLandUseClassificationName, targetFeature)


    def fillRegulationWithLandUseClassification(self, landUseClassificationName, targetFeature):
        regulationName = self.yleiskaavaUtils.getRegulationNameForLandUseClassification(self.planNumber, targetSchemaTableName, sourceLandUseClassificationName)

        targetFeature.setAttribute("kaavamaaraysotsikko", regulationName)

    
    def fillLandUseClassificationWithRegulation(self, sourceRegulationName, targetFeature):
        landUseClassificationName = self.yleiskaavaUtils.getLandUseClassificationNameForRegulation(self.planNumber, targetSchemaTableName, sourceRegulationName)

        targetFeature.setAttribute("kayttotarkoitus_lyhenne", landUseClassificationName)


    def shouldCreateNewRegulation(self):
        return self.dialogCopySourceDataToDatabase.checkBoxCreateRegulations.isChecked()


    def shouldFillLandUseClassificationWithRegulation(self):
        return self.dialogCopySourceDataToDatabase.checkBoxFillLandUseClassificationWithRegulation.isChecked()

    def getSourceFeatureValueForSourceTargetFieldMatch(self, fieldMatches, sourceFeature, targetFieldName):
        value = ""

        for fieldMatch in fieldMatches:
            if targetFieldName == fieldMatch["target"]:
                value = sourceFeature.attribute(fieldMatch["source"])
                break
        return value


    def handleSpatialPlanRelationInSourceToTargetCopy(self, targetFeature):
        # yleiskaavaan yhdistäminen, jos asetus "Yhdistä kaavakohteet yleiskaavaan"

        if self.dialogCopySettings.checkBoxLinkToSpatialPlan.isChecked():
            spatialPlanID = self.yleiskaavaDatabase.getSpatialPlanIDForPlanName(self.dialogCopySettings.comboBoxSpatialPlanName.currentText())
            if spatialPlanID != None:
                targetFeature.settAttribute("id_yleiskaava", spatialPlanID)


    def setTargetFeatureValues(sourceFeature, targetFeature):
        # tarvittaessa tehdään muunnos esim. int -> string kopioinnissa

        fieldMatches = self.getSourceTargetFieldMatches()
        fieldMatchTargetNames = [fieldMatch["target"] for fieldMatch in fieldMatches]

        defaultTargetFieldInfos = self.getDefaultTargetFieldInfo()

        for defaultTargetFieldInfo in defaultTargetFieldInfos:
            if defaultTargetFieldInfo["name"] in fieldMatchTargetNames: # Jos käyttäjä täsmännyt lähdekentän ja lähdekentässä on arvo, niin käytä sitä, muuten oletusarvoa, jos käyttäjä antanut sen
                sourceAttribute = None
                sourceFieldTypeName = None
                targetFieldTypeName = None
                for fieldMatch in fieldMatches:
                    if defaultTargetFieldInfo["name"] == fieldMatch["target"]:
                        sourceAttribute = sourceFeature.attribute(fieldMatch["source"])
                        sourceFieldTypeName = fieldMatch["sourceFieldTypeName"]
                        targetFieldTypeName = fieldMatch["targetFieldTypeName"]
                        break
                if not sourceAttribute.isNull():
                    attrValue = self.yleiskaavaUtils.getAttributeValueInCompatibleType(targetFieldTypeName, sourceFieldTypeName, sourceAttribute)
                    targetLayerFeature.setAttribute(fieldMatch["target"], attrValue)
                elif defaultTargetFieldInfo["value"] is not None:
                    targetLayerFeature.setAttribute(fieldMatch["target"], defaultTargetFieldInfo["value"])
            elif defaultTargetFieldInfo["value"] is not None:
                targetLayerFeature.setAttribute(fieldMatch["target"], defaultTargetFieldInfo["value"])
    

    def getDefaultTargetFieldInfo(self):
        defaultFieldNameValueInfos = []

        for i in range(self.dialogCopySettings.gridLayoutDefaultFieldValues.rowCount()):
            widget = self.dialogCopySettings.gridLayoutDefaultFieldValues.itemAtPosition(i, DataCopySourceToTarget.DEFAULT_VALUES_GRID_INPUT_INDEX).widget()
            text = widget.text()

            userFriendlyTableName = text.split('-')[0][:-1]
            userFriendlytargetFieldName = text.split('-')[1][:1]

            targetSchemaTableName = self.yleiskaavaDatabase.getTableNameForUserFriendlyschemaTableName( userFriendlyTableName)
            targetFieldName = self.yleiskaavaDatabase.getFieldNameForUserFriendlytargetFieldName(userFriendlytargetFieldName)

            targetFieldType = self.yleiskaavaDatabase.getTypeOftargetField(targetFieldName)

            value = self.getValueOfWidgetForTYpe(widget, targetFieldType)

            targetFieldInfo = { "name": targetFieldName, "value": value, "type": targetFieldType, "widget": widget }
            defaultFieldNameValueInfos.append(targetFieldInfo)

        return defaultFieldNameValueInfos


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
        elif targetFieldType == "LongLong": # QgsFieldValuesLineEdit
            text = widget.text()
            if text == "":
                return None
            else:
                return int(text)
        elif targetFieldType == "Date": # QgsDateTimeEdit
            dateValue = widget.date()
            if dateValue.isNull():
                return None
            else:
                return dateValue
        elif targetFieldType == "Bool": # QComboBox
            text = widget.currentText()
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

        for i in range(self.getGridLayoutSourceTargetMatchRowCount()):
            sourceFieldName = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(i, DataCopySourceToTarget.SOURCE_FIELD_NAME_INDEX).widget().text()
            sourceFieldTypeName = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(i, DataCopySourceToTarget.SOURCE_FIELD_TYPE_INDEX).widget().text()
            
            targetFieldName = None
            targetFieldTypeName = None
            text = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(i, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).widget().currentText()
            if text != '':
                targetFieldName, targetFieldTypeName = text.split(' ')
                targetFieldTypeName = targetFieldTypeName[1:-1]

            if targetFieldName != None:
                fieldMatches.append({ "source": sourceFieldName, "sourceFieldTypeName": sourceFieldTypeName, "target": targetFieldName, "targetFieldTypeName": targetFieldTypeName })
            
            return fieldMatches


    def targetFieldsHaveRegulation(self):
        for i in range(self.getGridLayoutSourceTargetMatchRowCount()):
            targetFieldName = None
            targetFieldTypeName = None
            text = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(i, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).widget().currentText()
            if text != '':
                targetFieldName, targetFieldTypeName = text.split(' ')
                targetFieldTypeName = targetFieldTypeName[1:-1]

            if targetFieldName == 'kaavamaaraysotsikko':
                return True

        return False


    def targetFieldsHaveLandUseClassification(self):
        for i in range(self.getGridLayoutSourceTargetMatchRowCount()):
            targetFieldName = None
            targetFieldTypeName = None
            text = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(i, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).widget().currentText()
            if text != '':
                targetFieldName, targetFieldTypeName = text.split(' ')
                targetFieldTypeName = targetFieldTypeName[1:-1]

            if targetFieldName == 'kayttotarkoitus_lyhenne':
                return True

        return False


    def getGridLayoutSourceTargetMatchRowCount(self):
        count = 0
        for index, field in enumerate(self.sourceLayer.fields().toList()):
            if field.name() != 'id' and self.yleiskaavaUtils.getStringTypeForFeatureField(field) != 'uuid':
                count += 1

        return count
