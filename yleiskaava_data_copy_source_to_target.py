
from PyQt5 import uic

from qgis.PyQt.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox

from qgis.core import (
    Qgis, QgsProject, QgsFeature, QgsField, QgsMessageLog, QgsMapLayer, QgsVectorLayer, QgsAuxiliaryLayer, QgsMapLayerProxyModel)

import os.path
from functools import partial
from collections import Counter

from .yleiskaava_database import YleiskaavaDatabase
from .yleiskaava_dialog_copy_source_data_to_database import Ui_DialogCopySourceDataToDatabase
from .yleiskaava_dialog_copy_settings import Ui_DialogCopySettings
from .yleiskaava_utils import levenshteinRatioAndDistance, getStringTypeForFeatureField


class DataCopySourceToTarget:
    
    SOURCE_FIELD_NAME_INDEX = 0
    SOURCE_FIELD_TYPE_NAME_INDEX = 1
    TARGET_TABLE_NAME_INDEX = 2
    TARGET_TABLE_FIELD_NAME_INDEX = 3

    def __init__(self, iface, yleiskaavaDatabase):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase

        self.plugin_dir = os.path.dirname(__file__)

        self.dialogCopySourceDataToDatabase = Ui_DialogCopySourceDataToDatabase()
        self.dialogCopySourceDataToDatabaseWidget = QWidget()
        self.dialogCopySourceDataToDatabase.setupUi(self.dialogCopySourceDataToDatabaseWidget)

        self.dialogChooseFeatures = uic.loadUi(os.path.join(self.plugin_dir, 'yleiskaava_dialog_choose_features.ui'))

        self.dialogCopySettings = Ui_DialogCopySettings()
        self.dialogCopySettingsWidget = QWidget()
        self.dialogCopySettings.setupUi(self.dialogCopySettingsWidget)

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
        self.dialogChooseFeatures.pushButtonNext.clicked.connect(self.chooseCopySettings)

    def setupDialogCopySettings(self):
        self.dialogCopySettings.pushButtonCancel.clicked.connect(self.cancelAndHideAllDialogs)
        self.dialogCopySettings.pushButtonRun.clicked.connect(self.runCopySourceDataToDatabase)

    def showDialogCopySourceDataToDatabase(self):
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

        self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.setFilters(QgsMapLayerProxyModel.VectorLayer)

        self.dialogCopySourceDataToDatabaseWidget.show()
        self.sourceLayer = self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.currentLayer()
        if self.sourceLayer is not None:
            # QgsMessageLog.logMessage(layer.name(), 'Yleiskaava-työkalu', Qgis.Info)
            self.updateUIBasedOnSourceLayer(self.sourceLayer)

    def handleMapLayerComboBoxSourceChanged(self, layer):
        # QgsMessageLog.logMessage(layer.name(), 'Yleiskaava-työkalu', Qgis.Info)
        self.sourceLayer = layer
        self.updateUIBasedOnSourceLayer(self.sourceLayer)

    def updateUIBasedOnSourceLayer(self, sourceLayer):

        #self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch = QGridLayout()
        #self.dialogCopySourceDataToDatabasegridLayoutSourceTargetMatch.setObjectName("gridLayoutSourceTargetMatch")
        for i in reversed(range(self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.count())): 
            widgetToRemove = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAt(i).widget()
            # remove it from the layout list
            self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)

        self.targetTableComboBoxes = []
        self.targetFieldNameComboBoxes = []

        for index, field in enumerate(sourceLayer.fields().toList()):
            if field.name() != 'id' and getStringTypeForFeatureField(field) != 'uuid':
                sourceFieldnameLabel = QLabel(field.name())
                sourceFieldtypeLabel = QLabel(getStringTypeForFeatureField(field))
                
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
        # QgsMessageLog.logMessage('handleTargetTableSelectChanged', 'Yleiskaava-työkalu', Qgis.Info)
        targetTableName = targetTableComboBox.currentText()
        QgsMessageLog.logMessage('targetTableName: ' + targetTableName + ', rowIndex: ' + str(rowIndex), 'Yleiskaava-työkalu', Qgis.Info)

        if targetTableName != "Valitse kohdetaulu":
            targetLayer = self.yleiskaavaDatabase.createLayerByTargetSchemaTableName(targetTableName)

            #colnames = [desc.name for desc in curs.description]

            targetFieldNames = ['']

            for index, field in enumerate(targetLayer.fields().toList()):
                targetFieldName = field.name()
                targetFieldtypeName = getStringTypeForFeatureField(field)
                targetFieldNames.append('' + targetFieldName + ' (' + targetFieldtypeName + ')')
                #QgsMessageLog.logMessage(targetFieldNames[index], 'Yleiskaava-työkalu', Qgis.Info)

            targetFieldNameComboBox.clear()
            targetFieldNameComboBox.addItems(targetFieldNames)

            sourceFieldName = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(rowIndex, DataCopySourceToTarget.SOURCE_FIELD_NAME_INDEX).widget().text()
            sourceFieldTypeName = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAtPosition(rowIndex, DataCopySourceToTarget.SOURCE_FIELD_TYPE_NAME_INDEX).widget().text()

            self.selectBestFittingTargetField(sourceFieldName, sourceFieldTypeName, targetLayer.fields(), targetFieldNameComboBox)

            #
            # Helpfully guess values for other widgets
            #
            for index, tempTargetTableComboBox in enumerate(self.targetTableComboBoxes):
                tempTargetTableName = tempTargetTableComboBox.currentText()
                if tempTargetTableName == "Valitse kohdetaulu":
                    tempTargetTableComboBox.setCurrentText(targetTableName)
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
            targetFieldtypeName = getStringTypeForFeatureField(field)

            levenshtein_ratio = levenshteinRatioAndDistance(sourceFieldName.lower(), targetFieldName)

            if sourceFieldName.lower() == targetFieldName and sourceFieldTypeName == targetFieldtypeName:
                targetFieldNameComboBox.setCurrentIndex(index + 1)
                QgsMessageLog.logMessage('foundMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
                break
            elif sourceFieldName.lower() == targetFieldName and sourceFieldName.lower() != 'id':
                targetFieldNameComboBox.setCurrentIndex(index + 1)
                QgsMessageLog.logMessage('foundMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
                break # should not be possible to have many cols with the same name
            elif sourceFieldName.lower() != 'id' and targetFieldtypeName != 'uuid' and levenshtein_ratio > max_levenshtein_ratio and levenshtein_ratio > 0.5:
                #QgsMessageLog.logMessage('Levenshtein_ratio : ' + str(levenshtein_ratio), 'Yleiskaava-työkalu', Qgis.Info)
                max_levenshtein_ratio = levenshtein_ratio
                targetFieldNameComboBox.setCurrentIndex(index + 1)
                QgsMessageLog.logMessage('foundLevenshtein_ratioMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
            elif (sourceFieldName.lower() in targetFieldName or targetFieldName in sourceFieldName.lower()) and sourceFieldName.lower() != 'id' and targetFieldtypeName != 'uuid':
                #foundMatch = True
                targetFieldNameComboBox.setCurrentIndex(index + 1)
                QgsMessageLog.logMessage('foundPartialNameMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
            # elif sourceFieldTypeName == targetFieldtypeName and not foundMatch:
            #     foundMatch = True
            #     targetFieldNameComboBox.setCurrentIndex(index + 1)
            #     QgsMessageLog.logMessage('foundTypeMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)

    def chooseSourceFeatures(self):
        self.dialogCopySourceDataToDatabaseWidget.hide()
        self.dialogChooseFeatures.show()
        self.iface.showAttributeTable(self.sourceLayer)


    def chooseCopySettings(self):
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

        self.dialogCopySettings.comboBoxLevelOfSpatialPlan.addItems(sorted(planLevelNames))
        self.dialogCopySettings.comboBoxLevelOfSpatialPlan.setCurrentText("paikallinen")

        # TODO hae oletusarvot, jos mahdollista, käyttäjän jo tekemien valintojen muukaan, esim. yleiskaavan nro nimen mukaan



        self.dialogCopySettingsWidget.show()

    
    def runCopySourceDataToDatabase(self):
        pass

    def cancelAndHideAllDialogs(self):
        self.dialogCopySourceDataToDatabaseWidget.hide()
        self.dialogChooseFeatures.hide()
        self.dialogCopySettingsWidget.hide()