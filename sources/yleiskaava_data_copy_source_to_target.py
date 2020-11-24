
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QVariant, QSize
from qgis.PyQt.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox, QCheckBox

from qgis.core import (
    Qgis, QgsProject,
    QgsFeature, QgsWkbTypes,
    QgsMessageLog, QgsMapLayer,
    QgsMapLayerProxyModel, QgsGeometry,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsApplication, QgsExpressionContextUtils)

from qgis.gui import QgsFilterLineEdit, QgsDateTimeEdit, QgsMessageBarItem

import os.path
from functools import partial
from operator import itemgetter
from collections import Counter
import uuid


# from .yleiskaava_dialog_copy_source_data_to_database import Ui_DialogCopySourceDataToDatabase
from .yleiskaava_data_copy_source_to_target_task import CopySourceDataToDatabaseTask
from .yleiskaava_utils import COPY_ERROR_REASONS
from .yleiskaava_database import YleiskaavaDatabase

class DataCopySourceToTarget:
    
    SOURCE_FIELD_NAME_INDEX = 0
    SOURCE_FIELD_TYPE_NAME_INDEX = 1
    TARGET_TABLE_NAME_INDEX = 2
    TARGET_TABLE_FIELD_NAME_INDEX = 3

    DEFAULT_VALUES_LABEL_INDEX = 0
    DEFAULT_VALUES_INPUT_INDEX = 1

    SETTINGS_DIALOG_MIN_WIDTH = 1068
    SETTINGS_DIALOG_MIN_HEIGHT = 1182

    COPY_SOURCE_DATA_DIALOG_MIN_WIDTH = 1006
    COPY_SOURCE_DATA_DIALOG_MIN_HEIGHT = 624

    MESSAGE_BAR_TEXT_COPYING = 'Kopioidaan lähdeaineiston kohteet tietokantaan. Älä muokkaa työtilan karttatasoja kopioinnin aikana!'


    def __init__(self, iface, plugin_dir, yleiskaavaSettings, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaSettings = yleiskaavaSettings
        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = plugin_dir

        self.dialogCopySourceDataToDatabase = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_copy_source_data_to_database.ui'))

        self.dialogChooseFeatures = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_choose_features.ui'))

        self.dialogCopySettings = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_copy_settings.ui'))

        self.dialogChooseRegulation = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_choose_regulation.ui'))

        self.dialogCopyMessage = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_copy_message.ui'))

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

        self.hasUserCanceledCopy = False
        

    def setup(self):
        self.setupDialogCopySourceDataToDatabase()
        self.setupDialogChooseFeatures()
        self.setupDialogCopySettings()
        self.setupDialogChooseRegulation()
        self.setupDialogCopyMessage()


    def setupDialogCopyMessage(self):
        self.dialogCopyMessage.labelWarning.setStyleSheet("color: rgb(51, 0, 0);")
        # self.dialogCopyMessage.pushButtonClose.clicked.connect(self.dialogCopyMessage.hide)
        self.dialogCopyMessage.pushButtonStop.clicked.connect(self.handleCopyTaskStopRequestedByUser)


    def setupDialogCopySourceDataToDatabase(self):
        self.dialogCopySourceDataToDatabase.pushButtonCancel.clicked.connect(self.hideAllDialogs)
        self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.layerChanged.connect(self.handleMapLayerComboBoxSourceChanged)
        self.dialogCopySourceDataToDatabase.pushButtonNext.clicked.connect(self.chooseSourceFeatures)


    def setupDialogChooseFeatures(self):
        self.dialogChooseFeatures.pushButtonCancel.clicked.connect(self.hideAllDialogs)
        self.dialogChooseFeatures.pushButtonPrevious.clicked.connect(self.openPreviousDialogCopySourceDataToDatabase)
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
        self.dialogChooseFeatures.hide()
        self.dialogCopySettings.hide()
        self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.setFilters(QgsMapLayerProxyModel.HasGeometry)
        self.dialogCopySourceDataToDatabase.resize(QSize(DataCopySourceToTarget.COPY_SOURCE_DATA_DIALOG_MIN_WIDTH, DataCopySourceToTarget.COPY_SOURCE_DATA_DIALOG_MIN_HEIGHT))
        if self.yleiskaavaSettings.shouldKeepDialogsOnTop():
            self.dialogCopySourceDataToDatabase.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        else:
            self.dialogCopySourceDataToDatabase.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.dialogCopySourceDataToDatabase.show()
        self.sourceLayer = self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.currentLayer()
        if self.sourceLayer is not None:
            # QgsMessageLog.logMessage(layer.name(), 'Yleiskaava-työkalu', Qgis.Info)
            self.updateUIBasedOnSourceLayer(self.sourceLayer)
            self.selectTargetLayerBasedOnSourceLayerGeometryType()


    def openPreviousDialogCopySourceDataToDatabase(self):
        self.dialogChooseFeatures.hide()
        self.dialogCopySettings.hide()
        self.dialogCopySourceDataToDatabase.show()
        

    def handleMapLayerComboBoxSourceChanged(self, layer):
        if layer is not None:
            # QgsMessageLog.logMessage(layer.name(), 'Yleiskaava-työkalu', Qgis.Info)
            self.sourceLayer = layer
            self.updateUIBasedOnSourceLayer(self.sourceLayer)
            self.selectTargetLayerBasedOnSourceLayerGeometryType()


    def selectTargetLayerBasedOnSourceLayerGeometryType(self):
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

            # self.yleiskaavaDatabase.reconnectToDB()

            index = 0
            for field in sourceLayer.fields().toList():
                # if True: #field.name() == 'id' or self.yleiskaavaUtils.getStringTypeForFeatureField(field) != 'uuid':
                # QgsMessageLog.logMessage('updateUIBasedOnSourceLayer - field.name(): ' + field.name(), 'Yleiskaava-työkalu', Qgis.Info)
                sourceFieldnameLabel = QLabel(field.name())
                # QgsMessageLog.logMessage('updateUIBasedOnSourceLayer - sourceFieldnameLabel != None? ' + str(sourceFieldnameLabel is not None), 'Yleiskaava-työkalu', Qgis.Info)
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
                
                self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.setCellWidget(index, DataCopySourceToTarget.SOURCE_FIELD_NAME_INDEX, sourceFieldnameLabel)
                self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.setCellWidget(index, DataCopySourceToTarget.SOURCE_FIELD_TYPE_NAME_INDEX, sourceFieldtypeLabel)
                self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.setCellWidget(index, DataCopySourceToTarget.TARGET_TABLE_NAME_INDEX, targetTableComboBox)
                self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.setCellWidget(index, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX, targetFieldNameComboBox)

                targetTableComboBox.currentTextChanged.connect(partial(self.handleTargetTableSelectChanged, index, sourceFieldTypeName, targetTableComboBox, targetFieldNameComboBox))
                # QgsMessageLog.logMessage('updateUIBasedOnSourceLayer - lisätty rivi tableWidgetSourceTargetMatch', 'Yleiskaava-työkalu', Qgis.Info)
                index += 1

            self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.resizeColumnsToContents()


    def handleTargetTableSelectChanged(self, rowIndex, sourceFieldTypeName, targetTableComboBox, targetFieldNameComboBox):

        # self.yleiskaavaDatabase.reconnectToDB()
        
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
        # self.yleiskaavaDatabase.reconnectToDB()
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
                self.iface.messageBar().pushMessage("Sama kohdekenttä " + fieldName + "valittu usealla lähdekentälle ja kohdekentän tyyppi (" + fieldTypeNames[index] + ") ei tue arvojen yhdistämistä", Qgis.Warning, duration=20)
                break

        self.dialogCopySourceDataToDatabase.hide()
        self.dialogCopySettings.hide()
        if self.yleiskaavaSettings.shouldKeepDialogsOnTop():
            self.dialogChooseFeatures.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        else:
            self.dialogChooseFeatures.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
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
        if self.yleiskaavaSettings.shouldKeepDialogsOnTop():
            self.dialogCopySettings.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        else:
            self.dialogCopySettings.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
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
        # self.yleiskaavaDatabase.reconnectToDB()
        plans, planLevelList = self.yleiskaavaDatabase.getSpatialPlansAndPlanLevels()

        planNames = [plan["nimi"] for plan in plans]

        planNameCounter = Counter(planNames)
        planNamesOrderedWithCount = planNameCounter.most_common()
        planNamesOrdered = [item[0] for item in planNamesOrderedWithCount]

        self.dialogCopySettings.comboBoxSpatialPlanName.clear()
        if len(planNamesOrdered) > 0:
            self.dialogCopySettings.comboBoxSpatialPlanName.addItems(planNamesOrdered)
            self.dialogCopySettings.comboBoxSpatialPlanName.setCurrentText(planNamesOrdered[0])

        # hae kaikki kaavatasot, täytä comboBoxLevelOfSpatialPlan niiden nimillä ja valitse sopiva yleiskaavataso
        planLevelNames = []
        for item in planLevelList:
            # QgsMessageLog.logMessage('initializeDialogCopySettingsPlanPart - type(item): ' + str(type(item)), 'Yleiskaava-työkalu', Qgis.Info)
            planLevelNames.append(item["koodi"])

        # kun käyttäjä vaihtaa yleiskaavan, niin vaihda automaattisesti kaavataso (tarvittaessa)
        self.dialogCopySettings.comboBoxLevelOfSpatialPlan.addItems(sorted(planLevelNames))
        if len(planNamesOrdered) > 0:
            for plan in plans:
                if plan["nimi"] == planNamesOrdered[0]:
                    self.dialogCopySettings.comboBoxLevelOfSpatialPlan.setCurrentText(plan["kaavan_taso_koodi"])
                    break

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
        count = 0
        spatialTargetTableFields = []
        if self.targetSchemaTableName is not None:
            count, spatialTargetTableFieldInfos = self.getDefaultFieldValuesRowCountAndFieldInfos()

        self.dialogCopySettings.tableWidgetDefaultFieldValues.clearContents()
        self.dialogCopySettings.tableWidgetDefaultFieldValues.setRowCount(count)
        self.dialogCopySettings.tableWidgetDefaultFieldValues.setColumnCount(2)
        self.dialogCopySettings.tableWidgetDefaultFieldValues.setHorizontalHeaderLabels([
            "Kohdekarttaso (kaavaobjekti) ja kenttä",
            "Kohdekentän oletusarvo"
        ])

        if self.targetSchemaTableName is not None:
            index = 0

            for fieldInfo in spatialTargetTableFieldInfos:
                targetFieldName = fieldInfo["name"]

                if self.yleiskaavaUtils.isShownTargetFieldName(targetFieldName):
                    success = False
                    success = self.showFieldInSettingsDialogDefaults(self.targetSchemaTableName, index, fieldInfo)
                    if success:
                        index += 1

        self.dialogCopySettings.tableWidgetDefaultFieldValues.resizeColumnsToContents()


    #def comboBoxLevelOfSpatialPlanCurrentTextChanged(self):
    def comboBoxSpatialPlanNameCurrentTextChanged(self):
        # self.yleiskaavaDatabase.reconnectToDB()
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


    def showFieldInSettingsDialogDefaults(self, schemaTableName, fieldIndex, fieldInfo):
        # targetSchemaTableLabel = QLabel(schemaTableName)
        # targetFieldLabel = QLabel(field.name())

        targetFieldName = fieldInfo["name"]
        targetFieldTypeName = fieldInfo["type"]

        # self.yleiskaavaDatabase.reconnectToDB()
        userFriendlyTableName = self.yleiskaavaDatabase.getUserFriendlyschemaTableName(schemaTableName)
        userFriendlyFieldName = self.yleiskaavaDatabase.getUserFriendlytargetFieldName(targetFieldName)

        # targetFieldLabel = QLabel('' + targetFieldName + ' (' + targetFieldTypeName + ')')
        # targetSchemaTableFieldLabel = QLabel(schemaTableName + '.' + targetFieldName + ' (' + targetFieldTypeName + ')')
        targetSchemaTableFieldLabel = QLabel(userFriendlyTableName + ' - ' + userFriendlyFieldName)
        self.dialogCopySettings.tableWidgetDefaultFieldValues.setCellWidget(fieldIndex, DataCopySourceToTarget.DEFAULT_VALUES_LABEL_INDEX, targetSchemaTableFieldLabel)

        widget = self.yleiskaavaUtils.getWidgetForSpatialFeatureFieldType(targetFieldTypeName, targetFieldName)

        if widget != None:
            self.dialogCopySettings.tableWidgetDefaultFieldValues.setCellWidget(fieldIndex, DataCopySourceToTarget.DEFAULT_VALUES_INPUT_INDEX, widget)

            if targetFieldName == 'muokkaaja':
                if QgsExpressionContextUtils.globalScope().hasVariable('user_account_name'):
                    widget.setText(QgsExpressionContextUtils.globalScope().variable('user_account_name'))
            elif targetFieldName == 'id_kansallinen_prosessin_vaihe':
                widget.setCurrentText(self.yleiskaavaSettings.getDefaultCodeValue(targetFieldName))
            elif targetFieldName == 'id_laillinen_sitovuus':
                widget.setCurrentText(self.yleiskaavaSettings.getDefaultCodeValue(targetFieldName))
            elif targetFieldName == 'id_prosessin_vaihe':
                widget.setCurrentText(self.yleiskaavaSettings.getDefaultCodeValue(targetFieldName))
            elif targetFieldName == 'id_kaavoitusprosessin_tila':
                widget.setCurrentText(self.yleiskaavaSettings.getDefaultCodeValue(targetFieldName))
        else:
            self.iface.messageBar().pushMessage('Bugi koodissa: showFieldInSettingsDialogDefaults widget == None', Qgis.Warning, duration=0)
            #QgsMessageLog.logMessage('showFieldInSettingsDialogDefaults widget == None', 'Yleiskaava-työkalu', Qgis.Critical)
            return False
            
        return True


    def runCopySourceDataToDatabase(self):
        # Lisää lähdeaineiston valittujen rivien tiedot kohdetauluun ja huomioi myös oletusarvot, puuttuvat arvot, yhteydet yleiskaava-, kaavamääräys- ja koodi-tauluihin sekä tarvittaessa tee uudet kaavamääräykset
        reason = self.getCopyErrorReason()

        if reason == None:
            transformContext = QgsProject.instance().transformContext() # OK - QgsCoordinateTransformContext: "QgsCoordinateTransformContext objects are thread safe for read and write.", https://qgis.org/pyqgis/3.4/core/QgsCoordinateTransformContext.html
            # self.yleiskaavaDatabase.reconnectToDB()
            spatialPlanName = self.dialogCopySettings.comboBoxSpatialPlanName.currentText() # ok
            spatialPlanID, planNumber = self.yleiskaavaDatabase.getSpatialPlanIDAndNumberForPlanName(spatialPlanName) # ok
            shouldLinkToSpatialPlan = self.dialogCopySettings.checkBoxLinkToSpatialPlan.isChecked() # ok
            fieldMatches = self.getSourceTargetFieldMatches() # ok
            includeFieldNamesForMultiValues = self.dialogCopySettings.checkBoxIncludeFieldNamesForMultiValues.isChecked() # ok
            targetFieldValueSeparator = self.dialogCopySettings.lineEditMultiValuesSeparator.text() # ok
            defaultFieldNameValueInfos = self.getDefaultTargetFieldInfo() # ok
            shouldCreateNewRegulation = self.dialogCopySettings.checkBoxCreateRegulations.isChecked() # ok
            shouldCapitalize = self.dialogCopySettings.checkBoxCapitalize.isChecked() # ok
            shouldFillLandUseClassificationWithRegulation = self.dialogCopySettings.checkBoxFillLandUseClassificationWithRegulation.isChecked() # ok
            specificRegulations = self.yleiskaavaDatabase.getSpecificRegulations()
            regulationNames = []
            for regulation in specificRegulations:
                  if not regulation["kaavamaarays_otsikko"].isNull():
                      if regulation["kaavamaarays_otsikko"].value() != None:
                        regulationNames.append(regulation["kaavamaarays_otsikko"].value()) # ok

            self.copySourceDataToDatabaseTask = CopySourceDataToDatabaseTask(self.yleiskaavaUtils, self.yleiskaavaDatabase, transformContext, planNumber, self.targetSchemaTableName, shouldLinkToSpatialPlan, spatialPlanName, spatialPlanID, fieldMatches, includeFieldNamesForMultiValues, targetFieldValueSeparator, defaultFieldNameValueInfos, shouldCreateNewRegulation, shouldCapitalize, shouldFillLandUseClassificationWithRegulation, regulationNames) # OK  - yllä olevat
            regulationLayer = self.yleiskaavaDatabase.getProjectLayer("yk_yleiskaava.kaavamaarays")
            regulationRelationLayer = self.yleiskaavaDatabase.getProjectLayer("yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys")
            self.copySourceDataToDatabaseTask.setDependentLayers([self.sourceLayer, self.targetLayer, regulationLayer, regulationRelationLayer])

            # self.copySourceDataToDatabaseTask.createFeatureRegulationRelation.connect(self.handleCreateFeatureRegulationRelation)
            # self.copySourceDataToDatabaseTask.createSpecificRegulationAndFeatureRegulationRelation.connect(self.handleCreateSpecificRegulationAndFeatureRegulationRelation)
            self.copySourceDataToDatabaseTask.progressChanged.connect(self.handleCopySourceDataToDatabaseTaskProgressChanged)
            self.copySourceDataToDatabaseTask.taskCompleted.connect(self.handleCopySourceDataToDatabaseTaskCompleted)
            self.copySourceDataToDatabaseTask.taskTerminated.connect(self.handleCopySourceDataToDatabaseTerminated)
            copyMessageBarItem = QgsMessageBarItem(DataCopySourceToTarget.MESSAGE_BAR_TEXT_COPYING)
            self.iface.messageBar().pushItem(copyMessageBarItem)
            self.dialogCopyMessage.progressBar.setValue(0)
            if self.yleiskaavaSettings.shouldKeepDialogsOnTop():
                self.dialogCopyMessage.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowStaysOnTopHint)
            else:
                self.dialogCopyMessage.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
            self.dialogCopyMessage.show()
            QgsApplication.taskManager().addTask(self.copySourceDataToDatabaseTask)

        elif reason == COPY_ERROR_REASONS.SELECTED_FEATURE_COUNT_IS_ZERO:
            self.iface.messageBar().pushMessage('Yhtään lähdekarttatason kohdetta ei ole valittuna', Qgis.Critical, duration=0)
        elif reason == COPY_ERROR_REASONS.TARGET_TABLE_NOT_SELECTED:
            self.iface.messageBar().pushMessage('Kopioinnin kohdekarttatasoa ei valittu', Qgis.Critical, duration=0)
        elif reason == COPY_ERROR_REASONS.TARGET_FIELD_SELECTED_MULTIPLE_TIMES_NOT_SUPPORTED_FOR_TYPE:
            self.iface.messageBar().pushMessage('Sama kohdekenttä valittu usealla lähdekentälle ja kohdekentän tyyppi ei tue arvojen yhdistämistä', Qgis.Critical, duration=0)


    # def handleCreateFeatureRegulationRelation(self, targetSchemaTableName, featureID, regulationName):
    #     self.yleiskaavaDatabase.createFeatureRegulationRelation(targetSchemaTableName, featureID, regulationName)


    # def handleCreateSpecificRegulationAndFeatureRegulationRelation(self, featureID, regulationName):
    #     self.yleiskaavaDatabase.createSpecificRegulationAndFeatureRegulationRelation(targetSchemaTableName, featureID, regulationName)


    def handleCopyTaskStopRequestedByUser(self):
        self.hasUserCanceledCopy = True
        self.copySourceDataToDatabaseTask.cancel()


    def handleCopySourceDataToDatabaseTaskProgressChanged(self, progress):
        self.dialogCopyMessage.progressBar.setValue(int(progress))


    def handleCopySourceDataToDatabaseTaskCompleted(self):
        self.hideAllDialogs()
        copyMessageBarItem = self.iface.messageBar().currentItem()
        if copyMessageBarItem is not None and copyMessageBarItem.text() == DataCopySourceToTarget.MESSAGE_BAR_TEXT_COPYING:
            try:
                self.iface.messageBar().popWidget()
            except RuntimeError:
                pass
        self.yleiskaavaUtils.refreshTargetLayersInProject() # Päivitä lopuksi työtilan karttatasot, jotka liittyvät T1:n ajoon

        messages = self.copySourceDataToDatabaseTask.getMessages()
        if len(messages) > 0:
            messageLevel = Qgis.Info
            for message in messages:
                if message['messageLevel'] == Qgis.Warning and (messageLevel != Qgis.Warning and messageLevel != Qgis.Critical):
                    messageLevel = message['messageLevel']
                elif message['messageLevel'] == Qgis.Critical and messageLevel != Qgis.Critical:
                    messageLevel = message['messageLevel']

            for message in messages:
                self.iface.messageBar().pushMessage(str(message['message']), message['messageLevel'], duration=0)

        if not self.hasUserCanceledCopy:
            self.iface.messageBar().pushMessage('Lähdeaineisto {} kopioitu tietokantaan'.format(self.sourceLayer.name()), Qgis.Info, duration=60)
        else:
            self.iface.messageBar().pushMessage('Lähdeaineistoa ei kopioitu kokonaisuudessaan tietokantaan', Qgis.Info, duration=0)
            
        if len(messages) > 0:
            messageLevel = Qgis.Warning
            self.iface.messageBar().pushMessage('Aineiston tuonnissa oli huomioitavia asioita', messageLevel, duration=0)


    def handleCopySourceDataToDatabaseTerminated(self):
        self.hideAllDialogs()
        copyMessageBarItem = self.iface.messageBar().currentItem()
        if copyMessageBarItem is not None and copyMessageBarItem.text() == DataCopySourceToTarget.MESSAGE_BAR_TEXT_COPYING:
            try:
                self.iface.messageBar().popWidget()
            except RuntimeError:
                pass
        self.yleiskaavaUtils.refreshTargetLayersInProject() # Päivitä lopuksi työtilan karttatasot, jotka liittyvät T1:n ajoon
        if not self.hasUserCanceledCopy:
            self.iface.messageBar().pushMessage('Lähdeaineiston kopiointi tietokantaan epäonnistui', Qgis.Critical, duration=0)
        else:
            self.hasUserCanceledCopy = False


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

        # self.yleiskaavaDatabase.reconnectToDB()

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

            # QgsMessageLog.logMessage("getDefaultTargetFieldInfo - targetFieldName: " + targetFieldName + ", value: " + str(value), 'Yleiskaava-työkalu', Qgis.Info)

            tempValue = None
            if not QVariant(value).isNull():
                tempValue = QVariant(value).value()
            else:
                tempValue = None

            targetFieldInfo = { "name": targetFieldName, "type": targetFieldType, "value": tempValue }
            defaultFieldNameValueInfos.append(targetFieldInfo)

            # QgsMessageLog.logMessage("getDefaultTargetFieldInfo - targetFieldName: " + targetFieldName + ", tempValue: " + str(tempValue), 'Yleiskaava-työkalu', Qgis.Info)

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
            count = len(fields)

        return count


    def getDefaultFieldValuesRowCount(self):
        count = 0
        count, spatialTargetTableFields = self.getDefaultFieldValuesRowCountAndFieldInfos()
        return count


    def getDefaultFieldValuesRowCountAndFieldInfos(self):
        count = 0
        spatialTargetTableFieldInfos = []

        # self.yleiskaavaDatabase.reconnectToDB()

        if self.targetSchemaTableName is not None:
            spatialTargetTableFieldInfos = self.yleiskaavaDatabase.getSchemaTableFieldInfos(self.targetSchemaTableName)
            count = self.yleiskaavaUtils.getShownFieldNameCountForFieldInfos(spatialTargetTableFieldInfos)

        return count, spatialTargetTableFieldInfos


    def pushButtonChooseExistingRegulationForDefaultClicked(self):
        self.setupRegulationsInDialog()
        if self.yleiskaavaSettings.shouldKeepDialogsOnTop():
            self.dialogChooseRegulation.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        else:
            self.dialogChooseRegulation.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.dialogChooseRegulation.show()


    def handleDialogChooseRegulationAccept(self):
        defaultRegulationTitle = None

        if self.currentRegulation is not None:
            defaultRegulationTitle = self.currentRegulation["kaavamaarays_otsikko"].value()
        else:
            defaultRegulationTitle = ""

        lineEdit = self.findDefaultValuesInputLineEditFromTableWidget('Kaavamääräysotsikko')
        lineEdit.setText(defaultRegulationTitle)

        if defaultRegulationTitle != "":
            lineEdit = self.findDefaultValuesInputLineEditFromTableWidget("Käyttötarkoituksen lyhenne (esim. A, C)")
            if self.targetLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_ALUE:
                    planNumber = self.yleiskaavaDatabase.getPlanNumberForName(self.dialogCopySettings.comboBoxSpatialPlanName.currentText())
                    landUseClassificationName = self.yleiskaavaUtils.getLandUseClassificationNameForRegulation(planNumber, self.targetSchemaTableName, defaultRegulationTitle)
                    lineEdit.setText(landUseClassificationName)
            else:
                lineEdit.setText(defaultRegulationTitle)

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

        # self.yleiskaavaDatabase.reconnectToDB()

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


        