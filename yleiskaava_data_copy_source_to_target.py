
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QVariant, QSize
from qgis.PyQt.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox, QCheckBox

from qgis.core import (
    Qgis, QgsProject, QgsFeature, QgsField, QgsWkbTypes, QgsMessageLog, QgsMapLayer, QgsVectorLayer,  QgsMapLayerProxyModel, QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform)

from qgis.gui import QgsFilterLineEdit, QgsDateTimeEdit

import os.path
from functools import partial
from collections import Counter
import uuid


from .yleiskaava_dialog_copy_source_data_to_database import Ui_DialogCopySourceDataToDatabase
#from .yleiskaava_dialog_copy_settings import Ui_DialogCopySettings
from .yleiskaava_utils import COPY_ERROR_REASONS

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

        self.dialogCopySourceDataToDatabase = Ui_DialogCopySourceDataToDatabase()
        self.dialogCopySourceDataToDatabaseWidget = QWidget()
        self.dialogCopySourceDataToDatabase.setupUi(self.dialogCopySourceDataToDatabaseWidget)

        self.dialogChooseFeatures = uic.loadUi(os.path.join(self.plugin_dir, 'yleiskaava_dialog_choose_features.ui'))

        self.dialogCopySettings = uic.loadUi(os.path.join(self.plugin_dir, 'yleiskaava_dialog_copy_settings.ui'))
        self.dialogCopySettings.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)

        self.sourceLayer = None

        self.targetSchemaTableName = None
        self.targetLayer = None

        self.targetTableComboBoxes = []
        self.targetFieldNameComboBoxes = []

        self.planNumber = None


    def setup(self):
        self.setupDialogCopySourceDataToDatabase()
        self.setupDialogChooseFeatures()
        self.setupDialogCopySettings()


    def setupDialogCopySourceDataToDatabase(self):
        self.dialogCopySourceDataToDatabase.pushButtonCancel.clicked.connect(self.hideAllDialogs)
        self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.layerChanged.connect(self.handleMapLayerComboBoxSourceChanged)
        self.dialogCopySourceDataToDatabase.pushButtonNext.clicked.connect(self.chooseSourceFeatures)


    def setupDialogChooseFeatures(self):
        self.dialogChooseFeatures.pushButtonCancel.clicked.connect(self.hideAllDialogs)
        self.dialogChooseFeatures.pushButtonPrevious.clicked.connect(self.showDialogCopySourceDataToDatabase)
        self.dialogChooseFeatures.pushButtonNext.clicked.connect(self.chooseCopySettings)


    def setupDialogCopySettings(self):
        self.dialogCopySettings.pushButtonCancel.clicked.connect(self.hideAllDialogs)
        self.dialogCopySettings.pushButtonPrevious.clicked.connect(self.chooseSourceFeatures)
        self.dialogCopySettings.pushButtonRun.clicked.connect(self.runCopySourceDataToDatabase)


    def hideAllDialogs(self):
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
        if layer is not None:
            # QgsMessageLog.logMessage(layer.name(), 'Yleiskaava-työkalu', Qgis.Info)
            self.sourceLayer = layer
            self.updateUIBasedOnSourceLayer(self.sourceLayer)
            
            geomType = self.sourceLayer.geometryType()

            if geomType == QgsWkbTypes.PointGeometry:
                self.selectTargetLayer('Pistemäiset kaavakohteet')
            elif geomType == QgsWkbTypes.LineGeometry:
                self.selectTargetLayer('Viivamaiset kaavakohteet')
        

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

        # QgsMessageLog.logMessage('handleTargetTableSelectChanged', 'Yleiskaava-työkalu', Qgis.Info)
        self.targetSchemaTableName = self.yleiskaavaDatabase.getTargetSchemaTableNameForUserFriendlyTableName(targetTableComboBox.currentText())
        # QgsMessageLog.logMessage('targetTableName: ' + self.targetSchemaTableName + ', rowIndex: ' + str(rowIndex), 'Yleiskaava-työkalu', Qgis.Info)

        if self.targetSchemaTableName != "Valitse kohdekarttataso":
            self.targetLayer = self.yleiskaavaDatabase.createLayerByTargetSchemaTableName(self.targetSchemaTableName)

            #colnames = [desc.name for desc in curs.description]

            # näytä kohdekentissä vain lähdekentän kanssa tyypiltään yhteensopivat kentät

            targetFieldComboBoxTexts = ['']

            for index, field in enumerate(self.targetLayer.fields().toList()):
                targetFieldName = field.name()
                targetFieldTypeName = self.yleiskaavaUtils.getStringTypeForFeatureField(field)
                if self.yleiskaavaUtils.compatibleTypes(sourceFieldTypeName, targetFieldTypeName):
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
        QgsMessageLog.logMessage('getTargetFieldNameAndTypeFromComboBoxText, text: ' + str(text), 'Yleiskaava-työkalu', Qgis.Info)
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
        fieldName = self.getTargetFieldSelectedMoreThanOneTime()
        if fieldName != None:
            return COPY_ERROR_REASONS.TARGET_FIELD_SELECTED_MULTIPLE_TIMES

        return None


    def selectedSourceFeaturesCount(self):
        return self.sourceLayer.selectedFeatureCount()
    
    def isTargetTableSelected(self):
        if self.targetSchemaTableName == None:
            return False
        else:
            return True


    def getTargetFieldSelectedMoreThanOneTime(self):
        targetFieldNames = []

        for i in range(self.getSourceTargetMatchRowCount()):
            # QgsMessageLog.logMessage("rowCount: " + str(self.getSourceTargetMatchRowCount()) + ", i: " + str(i), 'Yleiskaava-työkalu', Qgis.Info)

            targetFieldName = None
            targetFieldTypeName = None
            text = self.dialogCopySourceDataToDatabase.tableWidgetSourceTargetMatch.cellWidget(i, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX).currentText()
            if text != '':
                userFriendlyFieldName, targetFieldName, targetFieldTypeName = self.getTargetFieldNameAndTypeFromComboBoxText(text)

            if targetFieldName in targetFieldNames:
                return targetFieldName
            else:
                targetFieldNames.append(targetFieldName)

        return None


    def chooseSourceFeatures(self):
        # varmista, että self.targetSchemaTableName != None ja tarvittaessa ilmoita käyttäjälle
        if not self.isTargetTableSelected():
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
        # varmista, että ainakin yksi lähde-feature on valittuna ja tarvittaessa ilmoita käyttäjälle
        if self.selectedSourceFeaturesCount() == 0:
            self.iface.messageBar().pushMessage('Yhtään lähdekarttatason kohdetta ei ole valittuna', Qgis.Warning, duration=10)

        self.dialogCopySourceDataToDatabaseWidget.hide()
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
            

        self.initializeDialogCopySettingsPlanPart()
        self.initializeDialogCopySettingsDefaultFieldsPart()


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

        # kun käyttäjä vaihtaa yleiskaavan, niin vaihda automaattisesti kaavataso (tarvittaessa)
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
            spatialTargetTableLayer = self.yleiskaavaDatabase.createLayerByTargetSchemaTableName(self.targetSchemaTableName)

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
            self.iface.messageBar().pushMessage('Kopioidaan lähdeaineiston kohteet tietokantaan', Qgis.Info, duration=10)
            self.copySourceFeaturesToTargetLayer()

            # Päivitä lopuksi työtilan karttatasot, jotka liittyvät T1:n ajoon
            self.yleiskaavaUtils.refreshTargetLayersInProject()
        elif reason == COPY_ERROR_REASONS.SELECTED_FEATURE_COUNT_IS_ZERO:
            self.iface.messageBar().pushMessage('Yhtään lähdekarttatason kohdetta ei ole valittuna', Qgis.Critical)
        elif reason == COPY_ERROR_REASONS.TARGET_TABLE_NOT_SELECTED:
            self.iface.messageBar().pushMessage('Kopioinnin kohdekarttatasoa ei valittu', Qgis.Critical)
        elif reason == COPY_ERROR_REASONS.TARGET_FIELD_SELECTED_MULTIPLE_TIMES:
            self.iface.messageBar().pushMessage('Sama kohdekenttä valittu usealla lähdekentälle', Qgis.Critical)


    def copySourceFeaturesToTargetLayer(self):

        self.planNumber = self.yleiskaavaDatabase.getPlanNumberForName(self.getPlanNameFromCopySettings())
        
        provider = self.targetLayer.dataProvider()

        sourceCRS = self.sourceLayer.crs()
        targetCRS = self.targetLayer.crs()
        transform = None
        if sourceCRS != targetCRS:
            transform = QgsCoordinateTransform(sourceCRS, targetCRS, QgsProject.instance())

        sourceFeatures = self.sourceLayer.getSelectedFeatures()

        #targetLayerFeatures = []

        for sourceFeature in sourceFeatures:

            self.targetLayer.startEditing()

            sourceGeom = sourceFeature.geometry()

            if not sourceGeom.isNull() and transform is not None:
                transformedSourceGeom = QgsGeometry(sourceGeom)
                transformedSourceGeom.transform(transform)
            else:
                transformedSourceGeom = QgsGeometry(sourceGeom)

            targetLayerFeature = QgsFeature()
            targetLayerFeature.setFields(self.targetLayer.fields())
            targetLayerFeature.setAttribute("id", str(uuid.uuid4()))
            targetLayerFeature.setGeometry(transformedSourceGeom)

            self.setTargetFeatureValues(sourceFeature, targetLayerFeature)

            # QgsMessageLog.logMessage("copySourceFeaturesToTargetLayer - targetLayerFeature['nro']: " + str(targetLayerFeature['nro']), 'Yleiskaava-työkalu', Qgis.Info)

            self.handleRegulationAndLandUseClassificationInSourceToTargetCopy(sourceFeature, self.targetSchemaTableName, targetLayerFeature, False)
            self.handleSpatialPlanRelationInSourceToTargetCopy(targetLayerFeature)

            success = provider.addFeatures([targetLayerFeature])
            if not success:
                self.iface.messageBar().pushMessage('Bugi koodissa: copySourceFeaturesToTargetLayer - addFeatures() failed"', Qgis.Critical)
                # QgsMessageLog.logMessage("copySourceFeaturesToTargetLayer - addFeatures() failed", 'Yleiskaava-työkalu', Qgis.Critical)
            else:
                success = self.targetLayer.commitChanges()
                if not success:
                    self.iface.messageBar().pushMessage('Bugi koodissa: copySourceFeaturesToTargetLayer - commitChanges() failed, reason(s): "', Qgis.Critical)
                    # QgsMessageLog.logMessage("copySourceFeaturesToTargetLayer - commitChanges() failed, reason(s): ", 'Yleiskaava-työkalu', Qgis.Critical)
                    for error in self.targetLayer.commitErrors():
                        self.iface.messageBar().pushMessage(error + ".", Qgis.Critical)
                        # QgsMessageLog.logMessage(error + ".", 'Yleiskaava-työkalu', Qgis.Critical)
                else:
                    # pass
                    # QgsMessageLog.logMessage("copySourceFeaturesToTargetLayer - commitChanges() success", 'Yleiskaava-työkalu', Qgis.Info)

                    #targetLayerFeatures.append(targetLayerFeature)

                    # Kaavakohteen pitää olla jo tallennettuna tietokannassa, jotta voidaan lisätä relaatio kaavamääräykseen
                    self.handleRegulationAndLandUseClassificationInSourceToTargetCopy(sourceFeature, self.targetSchemaTableName, targetLayerFeature, True)

        self.notifyUserFinishedCopy()
        

    def notifyUserFinishedCopy(self):
        self.hideAllDialogs()
        self.iface.messageBar().pushMessage('Lähdeaineisto kopioitu tietokantaan', Qgis.Info, 30)

    def getPlanNameFromCopySettings(self):
        return self.dialogCopySettings.comboBoxSpatialPlanName.currentText()


    def handleRegulationAndLandUseClassificationInSourceToTargetCopy(self, sourceFeature, targetSchemaTableName, targetFeature, shouldCreateRelation):
        # Tee tarvittaessa linkki olemassa olevaan tai uuteen kaavamääräykseen. Huomioi asetukset "Luo tarvittaessa uudet kaavamääräykset" ja "Täytä kaavakohteiden käyttötarkoitus kaavamääräyksen mukaan tai päinvastoin"
        # Huomioi, että kaavamääräys voi tulla lähteen käyttötarkoituksen kautta (muokkaa myös asetus-dialogia, jotta ko. asia on mahdollista)
        # Muuttaa lähdekaavamääräyksen isoihin kirjaimiin, jos ei ole valmiiksi
        # Huomioi, että kaavamääräys ja/tai käyttötarkoitus ovat voineet tulla oletusarvojen kautta

        fieldMatches = self.getSourceTargetFieldMatches()
        fieldMatchTargetNames = [fieldMatch["target"] for fieldMatch in fieldMatches]

        sourceRegulationName = self.getSourceFeatureValueForSourceTargetFieldMatch(fieldMatches, sourceFeature, "kaavamaaraysotsikko")
        sourceLandUseClassificationName = self.getSourceFeatureValueForSourceTargetFieldMatch(fieldMatches, sourceFeature, "kayttotarkoitus_lyhenne")

        # QgsMessageLog.logMessage("sourceRegulationName: " + str(sourceRegulationName.value()), 'Yleiskaava-työkalu', Qgis.Info)
        # QgsMessageLog.logMessage("sourceLandUseClassificationName: " + str(sourceLandUseClassificationName.value()), 'Yleiskaava-työkalu', Qgis.Info)

        if "kaavamaaraysotsikko" in fieldMatchTargetNames and not sourceRegulationName.isNull():
            self.handleRegulationInSourceToTargetCopy(sourceFeature, targetFeature, sourceRegulationName, targetSchemaTableName, shouldCreateRelation)
        elif "kayttotarkoitus_lyhenne" in fieldMatchTargetNames and not sourceLandUseClassificationName.isNull():
            self.handleLandUseClassificationInSourceToTargetCopy(sourceFeature, targetFeature, sourceLandUseClassificationName, targetSchemaTableName, shouldCreateRelation)
        elif self.getDefaultValuesRegulationValue() != None:
            self.handleRegulationInSourceToTargetCopy(sourceFeature, targetFeature, self.getDefaultValuesRegulationValue(), targetSchemaTableName, shouldCreateRelation)
        elif self.getDefaultValuesLandUseClassificationValue() != None:
            self.handleLandUseClassificationInSourceToTargetCopy(sourceFeature, targetFeature, self.getDefaultValuesLandUseClassificationValue(), targetSchemaTableName, shouldCreateRelation)


    def getDefaultValuesRegulationValue(self):
        defaultTargetFieldInfos = self.getDefaultTargetFieldInfo()

        for defaultTargetFieldInfo in defaultTargetFieldInfos:
            if defaultTargetFieldInfo["name"] == "kaavamaaraysotsikko":
                return defaultTargetFieldInfo["value"]

    
    def getDefaultValuesLandUseClassificationValue(self):
        defaultTargetFieldInfos = self.getDefaultTargetFieldInfo()

        for defaultTargetFieldInfo in defaultTargetFieldInfos:
            if defaultTargetFieldInfo["name"] == "kayttotarkoitus_lyhenne":
                return defaultTargetFieldInfo["value"]


    def handleLandUseClassificationInSourceToTargetCopy(self, sourceFeature, targetFeature, sourceLandUseClassificationName, targetSchemaTableName, shouldCreateRelation):
        if sourceLandUseClassificationName.value() != "":
            regulationName = self.yleiskaavaUtils.getRegulationNameForLandUseClassification(self.planNumber, targetSchemaTableName, sourceLandUseClassificationName.value())

            regulationList = self.yleiskaavaDatabase.getSpecificRegulations()
            regulationNames = [regulation["kaavamaarays_otsikko"].value() for regulation in regulationList]

            if shouldCreateRelation:
                if regulationName in regulationNames:
                    self.yleiskaavaDatabase.createFeatureRegulationRelation(self.targetSchemaTableName, targetFeature["id"], regulationName)
                elif self.shouldCreateNewRegulation(): # uusi otsikko & kaavamääräys (tai muuten virhe otsikon oikeinkirjoituksessa, tms)
                    self.yleiskaavaDatabase.createSpecificRegulationAndFeatureRegulationRelation(self.targetSchemaTableName, targetFeature["id"], regulationName)
            else:
                if self.shouldFillLandUseClassificationWithRegulation():
                    self.fillRegulationWithLandUseClassification(sourceLandUseClassificationName, targetSchemaTableName, targetFeature)


    def handleRegulationInSourceToTargetCopy(self, sourceFeature, targetFeature, sourceRegulationName, targetSchemaTableName, shouldCreateRelation):
        # QgsMessageLog.logMessage("handleRegulationInSourceToTargetCopy - sourceRegulationName: " + sourceRegulationName.value(), 'Yleiskaava-työkalu', Qgis.Info)
        if sourceRegulationName.value() != "":
            regulationList = self.yleiskaavaDatabase.getSpecificRegulations()
            regulationNames = [regulation["kaavamaarays_otsikko"].value() for regulation in regulationList]

            if shouldCreateRelation:
                if sourceRegulationName.value() in regulationNames:
                    # QgsMessageLog.logMessage("handleRegulationInSourceToTargetCopy - sourceRegulationName.value() in regulationNames", 'Yleiskaava-työkalu', Qgis.Info)
                    self.yleiskaavaDatabase.createFeatureRegulationRelation(self.targetSchemaTableName, targetFeature["id"], sourceRegulationName.value())
                elif self.shouldCreateNewRegulation(): # uusi otsikko & kaavamääräys (tai muuten virhe otsikon oikeinkirjoituksessa, tms)
                    self.yleiskaavaDatabase.createSpecificRegulationAndFeatureRegulationRelation(self.targetSchemaTableName, targetFeature["id"], sourceRegulationName)
            else:
                if self.shouldFillLandUseClassificationWithRegulation():
                    self.fillLandUseClassificationWithRegulation(sourceRegulationName, targetSchemaTableName, targetFeature)


    def fillRegulationWithLandUseClassification(self, landUseClassificationName, targetSchemaTableName, targetFeature):
        regulationName = self.yleiskaavaUtils.getRegulationNameForLandUseClassification(self.planNumber, targetSchemaTableName, landUseClassificationName.value())

        targetFeature.setAttribute("kaavamaaraysotsikko", regulationName)

    
    def fillLandUseClassificationWithRegulation(self, sourceRegulationName, targetSchemaTableName, targetFeature):
        QgsMessageLog.logMessage("fillLandUseClassificationWithRegulation - planNumber: " + str(self.planNumber) + ", targetSchemaTableName: " + targetSchemaTableName + ", sourceRegulationName: " + str(sourceRegulationName.value()), 'Yleiskaava-työkalu', Qgis.Info)

        landUseClassificationName = self.yleiskaavaUtils.getLandUseClassificationNameForRegulation(self.planNumber, targetSchemaTableName, sourceRegulationName.value())

        targetFeature.setAttribute("kayttotarkoitus_lyhenne", landUseClassificationName)


    def shouldCreateNewRegulation(self):
        return self.dialogCopySettings.checkBoxCreateRegulations.isChecked()


    def shouldFillLandUseClassificationWithRegulation(self):
        return self.dialogCopySettings.checkBoxFillLandUseClassificationWithRegulation.isChecked()

    def getSourceFeatureValueForSourceTargetFieldMatch(self, fieldMatches, sourceFeature, targetFieldName):
        value = QVariant()

        for fieldMatch in fieldMatches:
            if targetFieldName == fieldMatch["target"]:
                value = QVariant(sourceFeature[fieldMatch["source"]])
                break
        return value


    def handleSpatialPlanRelationInSourceToTargetCopy(self, targetFeature):
        # yleiskaavaan yhdistäminen, jos asetus "Yhdistä kaavakohteet yleiskaavaan"

        if self.dialogCopySettings.checkBoxLinkToSpatialPlan.isChecked():
            spatialPlanID = self.yleiskaavaDatabase.getSpatialPlanIDForPlanName(self.dialogCopySettings.comboBoxSpatialPlanName.currentText())
            if spatialPlanID != None:
                targetFeature.setAttribute("id_yleiskaava", spatialPlanID)


    def setTargetFeatureValues(self, sourceFeature, targetFeature):
        # tarvittaessa tehdään muunnos esim. int -> string kopioinnissa

        sourceAttrData = self.getSourceFeatureAttributesWithInfo(sourceFeature)
        targetFieldData = self.getTargetFeatureFieldInfo(targetFeature)

        fieldMatches = self.getSourceTargetFieldMatches()

        # QgsMessageLog.logMessage("len(fieldMatches): " + str(len(fieldMatches)), 'Yleiskaava-työkalu', Qgis.Info)

        fieldMatchSourceNames = [fieldMatch["source"] for fieldMatch in fieldMatches]

        defaultTargetFieldInfos = self.getDefaultTargetFieldInfo()

        # QgsMessageLog.logMessage("len(defaultTargetFieldInfos): " + str(len(defaultTargetFieldInfos)), 'Yleiskaava-työkalu', Qgis.Info)

        # QgsMessageLog.logMessage("len(targetFieldData): " + str(len(targetFieldData)), 'Yleiskaava-työkalu', Qgis.Info)

        for targetFieldDataItem in targetFieldData:

            foundFieldMatchForTarget = False

            for sourceAttrDataItem in sourceAttrData: # Jos käyttäjä täsmännyt lähdekentän kohdekenttään ja lähdekentässä on arvo, niin käytä sitä, muuten käytä kohdekenttään oletusarvoa, jos käyttäjä antanut sen

                foundFieldMatch = False
                sourceHadValue = False

                for fieldMatch in fieldMatches:
                    # QgsMessageLog.logMessage("fieldMatch - source: " + fieldMatch["source"] + ", sourceFieldTypeName: " + fieldMatch["sourceFieldTypeName"] + ", target:" + fieldMatch["target"] + ", targetFieldTypeName:" + fieldMatch["targetFieldTypeName"], 'Yleiskaava-työkalu', Qgis.Info)
 
                    if fieldMatch["source"] == sourceAttrDataItem["name"] and fieldMatch["target"] == targetFieldDataItem["name"]:
                        if not sourceAttrDataItem["value"].isNull():
                            # QgsMessageLog.logMessage("setTargetFeatureValues, fieldMatch - sourceHadValue = True - source: " + fieldMatch["source"] + ", sourceFieldTypeName: " + fieldMatch["sourceFieldTypeName"] + ", sourceValue: " + str(sourceAttrDataItem["value"].value()) + ", target:" + fieldMatch["target"] + ", targetFieldTypeName:" + fieldMatch["targetFieldTypeName"], 'Yleiskaava-työkalu', Qgis.Info)

                            attrValue = self.yleiskaavaUtils.getAttributeValueInCompatibleType(targetFieldDataItem["name"], targetFieldDataItem["type"], sourceAttrDataItem["type"], sourceAttrDataItem["value"])
                            if attrValue != None:
                                targetFeature.setAttribute(targetFieldDataItem["name"], attrValue)
                            else:
                                self.iface.messageBar().pushMessage('Lähderivin sarakkeen ' + sourceAttrDataItem["name"] + ' arvoa ei voitu kopioida kohderiville', Qgis.Warning)
                            sourceHadValue = True
                        foundFieldMatch = True
                        foundFieldMatchForTarget = True
                        break                

                if foundFieldMatch and not sourceHadValue:
                    # QgsMessageLog.logMessage("setTargetFeatureValues, foundFieldMatch and not sourceHadValue - targetFieldName: " + targetFieldDataItem["name"] + ", sourceAttrName:" + sourceAttrDataItem["name"], 'Yleiskaava-työkalu', Qgis.Info)
                    for defaultTargetFieldInfo in defaultTargetFieldInfos:
                        # QgsMessageLog.logMessage("defaultTargetFieldInfo - defaultTargetName: " + defaultTargetFieldInfo["name"] + ", targetFieldName: " + targetFieldDataItem["name"], 'Yleiskaava-työkalu', Qgis.Info)
                        
                        if defaultTargetFieldInfo["name"] == targetFieldDataItem["name"]:
                            # QgsMessageLog.logMessage("setTargetFeatureValues, foundFieldMatch and not sourceHadValue, defaultTargetFieldInfo - defaultTargetName = targetFieldName: " + defaultTargetFieldInfo["name"] + ", defaultTargetValue: " + str(defaultTargetFieldInfo["value"].value()), 'Yleiskaava-työkalu', Qgis.Info)
                            
                            if not defaultTargetFieldInfo["value"].isNull():
                                attrValue = self.yleiskaavaUtils.getAttributeValueInCompatibleType(targetFieldDataItem["name"], targetFieldDataItem["type"], defaultTargetFieldInfo["type"], defaultTargetFieldInfo["value"])
                                if attrValue != None:
                                    targetFeature.setAttribute(targetFieldDataItem["name"], attrValue)
                                else:
                                    self.iface.messageBar().pushMessage('Oletusarvoa ei voitu kopioida kohderiville ' + targetFieldDataItem["name"], Qgis.Warning)
                            break

            if not foundFieldMatchForTarget:
                for defaultTargetFieldInfo in defaultTargetFieldInfos:
                    # QgsMessageLog.logMessage("setTargetFeatureValues, not foundFieldMatch - targetFieldName: " + targetFieldDataItem["name"] + ", targetFieldType: " + targetFieldDataItem["type"], 'Yleiskaava-työkalu', Qgis.Info)
                    # QgsMessageLog.logMessage("setTargetFeatureValues, not foundFieldMatch - defaultTargetName: " + defaultTargetFieldInfo["name"] + ", defaultTargetType: " + defaultTargetFieldInfo["type"]  + ", defaultTargetValue: " + str(defaultTargetFieldInfo["value"].value()), 'Yleiskaava-työkalu', Qgis.Info)
                    
                    if defaultTargetFieldInfo["name"] == targetFieldDataItem["name"]:
                        # QgsMessageLog.logMessage("defaultTargetFieldInfo - defaultTargetName = targetFieldName: " + defaultTargetFieldInfo["name"], 'Yleiskaava-työkalu', Qgis.Info)
                        
                        if not defaultTargetFieldInfo["value"].isNull():
                            # QgsMessageLog.logMessage("setTargetFeatureValues, not foundFieldMatch - not defaultTargetFieldInfo['value'].isNull()", 'Yleiskaava-työkalu', Qgis.Info)

                            attrValue = self.yleiskaavaUtils.getAttributeValueInCompatibleType(targetFieldDataItem["name"], targetFieldDataItem["type"], defaultTargetFieldInfo["type"], defaultTargetFieldInfo["value"])

                            # QgsMessageLog.logMessage("setTargetFeatureValues, not foundFieldMatch - attrValue: " + str(attrValue), 'Yleiskaava-työkalu', Qgis.Info)

                            if attrValue != None:
                                targetFeature.setAttribute(targetFieldDataItem["name"], attrValue)
                            else:
                                self.iface.messageBar().pushMessage('Oletusarvoa ei voitu kopioida kohderiville ' + targetFieldDataItem["name"], Qgis.Warning)
                        break


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


    def getSourceFeatureAttributesWithInfo(self, sourceFeature):
        data = []
        for index, field in enumerate(self.sourceLayer.fields().toList()):
            if field.name() != 'id' and self.yleiskaavaUtils.getStringTypeForFeatureField(field) != 'uuid':
                data.append({
                    "name": field.name(),
                    "type": self.yleiskaavaUtils.getStringTypeForFeatureField(field),
                    "value": QVariant(sourceFeature[field.name()])
                })

                # QgsMessageLog.logMessage("getSourceFeatureAttributesWithInfo - name: " + field.name() + ", type: " + str(self.yleiskaavaUtils.getStringTypeForFeatureField(field)) + ", value: " + str(QVariant(sourceFeature[field.name()]).value()), 'Yleiskaava-työkalu', Qgis.Info)

        return data


    def getTargetFeatureFieldInfo(self, targetFeature):
        data = []
        for index, field in enumerate(self.targetLayer.fields().toList()):
            data.append({
                "name": field.name(),
                "type": self.yleiskaavaUtils.getStringTypeForFeatureField(field)
            })

            # QgsMessageLog.logMessage("getTargetFeatureFieldInfo - name: " + field.name() + ", type: " + str(self.yleiskaavaUtils.getStringTypeForFeatureField(field)), 'Yleiskaava-työkalu', Qgis.Info)

        return data


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

    

