
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QVariant, QSize
from qgis.PyQt.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox, QCheckBox

from qgis.core import (
    Qgis, QgsProject, QgsFeature, QgsWkbTypes, QgsMessageLog, QgsMapLayer,  QgsMapLayerProxyModel, QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsTask, QgsApplication)

from qgis.gui import QgsFilterLineEdit, QgsDateTimeEdit, QgsMessageBarItem

import os.path
from functools import partial
from operator import itemgetter
from collections import Counter
import uuid


# from .yleiskaava_dialog_copy_source_data_to_database import Ui_DialogCopySourceDataToDatabase
from .yleiskaava_copy_source_data_to_database_task import CopySourceDataToDatabaseTask
from .yleiskaava_utils import COPY_ERROR_REASONS
from .yleiskaava_database import YleiskaavaDatabase

class DataCopySourceToTarget:
    
    SOURCE_FIELD_NAME_INDEX = 0
    SOURCE_FIELD_TYPE_NAME_INDEX = 1
    TARGET_TABLE_NAME_INDEX = 2
    TARGET_TABLE_FIELD_NAME_INDEX = 3

    DEFAULT_VALUES_LABEL_INDEX = 0
    DEFAULT_VALUES_INPUT_INDEX = 1

    OBJECT_NAME_UNIQUE_IDENTIFIERS = {
        "SOURCE_FIELD_NAME": "sn",
        "SOURCE_FIELD_TYPE_NAME":"st",
        "TARGET_TABLE_NAME": "ttn",
        "TARGET_TABLE_FIELD_NAME": "tfn",
        "DEFAULT_VALUES_LABEL": "dl",
        "DEFAULT_VALUES_INPUT": "di"
    }

    SETTINGS_DIALOG_MIN_WIDTH = 1068
    SETTINGS_DIALOG_MIN_HEIGHT = 1182

    COPY_SOURCE_DATA_DIALOG_MIN_WIDTH = 1006
    COPY_SOURCE_DATA_DIALOG_MIN_HEIGHT = 624


    def __init__(self, iface, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = os.path.dirname(__file__)

        self.dialogCopySourceDataToDatabase = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_copy_source_data_to_database.ui'))
        self.dialogCopySourceDataToDatabase.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)

        # self.dialogCopySourceDataToDatabase = Ui_DialogCopySourceDataToDatabase()
        # self.dialogCopySourceDataToDatabaseWidget = QWidget()
        # self.dialogCopySourceDataToDatabase.setupUi(self.dialogCopySourceDataToDatabaseWidget)

        self.dialogChooseFeatures = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_choose_features.ui'))
        self.dialogChooseFeatures.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)

        self.dialogCopySettings = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_copy_settings.ui'))
        self.dialogCopySettings.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)

        self.dialogChooseRegulation = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_choose_regulation.ui'))
        self.dialogChooseRegulation.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)

        self.dialogCopyMessage = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_copy_message.ui'))
        self.dialogCopyMessage.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)

        self.sourceLayer = None

        self.targetSchemaTableName = None
        self.targetLayer = None

        self.targetTableComboBoxes = []
        self.targetFieldNameComboBoxes = []

        # Kaavamääräysdialogia varten:
        self.regulations = None
        self.currentRegulation = None
        self.regulationTitles = None
        self.includeAreaRegulations = False
        self.includeSuplementaryAreaRegulations = False
        self.includeLineRegulations = False
        self.includePointRegulations = False

        self.copyMessageBarItem = None


    def setup(self):
        self.setupDialogCopySourceDataToDatabase()
        self.setupDialogChooseFeatures()
        self.setupDialogCopySettings()
        self.setupDialogChooseRegulation()
        self.setupDialogCopyMessage()


    def setupDialogCopyMessage(self):
        self.dialogCopyMessage.labelWarning.setStyleSheet("color: rgb(204, 51, 0);")
        self.dialogCopyMessage.pushButtonClose.clicked.connect(self.dialogCopyMessage.hide)


    def setupDialogCopySourceDataToDatabase(self):
        self.dialogCopySourceDataToDatabase.pushButtonCancel.clicked.connect(self.hideAllDialogs)
        self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.layerChanged.connect(self.handleMapLayerComboBoxSourceChanged)
        self.dialogCopySourceDataToDatabase.pushButtonNext.clicked.connect(self.chooseSourceFeatures)


    def setupDialogChooseFeatures(self):
        self.dialogChooseFeatures.pushButtonCancel.clicked.connect(self.hideAllDialogs)
        self.dialogChooseFeatures.pushButtonPrevious.clicked.connect(self.showDialogCopySourceDataToDatabase)
        self.dialogChooseFeatures.pushButtonNext.clicked.connect(self.chooseCopySettings)


    def setupDialogCopySettings(self):

        self.dialogCopySettings.pushButtonChooseExistingRegulationForDefault.clicked.connect(self.pushButtonChooseExistingRegulationForDefaultClicked)

        self.dialogCopySettings.comboBoxSpatialPlanName.currentTextChanged.connect(self.comboBoxSpatialPlanNameCurrentTextChanged)
        #self.dialogCopySettings.comboBoxSpatialPlanName.currentTextChanged.connect(self.comboBoxSpatialPlanName)
        # lisää signaali self.dialogCopySettings.checkBoxLinkToSpatialPlan checked muutokselle 
        self.dialogCopySettings.checkBoxLinkToSpatialPlan.stateChanged.connect(self.checkBoxLinkToSpatialPlanStateChanged)

        self.dialogCopySettings.pushButtonCancel.clicked.connect(self.hideAllDialogs)
        self.dialogCopySettings.pushButtonPrevious.clicked.connect(self.chooseSourceFeatures)
        self.dialogCopySettings.pushButtonRun.clicked.connect(self.runCopySourceDataToDatabase)


    def setupDialogChooseRegulation(self):
        self.dialogChooseRegulation.comboBoxRegulationTitles.currentIndexChanged.connect(self.handleComboBoxRegulationTitleChanged)

        self.dialogChooseRegulation.checkBoxShowOnlyUsedRegulations.stateChanged.connect(self.checkBoxShowOnlyUsedRegulationsStateChanged)

        self.dialogChooseRegulation.pushButtonAccept.clicked.connect(self.handleDialogChooseRegulationAccept)
        self.dialogChooseRegulation.pushButtonCancel.clicked.connect(self.dialogChooseRegulation.hide)


    def hideAllDialogs(self):
        self.dialogCopySourceDataToDatabase.hide()
        self.dialogChooseFeatures.hide()
        self.dialogCopySettings.hide()
        self.dialogChooseRegulation.hide()
        self.dialogCopyMessage.hide()


    def openDialogCopySourceDataToDatabase(self):
        self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.setFilters(QgsMapLayerProxyModel.HasGeometry)
        self.dialogCopySourceDataToDatabase.resize(QSize(DataCopySourceToTarget.COPY_SOURCE_DATA_DIALOG_MIN_WIDTH, DataCopySourceToTarget.COPY_SOURCE_DATA_DIALOG_MIN_HEIGHT))
        self.dialogCopySourceDataToDatabase.show()
        self.sourceLayer = self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.currentLayer()
        if self.sourceLayer is not None:
            # QgsMessageLog.logMessage(layer.name(), 'Yleiskaava-työkalu', Qgis.Info)
            self.updateUIBasedOnSourceLayer(self.sourceLayer)


    def showDialogCopySourceDataToDatabase(self):
        #self.dialogCopySourceDataToDatabase.hide()
        self.dialogChooseFeatures.hide()
        self.dialogCopySettings.hide()
        self.dialogCopySourceDataToDatabase.resize(QSize(DataCopySourceToTarget.COPY_SOURCE_DATA_DIALOG_MIN_WIDTH, DataCopySourceToTarget.COPY_SOURCE_DATA_DIALOG_MIN_HEIGHT))
        self.dialogCopySourceDataToDatabase.show()


    def handleMapLayerComboBoxSourceChanged(self, layer):
        if layer is not None:
            # QgsMessageLog.logMessage(layer.name(), 'Yleiskaava-työkalu', Qgis.Info)
            self.sourceLayer = layer
            self.updateUIBasedOnSourceLayer(self.sourceLayer)
            
            geomType = self.sourceLayer.geometryType()

            if geomType == QgsWkbTypes.PointGeometry:
                self.selectTargetLayer(YleiskaavaDatabase.KAAVAOBJEKTI_PISTE)
            elif geomType == QgsWkbTypes.LineGeometry:
                self.selectTargetLayer(YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA)
        

    def selectTargetLayer(self, layerName):
        widget = self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.cellWidget(0, DataCopySourceToTarget.TARGET_TABLE_NAME_INDEX)
        if widget != None:
            widget.setCurrentIndex(1)


    def updateUIBasedOnSourceLayer(self, sourceLayer):
        if sourceLayer is not None:
            self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.clearContents()
            self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.setRowCount(self.getSourceTargetMatchRowCount())
            self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.setColumnCount(4)
            self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.setHorizontalHeaderLabels([
                "Lähdekenttä",
                "Lähdetietotyyppi",
                "Kohdekarttataso (kaavaobjekti)",
                "Kohdekarttatason kenttä"
            ])

            self.targetTableComboBoxes = []
            self.targetFieldNameComboBoxes = []


            index = 0
            for field in sourceLayer.fields().toList():
                if field.name() != 'id' and self.yleiskaavaUtils.getStringTypeForFeatureField(field) != 'uuid':
                    sourceFieldnameLabel = QLabel(field.name())
                    sourceFieldnameLabel.setObjectName(DataCopySourceToTarget.OBJECT_NAME_UNIQUE_IDENTIFIERS["SOURCE_FIELD_NAME"] + str(index))
                    sourceFieldTypeName = self.yleiskaavaUtils.getStringTypeForFeatureField(field)
                    sourceFieldtypeLabel = QLabel(sourceFieldTypeName)
                    sourceFieldtypeLabel.setObjectName(DataCopySourceToTarget.OBJECT_NAME_UNIQUE_IDENTIFIERS["SOURCE_FIELD_TYPE_NAME"] + str(index))
                    
                    targetTableComboBox = QComboBox()
                    targetTableComboBox.setObjectName(DataCopySourceToTarget.OBJECT_NAME_UNIQUE_IDENTIFIERS["TARGET_TABLE_NAME"] + str(index))

                    # anna valita vain geometrialtaan lähdetason kanssa yhteensopiva kohdetaso
                    targetTableNames = sorted(self.yleiskaavaDatabase.getTargetSchemaTableNamesShownInCopySourceToTargetUI(geometry_type = sourceLayer.geometryType()))
                    targetTableNames.insert(0, "Valitse kohdekarttataso")

                    targetTableComboBox.addItems(targetTableNames)
                    self.targetTableComboBoxes.append(targetTableComboBox)
                    
                    targetFieldNameComboBox = QComboBox()
                    targetFieldNameComboBox.setObjectName(DataCopySourceToTarget.OBJECT_NAME_UNIQUE_IDENTIFIERS["TARGET_TABLE_FIELD_NAME"] + str(index))
                    self.targetFieldNameComboBoxes.append(targetFieldNameComboBox)
                    
                    self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.setCellWidget(index, DataCopySourceToTarget.SOURCE_FIELD_NAME_INDEX, sourceFieldnameLabel)
                    self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.setCellWidget(index, DataCopySourceToTarget.SOURCE_FIELD_TYPE_NAME_INDEX, sourceFieldtypeLabel)
                    self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.setCellWidget(index, DataCopySourceToTarget.TARGET_TABLE_NAME_INDEX, targetTableComboBox)
                    self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.setCellWidget(index, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX, targetFieldNameComboBox)

                    targetTableComboBox.currentTextChanged.connect(partial(self.handleTargetTableSelectChanged, index, sourceFieldTypeName, targetTableComboBox, targetFieldNameComboBox))

                    index += 1

            self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.resizeColumnsToContents()


    def handleTargetTableSelectChanged(self, rowIndex, sourceFieldTypeName, targetTableComboBox, targetFieldNameComboBox):

        text = targetTableComboBox.currentText()
        if text != "Valitse kohdekarttataso":

            # QgsMessageLog.logMessage('handleTargetTableSelectChanged', 'Yleiskaava-työkalu', Qgis.Info)
            self.targetSchemaTableName = self.yleiskaavaDatabase.getTargetSchemaTableNameForUserFriendlyTableName(text)
            # QgsMessageLog.logMessage('handleTargetTableSelectChanged - targetTableName: ' + self.targetSchemaTableName + ', rowIndex: ' + str(rowIndex), 'Yleiskaava-työkalu', Qgis.Info)

            if self.targetSchemaTableName is not None:
                self.targetLayer = self.yleiskaavaDatabase.getProjectLayer(self.targetSchemaTableName)

                #colnames = [desc.name for desc in curs.description]

                # näytä kohdekentissä vain lähdekentän kanssa tyypiltään yhteensopivat kentät

                targetFieldComboBoxTexts = ['']

                # QgsMessageLog.logMessage('handleTargetTableSelectChanged - self.targetLayer.name(): ' + self.targetLayer.name() + ', rowIndex: ' + str(rowIndex), 'Yleiskaava-työkalu', Qgis.Info)

                for index, field in enumerate(self.targetLayer.fields().toList()):
                    targetFieldName = field.name()
                    targetFieldTypeName = self.yleiskaavaUtils.getStringTypeForFeatureField(field)
                    if self.yleiskaavaUtils.compatibleTypes(sourceFieldTypeName, targetFieldTypeName) and self.yleiskaavaUtils.isShownTargetFieldName(targetFieldName):
                        targetFieldComboBoxTexts.append(self.getTargetFieldComboBoxText(targetFieldName, targetFieldTypeName))
                        #QgsMessageLog.logMessage(targetFieldNames[index], 'Yleiskaava-työkalu', Qgis.Info)

                targetFieldNameComboBox.clear()
                targetFieldNameComboBox.addItems(targetFieldComboBoxTexts)

                sourceFieldName = self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.cellWidget(rowIndex, DataCopySourceToTarget.SOURCE_FIELD_NAME_INDEX).text()
                sourceFieldTypeName = self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.cellWidget(rowIndex, DataCopySourceToTarget.SOURCE_FIELD_TYPE_NAME_INDEX).text()

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
        userFriendlyFieldName = self.yleiskaavaDatabase.getUserFriendlytargetFieldName(targetFieldName)
        return '' + userFriendlyFieldName + ' (' + targetFieldName + ', ' + targetFieldTypeName + ')'


    def getTargetFieldNameAndTypeFromComboBoxText(self, text):
        # QgsMessageLog.logMessage('getTargetFieldNameAndTypeFromComboBoxText, text: ' + str(text), 'Yleiskaava-työkalu', Qgis.Info)
        userFriendlyFieldName, targetFieldNameAndTypeName = text.rsplit(' (', 1)
        targetFieldName, targetFieldTypeName = targetFieldNameAndTypeName[0:-1].split(', ')
        return userFriendlyFieldName, targetFieldName, targetFieldTypeName


    def selectBestFittingTargetField(self, sourceFieldName, sourceFieldTypeName, targetFields, targetFieldNameComboBox):
        
        max_levenshtein_ratio = 0

        if sourceFieldName == 'Yleisk_nro':
            targetFieldNameComboBox.setCurrentText('')
            return
        elif sourceFieldName.lower().startswith('luok'):
            targetFieldComboBoxText = self.getTargetFieldComboBoxText('luokittelu', 'String')
            targetFieldNameComboBox.setCurrentText(targetFieldComboBoxText)
            return
        elif sourceFieldName.lower().startswith('tuont'):
            targetFieldComboBoxText = self.getTargetFieldComboBoxText('aineisto_lisatieto', 'String')
            targetFieldNameComboBox.setCurrentText(targetFieldComboBoxText)
            return


        for index, field in enumerate(targetFields.toList()):
            targetFieldName = field.name()
            targetFieldTypeName = self.yleiskaavaUtils.getStringTypeForFeatureField(field)
            targetFieldComboBoxText = self.getTargetFieldComboBoxText(targetFieldName, targetFieldTypeName)

            levenshtein_ratio = self.yleiskaavaUtils.levenshteinRatioAndDistance(sourceFieldName.lower(), targetFieldName)

            if sourceFieldName.lower() == targetFieldName and sourceFieldTypeName == targetFieldTypeName:
                targetFieldNameComboBox.setCurrentText(targetFieldComboBoxText)
                # QgsMessageLog.logMessage('foundMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
                break
            elif sourceFieldName.lower() == targetFieldName and sourceFieldName.lower() != 'id':
                targetFieldNameComboBox.setCurrentText(targetFieldComboBoxText)
                # QgsMessageLog.logMessage('foundMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
                break # should not be possible to have many cols with the same name
            elif sourceFieldName.lower() != 'id' and targetFieldTypeName != 'uuid' and levenshtein_ratio > max_levenshtein_ratio and levenshtein_ratio > 0.5:
                #QgsMessageLog.logMessage('Levenshtein_ratio : ' + str(levenshtein_ratio), 'Yleiskaava-työkalu', Qgis.Info)
                max_levenshtein_ratio = levenshtein_ratio
                targetFieldNameComboBox.setCurrentText(targetFieldComboBoxText)
                # QgsMessageLog.logMessage('foundLevenshtein_ratioMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
            elif (sourceFieldName.lower() in targetFieldName or targetFieldName in sourceFieldName.lower()) and sourceFieldName.lower() != 'id' and targetFieldTypeName != 'uuid':
                #foundMatch = True
                targetFieldNameComboBox.setCurrentText(targetFieldComboBoxText)
                # QgsMessageLog.logMessage('foundPartialNameMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
            # elif sourceFieldTypeName == targetFieldTypeName and not foundMatch:
            #     foundMatch = True
            #     targetFieldNameComboBox.setCurrentText(targetFieldComboBoxText)
            #     QgsMessageLog.logMessage('foundTypeMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)


    def getCopyErrorReason(self):

        # varmista, että ainakin yksi lähde-feature on valittuna
        if self.selectedSourceFeaturesCount() == 0:
            return COPY_ERROR_REASONS.SELECTED_FEATURE_COUNT_IS_ZERO

        # varmista, että self.targetSchemaTableName != None ja tarvittaessa ilmoita käyttäjälle
        if not self.isTargetTableSelected():
            return COPY_ERROR_REASONS.TARGET_TABLE_NOT_SELECTED

        # varmista, että kukin kohdekenttä on mahdollista valita vain kerran
        fieldNames, fieldTypeNames = self.getTargetFieldSelectedMoreThanOneTime()
        for index, fieldName in enumerate(fieldNames):
            if fieldName != None and fieldTypeNames[index] != 'String':
                return COPY_ERROR_REASONS.TARGET_FIELD_SELECTED_MULTIPLE_TIMES_NOT_SUPPORTED_FOR_TYPE

        return None


    def selectedSourceFeaturesCount(self):
        return self.sourceLayer.selectedFeatureCount()
    
    def isTargetTableSelected(self):
        if self.targetSchemaTableName == None:
            return False
        else:
            return True


    def getTargetFieldSelectedMoreThanOneTime(self):
        multiTargetFieldNames = []
        multiTargetFieldNameTypes = []

        targetFieldNames = []
        targetFieldTypeNames = []

        for i in range(self.getSourceTargetMatchRowCount()):
            # QgsMessageLog.logMessage("rowCount: " + str(self.getSourceTargetMatchRowCount()) + ", i: " + str(i), 'Yleiskaava-työkalu', Qgis.Info)

            targetFieldName = None
            targetFieldTypeName = None
            text = self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.cellWidget(i, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).currentText()
            if text != '':
                userFriendlyFieldName, targetFieldName, targetFieldTypeName = self.getTargetFieldNameAndTypeFromComboBoxText(text)

                if targetFieldName in targetFieldNames:
                    if targetFieldName not in multiTargetFieldNames:
                        multiTargetFieldNames.append(targetFieldName),
                        multiTargetFieldNameTypes.append(targetFieldTypeName)
                else:
                    targetFieldNames.append(targetFieldName)
                    targetFieldTypeNames.append(targetFieldTypeName)

        return multiTargetFieldNames, multiTargetFieldNameTypes


    def chooseSourceFeatures(self):
        # varmista, että self.targetSchemaTableName != None ja tarvittaessa ilmoita käyttäjälle
        if not self.isTargetTableSelected():
            self.iface.messageBar().pushMessage('Kopioinnin kohdekarttatasoa ei valittu', Qgis.Warning, duration=10)

        # varmista, että kukin kohdekenttä on mahdollista valita vain kerran
        fieldNames, fieldTypeNames = self.getTargetFieldSelectedMoreThanOneTime()
        for index, fieldName in enumerate(fieldNames):
            if fieldName != None and fieldTypeNames[index] != 'String':
                self.iface.messageBar().pushMessage("Sama kohdekenttä " + fieldName + "valittu usealla lähdekentälle ja kohdekentän tyyppi (" + fieldTypeNames[index] + ") ei tue arvojen yhdistämistä", Qgis.Warning)
                break

        self.dialogCopySourceDataToDatabase.hide()
        self.dialogCopySettings.hide()
        self.dialogChooseFeatures.show()
        self.iface.showAttributeTable(self.sourceLayer)


    def chooseCopySettings(self):
        # varmista, että ainakin yksi lähde-feature on valittuna ja tarvittaessa ilmoita käyttäjälle
        if self.selectedSourceFeaturesCount() == 0:
            self.iface.messageBar().pushMessage('Yhtään lähdekarttatason kohdetta ei ole valittuna', Qgis.Warning, duration=10)

        self.dialogCopySourceDataToDatabase.hide()
        self.dialogChooseFeatures.hide()
        self.showDialogCopySettings()


    def showDialogCopySettings(self):

        # # jos "Luo tarvittaessa uudet kaavamääräykset" / "Täytä kaavakohteiden käyttötarkoitus kaavamääräyksen mukaan tai päinvastoin" eivät relevantteja lähdeaineiston täysmäysten perusteella, niin näytä ko. elementit dialogissa disabloituna ja ilman valintaa
        # if not self.targetFieldsHaveRegulation() and not self.targetFieldsHaveLandUseClassification():
        #     self.dialogCopySettings.checkBoxCreateRegulations.setChecked(False)
        #     #self.dialogCopySettings.checkBoxCreateRegulations.setEnabled(False)
        # else:
        #     self.dialogCopySettings.checkBoxCreateRegulations.setChecked(True)
        #     self.dialogCopySettings.checkBoxCreateRegulations.setEnabled(True)

        # Huomioi, että jos käyttötarkoitus ja kaavamääräys molemmat lähdekohde-matchissä tai ei kumpaakaan, niin ei ruksia asetusdialogissa "Täytä kaavakohteiden käyttötarkoitus kaavamääräyksen mukaan tai päinvastoin"-kohtaan
        # if (not self.targetFieldsHaveRegulation() and not self.targetFieldsHaveLandUseClassification()) or (self.targetFieldsHaveRegulation() and self.targetFieldsHaveLandUseClassification()):
        #     self.dialogCopySettings.checkBoxFillLandUseClassificationWithRegulation.setChecked(False)
        #     #self.dialogCopySettings.checkBoxFillLandUseClassificationWithRegulation.setEnabled(False)
        # else:
        #     self.dialogCopySettings.checkBoxFillLandUseClassificationWithRegulation.setChecked(True)
        #     self.dialogCopySettings.checkBoxFillLandUseClassificationWithRegulation.setEnabled(True)
            
        self.initializeDialogCopySettingsMultiFieldMatchPart()
        self.initializeDialogCopySettingsPlanPart()
        self.initializeDialogCopySettingsDefaultFieldsPart()

        self.dialogCopySettings.resize(QSize(DataCopySourceToTarget.SETTINGS_DIALOG_MIN_WIDTH, DataCopySourceToTarget.SETTINGS_DIALOG_MIN_HEIGHT))
        self.dialogCopySettings.show()
        

    def initializeDialogCopySettingsMultiFieldMatchPart(self):
        fieldNames, fieldTypeNames = self.getTargetFieldSelectedMoreThanOneTime()
        # QgsMessageLog.logMessage("initializeDialogCopySettingsMultiFieldMatchPart - len(fieldNames): " + str(len(fieldNames)) + ", fieldNames: ", 'Yleiskaava-työkalu', Qgis.Info)
        # for fieldName in fieldNames:
        #     QgsMessageLog.logMessage(str(fieldName), 'Yleiskaava-työkalu', Qgis.Info)
        if len(fieldNames) == 0:
            self.dialogCopySettings.checkBoxIncludeFieldNamesForMultiValues.setChecked(False)
            self.dialogCopySettings.checkBoxIncludeFieldNamesForMultiValues.setEnabled(False)
            self.dialogCopySettings.labelMultiValuesSeparator.setEnabled(False)
            self.dialogCopySettings.lineEditMultiValuesSeparator.setEnabled(False)
        else:
            self.dialogCopySettings.checkBoxIncludeFieldNamesForMultiValues.setChecked(True)
            self.dialogCopySettings.checkBoxIncludeFieldNamesForMultiValues.setEnabled(True)
            self.dialogCopySettings.labelMultiValuesSeparator.setEnabled(True)
            self.dialogCopySettings.lineEditMultiValuesSeparator.setEnabled(True)


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

        # kun käyttäjä vaihtaa yleiskaavan, niin vaihda automaattisesti kaavataso (tarvittaessa)
        self.dialogCopySettings.comboBoxLevelOfSpatialPlan.addItems(sorted(planLevelNames))
        if len(planNamesOrdered) > 0:
            self.dialogCopySettings.comboBoxLevelOfSpatialPlan.setCurrentText(self.yleiskaavaDatabase.getYleiskaavaPlanLevelCodeWithPlanName(self.dialogCopySettings.comboBoxSpatialPlanName.currentText()))

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



    def initializeDialogCopySettingsDefaultFieldsPart(self):
        # 
        # esitä dialogissa sellaiset kohdekentät, joilla ei ole vielä arvoa tauluissa
        # yleiskaava, kaavaobjekti_*, kaavamaarays. Hae oletusarvot, jos mahdollista,
        # käyttäjän jo tekemien valintojen muukaan, esim. yleiskaavan nro nimen mukaan
        # Käsittele id_* kentät ja eri tyyppiset kentät jotenkin järkevästi
        #
        self.dialogCopySettings.tableWidgetDefaultFieldValues.clearContents()
        self.dialogCopySettings.tableWidgetDefaultFieldValues.setRowCount(self.getDefaultFieldValuesRowCount())
        self.dialogCopySettings.tableWidgetDefaultFieldValues.setColumnCount(2)
        self.dialogCopySettings.tableWidgetDefaultFieldValues.setHorizontalHeaderLabels([
            "Kohdekarttaso (kaavaobjekti) ja kenttä",
            "Kohdekentän oletusarvo"
        ])


        if self.targetSchemaTableName is not None:
            spatialTargetTableLayer = self.yleiskaavaDatabase.getProjectLayer(self.targetSchemaTableName)

            spatialTargetTableFields = self.yleiskaavaDatabase.getSchemaTableFields(self.targetSchemaTableName)

            index = 0

            for field in spatialTargetTableFields:
                targetFieldName = field.name()

                if self.yleiskaavaUtils.isShownTargetFieldName(targetFieldName):
                    success = self.showFieldInSettingsDialogDefaults(self.targetSchemaTableName, spatialTargetTableLayer, index, field)
                    if success:
                        index += 1

        self.dialogCopySettings.tableWidgetDefaultFieldValues.resizeColumnsToContents()


    #def comboBoxLevelOfSpatialPlanCurrentTextChanged(self):
    def comboBoxSpatialPlanNameCurrentTextChanged(self):
        self.dialogCopySettings.comboBoxLevelOfSpatialPlan.setCurrentText(self.yleiskaavaDatabase.getYleiskaavaPlanLevelCodeWithPlanName(self.dialogCopySettings.comboBoxSpatialPlanName.currentText()))


    def checkBoxLinkToSpatialPlanStateChanged(self):
        if self.dialogCopySettings.checkBoxLinkToSpatialPlan.isChecked():
            self.dialogCopySettings.comboBoxSpatialPlanName.setEnabled(True)
        else:
            self.dialogCopySettings.comboBoxSpatialPlanName.setEnabled(False)


    # def getChosenTargetFieldNames(self):
    #     # hae valittujen kohdekenttien nimet dialogin taulusta
    #     names = []
    #     for i in range(self.getSourceTargetMatchRowCount()):
    #         name = self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.cellWidget(i,DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).currentText()
    #         if len(name) > 0:
    #              # Remove userFriendlyFieldName and type and append
    #             userFriendlyFieldName, targetFieldName, targetFieldTypeName = self.getTargetFieldNameAndTypeFromComboBoxText(name)
    #             names.append(targetFieldName)
    #     return names


    def showFieldInSettingsDialogDefaults(self, schemaTableName, layer, fieldIndex, field):
        # targetSchemaTableLabel = QLabel(schemaTableName)
        # targetFieldLabel = QLabel(field.name())

        targetFieldName = field.name()
        targetFieldTypeName = self.yleiskaavaUtils.getStringTypeForFeatureField(field)

        userFriendlyTableName = self.yleiskaavaDatabase.getUserFriendlyschemaTableName(schemaTableName)
        userFriendlyFieldName = self.yleiskaavaDatabase.getUserFriendlytargetFieldName(targetFieldName)

        # targetFieldLabel = QLabel('' + targetFieldName + ' (' + targetFieldTypeName + ')')
        # targetSchemaTableFieldLabel = QLabel(schemaTableName + '.' + targetFieldName + ' (' + targetFieldTypeName + ')')
        targetSchemaTableFieldLabel = QLabel(userFriendlyTableName + ' - ' + userFriendlyFieldName)
        targetSchemaTableFieldLabel.setObjectName(DataCopySourceToTarget.OBJECT_NAME_UNIQUE_IDENTIFIERS["DEFAULT_VALUES_LABEL"] + str(fieldIndex))
        self.dialogCopySettings.tableWidgetDefaultFieldValues.setCellWidget(fieldIndex, DataCopySourceToTarget.DEFAULT_VALUES_LABEL_INDEX, targetSchemaTableFieldLabel)

        widget = self.yleiskaavaUtils.getWidgetForSpatialFeatureFieldType(targetFieldTypeName, targetFieldName)

        if widget != None:
            widget.setObjectName(DataCopySourceToTarget.OBJECT_NAME_UNIQUE_IDENTIFIERS["DEFAULT_VALUES_INPUT"] + str(fieldIndex))
            self.dialogCopySettings.tableWidgetDefaultFieldValues.setCellWidget(fieldIndex, DataCopySourceToTarget.DEFAULT_VALUES_INPUT_INDEX, widget)
        else:
            self.iface.messageBar().pushMessage('Bugi koodissa: showFieldInSettingsDialogDefaults widget == None', Qgis.Warning)
            #QgsMessageLog.logMessage('showFieldInSettingsDialogDefaults widget == None', 'Yleiskaava-työkalu', Qgis.Critical)
            return False
            
        return True


    def runCopySourceDataToDatabase(self):
        # Lisää lähdeaineiston valittujen rivien tiedot kohdetauluun ja huomioi myös oletusarvot, puuttuvat arvot, yhteydet yleiskaava-, kaavamääräys- ja koodi-tauluihin sekä tarvittaessa tee uudet kaavamääräykset
        reason = self.getCopyErrorReason()

        if reason == None:
            
            # TODO make memory copy of source and target layer before copy to db / tai tee ainakin kohdetasosta alunperinkin työtilasta erillinen karttataso

            sourceFeatures = self.sourceLayer.getSelectedFeatures()
            sourceCRS = self.sourceLayer.crs()
            sourceLayerFields = self.sourceLayer.fields().toList()

            transformContext = QgsProject.instance().transformContext()
            planNumber = self.yleiskaavaDatabase.getPlanNumberForName(self.getPlanNameFromCopySettings())
            shouldLinkToSpatialPlan = self.dialogCopySettings.checkBoxLinkToSpatialPlan.isChecked()
            spatialPlanName = self.dialogCopySettings.comboBoxSpatialPlanName.currentText()
            fieldMatches = self.getSourceTargetFieldMatches()
            includeFieldNamesForMultiValues = self.dialogCopySettings.checkBoxIncludeFieldNamesForMultiValues.isChecked()
            targetFieldValueSeparator = self.dialogCopySettings.lineEditMultiValuesSeparator.text()
            defaultFieldNameValueInfos = self.getDefaultTargetFieldInfo()
            shouldCreateNewRegulation = self.dialogCopySettings.checkBoxCreateRegulations.isChecked()
            shouldFillLandUseClassificationWithRegulation = self.dialogCopySettings.checkBoxFillLandUseClassificationWithRegulation.isChecked()
            specificRegulations = self.yleiskaavaDatabase.getSpecificRegulations()

            self.copySourceDataToDatabaseTask = CopySourceDataToDatabaseTask(self.yleiskaavaUtils, self.yleiskaavaDatabase, transformContext, planNumber, sourceFeatures, sourceCRS, sourceLayerFields, self.targetLayer.clone(), self.targetSchemaTableName, shouldLinkToSpatialPlan, spatialPlanName, fieldMatches, includeFieldNamesForMultiValues, targetFieldValueSeparator, defaultFieldNameValueInfos, shouldCreateNewRegulation, shouldFillLandUseClassificationWithRegulation, specificRegulations)

            self.copySourceDataToDatabaseTask.taskCompleted.connect(self.postCopySourceDataToDatabaseRun)
            self.copySourceDataToDatabaseTask.taskTerminated.connect(self.postCopySourceDataToDatabaseError)
            QgsApplication.taskManager().addTask(self.copySourceDataToDatabaseTask)
            self.copyMessageBarItem = QgsMessageBarItem('Kopioidaan lähdeaineiston kohteet tietokantaan. Älä muokkaa työtilan karttatasoja kopioinnin aikana!')
            self.iface.messageBar().pushItem(self.copyMessageBarItem)
            self.dialogCopyMessage.show()

        elif reason == COPY_ERROR_REASONS.SELECTED_FEATURE_COUNT_IS_ZERO:
            self.iface.messageBar().pushMessage('Yhtään lähdekarttatason kohdetta ei ole valittuna', Qgis.Critical)
        elif reason == COPY_ERROR_REASONS.TARGET_TABLE_NOT_SELECTED:
            self.iface.messageBar().pushMessage('Kopioinnin kohdekarttatasoa ei valittu', Qgis.Critical)
        elif reason == COPY_ERROR_REASONS.TARGET_FIELD_SELECTED_MULTIPLE_TIMES_NOT_SUPPORTED_FOR_TYPE:
            self.iface.messageBar().pushMessage('Sama kohdekenttä valittu usealla lähdekentälle ja kohdekentän tyyppi ei tue arvojen yhdistämistä', Qgis.Critical)
        

    def postCopySourceDataToDatabaseRun(self):
        self.hideAllDialogs()
        self.iface.messageBar().popWidget(self.copyMessageBarItem)
        self.copyMessageBarItem = None
        self.iface.messageBar().pushMessage('Lähdeaineisto kopioitu tietokantaan', Qgis.Info)
        # Päivitä lopuksi työtilan karttatasot, jotka liittyvät T1:n ajoon
        self.yleiskaavaUtils.refreshTargetLayersInProject()


    def postCopySourceDataToDatabaseError(self):
        self.iface.messageBar().pushMessage('Lähdeaineiston kopiointi tietokantaan epäonnistui', Qgis.Critical)


    def getPlanNameFromCopySettings(self):
        return self.dialogCopySettings.comboBoxSpatialPlanName.currentText()


    def getSourceTargetFieldMatches(self):
        fieldMatches = []

        rowCount = self.getSourceTargetMatchRowCount()

        #QgsMessageLog.logMessage("getSourceTargetFieldMatches - rowCount: " + str(rowCount), 'Yleiskaava-työkalu', Qgis.Info)

        for index in range(rowCount):
            sourceFieldName = self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.cellWidget(index, DataCopySourceToTarget.SOURCE_FIELD_NAME_INDEX).text()
            sourceFieldTypeName = self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.cellWidget(index, DataCopySourceToTarget.SOURCE_FIELD_TYPE_NAME_INDEX).text()
            
            targetFieldName = None
            targetFieldTypeName = None
            text = self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.cellWidget(index, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).currentText()
            

            # QgsMessageLog.logMessage("getSourceTargetFieldMatches - index: " + str(index) + ", sourceFieldName: " + sourceFieldName + ", sourceFieldTypeName: " + sourceFieldTypeName + ", TARGET_TABLE_FIELD_NAME: " + text, 'Yleiskaava-työkalu', Qgis.Info)

            if text != '':
                userFriendlyFieldName, targetFieldName, targetFieldTypeName = self.getTargetFieldNameAndTypeFromComboBoxText(text)

            if targetFieldName != None:
                fieldMatches.append({ "source": sourceFieldName, "sourceFieldTypeName": sourceFieldTypeName, "target": targetFieldName, "targetFieldTypeName": targetFieldTypeName })
            
        return fieldMatches


    def getDefaultTargetFieldInfo(self):
        defaultFieldNameValueInfos = []

        for i in range(self.getDefaultFieldValuesRowCount()):
            text = self.dialogCopySettings.tableWidgetDefaultFieldValues.cellWidget(i, DataCopySourceToTarget.DEFAULT_VALUES_LABEL_INDEX).text()

            userFriendlyTableName = text.split(' - ')[0]
            userFriendlytargetFieldName = text.split(' - ')[1]

            targetSchemaTableName = self.yleiskaavaDatabase.getTableNameForUserFriendlyschemaTableName(userFriendlyTableName)
            targetFieldName = self.yleiskaavaDatabase.getFieldNameForUserFriendlytargetFieldName(userFriendlytargetFieldName)

            targetFieldType = self.yleiskaavaDatabase.getTypeOftargetField(targetFieldName)
            widgetClass = self.yleiskaavaUtils.getClassOftargetFieldType(targetFieldType)

            widget = self.dialogCopySettings.tableWidgetDefaultFieldValues.cellWidget(i, DataCopySourceToTarget.DEFAULT_VALUES_INPUT_INDEX)
            # QgsMessageLog.logMessage("getDefaultTargetFieldInfo - targetFieldName: " + targetFieldName, 'Yleiskaava-työkalu', Qgis.Info)
            value = self.yleiskaavaUtils.getValueOfWidgetForType(widget, targetFieldType)
            variantValue = None
            if value is None:
                variantValue = QVariant()
            else:
                variantValue = QVariant(value)

            targetFieldInfo = { "name": targetFieldName, "type": targetFieldType, "widget": widget, "value": variantValue }
            defaultFieldNameValueInfos.append(targetFieldInfo)

            # QgsMessageLog.logMessage("getDefaultTargetFieldInfo - targetFieldName: " + targetFieldName + ", value: " + str(variantValue.value()), 'Yleiskaava-työkalu', Qgis.Info)

        return defaultFieldNameValueInfos


    def targetFieldsHaveRegulation(self):
        for i in range(self.getSourceTargetMatchRowCount()):
            # QgsMessageLog.logMessage("targetFieldsHaveRegulation - tableWidgetRowCount: " + str(self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.rowCount()) + ", rowCount: " + str(self.getSourceTargetMatchRowCount()) + ", i: " + str(i), 'Yleiskaava-työkalu', Qgis.Info)
            targetFieldName = None
            targetFieldTypeName = None
            text = self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.cellWidget(i, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).currentText()
            if text != '':
                userFriendlyFieldName, targetFieldName, targetFieldTypeName = self.getTargetFieldNameAndTypeFromComboBoxText(text)

            if targetFieldName == 'kaavamaaraysotsikko':
                return True

        return False


    def targetFieldsHaveLandUseClassification(self):
        for i in range(self.getSourceTargetMatchRowCount()):
            targetFieldName = None
            targetFieldTypeName = None
            text = self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.cellWidget(i, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).currentText()
            if text != '':
                userFriendlyFieldName, targetFieldName, targetFieldTypeName = self.getTargetFieldNameAndTypeFromComboBoxText(text)

            if targetFieldName == 'kayttotarkoitus_lyhenne':
                return True

        return False


    def getSourceTargetMatchRowCount(self):
        count = 0
        if self.sourceLayer is not None:
            fields = self.sourceLayer.fields().toList()
            for index, field in enumerate(fields):
                if field.name() != 'id' and self.yleiskaavaUtils.getStringTypeForFeatureField(field) != 'uuid':
                    count += 1

        return count


    def getDefaultFieldValuesRowCount(self):
        count = 0

        if self.targetSchemaTableName is not None:
            spatialTargetTableFields = self.yleiskaavaDatabase.getSchemaTableFields(self.targetSchemaTableName)
            count = self.yleiskaavaUtils.getShownFieldNameCount(spatialTargetTableFields)

        return count

    
    def pushButtonChooseExistingRegulationForDefaultClicked(self):
        self.setupRegulationsInDialog()
        self.dialogChooseRegulation.show()


    def handleDialogChooseRegulationAccept(self):
        defaultRegulationTitle = None

        if self.currentRegulation is not None:
            defaultRegulationTitle = self.currentRegulation["kaavamaarays_otsikko"].value()
        else:
            defaultRegulationTitle = ""

        lineEdit = self.findDefaultValuesInputLineEditFromTableWidget('Kaavamääräysotsikko')
        lineEdit.setText(defaultRegulationTitle)

        if self.targetLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_ALUE and defaultRegulationTitle != "":
            lineEdit = self.findDefaultValuesInputLineEditFromTableWidget("Käyttötarkoituksen lyhenne (esim. A, C)")
            planNumber = self.yleiskaavaDatabase.getPlanNumberForName(self.getPlanNameFromCopySettings())
            landUseClassificationName = self.yleiskaavaUtils.getLandUseClassificationNameForRegulation(planNumber, self.targetSchemaTableName, defaultRegulationTitle)
            lineEdit.setText(landUseClassificationName)

        self.dialogChooseRegulation.hide()

    
    def findDefaultValuesInputLineEditFromTableWidget(self, userFriendlytargetFieldNameToSearh):
        for i in range(self.getDefaultFieldValuesRowCount()):
            text = self.dialogCopySettings.tableWidgetDefaultFieldValues.cellWidget(i, DataCopySourceToTarget.DEFAULT_VALUES_LABEL_INDEX).text()

            userFriendlyTableName = text.split(' - ')[0]
            userFriendlytargetFieldName = text.split(' - ')[1]

            if userFriendlytargetFieldName == userFriendlytargetFieldNameToSearh:
                return self.dialogCopySettings.tableWidgetDefaultFieldValues.cellWidget(i, DataCopySourceToTarget.DEFAULT_VALUES_INPUT_INDEX)


    def setupRegulationsInDialog(self):
        self.includeAreaRegulations = False
        self.includeSuplementaryAreaRegulations = False
        self.includeLineRegulations = False
        self.includePointRegulations = False
        if self.targetLayer is None:
            self.includeAreaRegulations = True
            self.includeSuplementaryAreaRegulations = True
            self.includeLineRegulations = True
            self.includePointRegulations = True
        elif self.targetLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_ALUE:
            self.includeAreaRegulations = True
        elif self.targetLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA:
            self.includeSuplementaryAreaRegulations = True
        elif self.targetLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA:
            self.includeLineRegulations = True
        elif self.targetLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_PISTE:
            self.includePointRegulations = True

        shouldShowOnlyUsedRegulations = False
        if self.dialogChooseRegulation.checkBoxShowOnlyUsedRegulations.isChecked():
            shouldShowOnlyUsedRegulations = True


        self.regulations = sorted(self.yleiskaavaDatabase.getSpecificRegulations(shouldShowOnlyUsedRegulations, self.includeAreaRegulations,  self.includeSuplementaryAreaRegulations,  self.includeLineRegulations,  self.includePointRegulations), key=itemgetter('alpha_sort_key'))
        self.regulationTitles = []
        for index, regulation in enumerate(self.regulations):
            #QgsMessageLog.logMessage("setupRegulationsInDialog - index: " + str(index) + ", regulation['kaavamaarays_otsikko']: " + str(regulation['kaavamaarays_otsikko'].value()) + ", regulation['maaraysteksti']: " + str(regulation['maaraysteksti'].value()) + ", regulation['kuvaus_teksti']: " + str(regulation['kuvaus_teksti'].value()), 'Yleiskaava-työkalu', Qgis.Info)
            # QgsMessageLog.logMessage("setupRegulationsInDialog - index: " + str(index) + ", regulation['kaavamaarays_otsikko']: " + str(regulation['kaavamaarays_otsikko'].value()), 'Yleiskaava-työkalu', Qgis.Info)
            self.regulationTitles.append(regulation["kaavamaarays_otsikko"].value())
        self.dialogChooseRegulation.comboBoxRegulationTitles.clear()
        self.dialogChooseRegulation.comboBoxRegulationTitles.addItems(self.regulationTitles)

        self.dialogChooseRegulation.comboBoxRegulationTitles.insertItem(0, "Valitse kaavamääräys")
        self.dialogChooseRegulation.comboBoxRegulationTitles.setCurrentIndex(0)
        self.currentRegulation = None

    
    def handleComboBoxRegulationTitleChanged(self, currentIndex):
        # QgsMessageLog.logMessage("handleComboBoxRegulationTitleChanged - currentIndex: " + str(currentIndex) + ", len(self.regulations): " + str(len(self.regulations)), 'Yleiskaava-työkalu', Qgis.Info)
        if currentIndex > 0 and self.regulations is not None and len(self.regulations) >= (currentIndex - 1):
            self.currentRegulation = self.regulations[currentIndex - 1]

            self.dialogChooseRegulation.plainTextEditRegulationTitle.setPlainText(self.currentRegulation["kaavamaarays_otsikko"].value())
            if not self.currentRegulation["maaraysteksti"].isNull():
                self.dialogChooseRegulation.plainTextEditRegulationText.setPlainText(self.currentRegulation["maaraysteksti"].value())
            else:
                self.dialogChooseRegulation.plainTextEditRegulationText.setPlainText("")
            if not self.currentRegulation["kuvaus_teksti"].isNull():
                self.dialogChooseRegulation.plainTextEditRegulationDescription.setPlainText(self.currentRegulation["kuvaus_teksti"].value())
            else:
                self.dialogChooseRegulation.plainTextEditRegulationDescription.setPlainText("")
        else:
            self.currentRegulation = None
            self.dialogChooseRegulation.plainTextEditRegulationTitle.setPlainText("")
            self.dialogChooseRegulation.plainTextEditRegulationText.setPlainText("")
            self.dialogChooseRegulation.plainTextEditRegulationDescription.setPlainText("")


    def checkBoxShowOnlyUsedRegulationsStateChanged(self):
        self.setupRegulationsInDialog()


        