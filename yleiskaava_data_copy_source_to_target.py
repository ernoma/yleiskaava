
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox

from qgis.core import (Qgis, QgsProject, QgsFeature, QgsField, QgsMessageLog, QgsMapLayer, QgsVectorLayer, QgsAuxiliaryLayer, QgsMapLayerProxyModel)

from functools import partial

from .yleiskaava_database import YleiskaavaDatabase
from .yleiskaava_dialog_copy_source_data_to_database import Ui_DialogCopySourceDataToDatabase

class DataCopySourceToTarget:
    
    SOURCE_FIELD_NAME_INDEX = 0
    SOURCE_FIELD_TYPE_NAME_INDEX = 1
    TARGET_TABLE_NAME_INDEX = 2
    TARGET_TABLE_FIELD_NAME_INDEX = 3

    def __init__(self, iface, yleiskaavaDatabase):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase

        self.dialogCopySourceDataToDatabase = Ui_DialogCopySourceDataToDatabase()
        self.dialogCopySourceDataToDatabaseWidget = QWidget()
        self.dialogCopySourceDataToDatabase.setupUi(self.dialogCopySourceDataToDatabaseWidget)

        self.tables_yleiskaava = [
            {"name": "Valitse kohdetaulu", "geomFieldName": None},
            {"name": "yk_yleiskaava.yleiskaava", "geomFieldName": "kaavan_ulkorajaus"},
            {"name": "yk_yleiskaava.kaavaobjekti_alue", "geomFieldName": "geom"},
            {"name": "yk_yleiskaava.kaavaobjekti_alue_taydentava", "geomFieldName": "geom"},
            {"name": "yk_yleiskaava.kaavaobjekti_viiva", "geomFieldName": "geom"},
            {"name": "yk_yleiskaava.kaavaobjekti_piste", "geomFieldName": "geom"}#,
            # {"name": "yk_yleiskaava.yleismaarays", "geomFieldName": None},
            # {"name": "yk_yleiskaava.kaavamaarays", "geomFieldName": None},
            # {"name": "yk_kuvaustekniikka.teema", "geomFieldName": None},
            # {"name": "yk_prosessi.lahtoaineisto", "geomFieldName": None},
            # {"name": "yk_prosessi.dokumentti", "geomFieldName": None},
        ]

    def setupDialogCopySourceDataToDatabase(self):
        self.dialogCopySourceDataToDatabase.pushButtonCancel.clicked.connect(self.dialogCopySourceDataToDatabaseWidget.hide)
        self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.layerChanged.connect(self.handleMapLayerComboBoxSourceChanged)

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
        layer = self.dialogCopySourceDataToDatabase.mMapLayerComboBoxSource.currentLayer()
        if layer is not None:
            # QgsMessageLog.logMessage(layer.name(), 'Yleiskaava-työkalu', Qgis.Info)
            self.updateUIBasedOnSourceLayer(layer)

    def handleMapLayerComboBoxSourceChanged(self, layer):
        # QgsMessageLog.logMessage(layer.name(), 'Yleiskaava-työkalu', Qgis.Info)
        self.updateUIBasedOnSourceLayer(layer)

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
            sourceFieldnameLabel = QLabel(field.name())
            sourceFieldtypeLabel = QLabel(self.getStringTypeForField(field))
            
            targetTableComboBox = QComboBox()
            targetTableComboBox.addItems(sorted([item['name'] for item in self.tables_yleiskaava]))
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
            schema, table_name = targetTableName.split('.')

            #query = "SELECT * FROM {} LIMIT 0".format(targetTableName)

            table_item = next(item for item in self.tables_yleiskaava if item["name"] == targetTableName)
            uri = self.yleiskaavaDatabase.createDbURI(schema, table_name, table_item["geomFieldName"])
            
            targetLayer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")

            #colnames = [desc.name for desc in curs.description]

            targetFieldNames = ['']

            for index, field in enumerate(targetLayer.fields().toList()):
                targetFieldName = field.name()
                targetFieldtypeName = self.getStringTypeForField(field)
                targetFieldNames.append('' + targetFieldName + ' (' + targetFieldtypeName + ')')

            #for index, comboBox in enumerate(self.targetFieldNameComboBoxes):
                #comboBox.addItems(colnames)
            #    comboBox.
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
        
        foundMatch = False

        for index, field in enumerate(targetFields.toList()):
            targetFieldName = field.name()
            targetFieldtypeName = self.getStringTypeForField(field)

            if sourceFieldName.lower() == targetFieldName and sourceFieldTypeName == targetFieldtypeName:
                targetFieldNameComboBox.setCurrentIndex(index + 1)
                QgsMessageLog.logMessage('foundMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
                break
            elif sourceFieldName.lower() == targetFieldName: 
                targetFieldNameComboBox.setCurrentIndex(index + 1)
                QgsMessageLog.logMessage('foundMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
                break # should not be possible to have many cols with the same name
            elif sourceFieldName.lower() in targetFieldName or targetFieldName in sourceFieldName.lower():
                foundMatch = True
                targetFieldNameComboBox.setCurrentIndex(index + 1)
                QgsMessageLog.logMessage('foundPartialNameMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)
            # elif sourceFieldTypeName == targetFieldtypeName and not foundMatch:
            #     foundMatch = True
            #     targetFieldNameComboBox.setCurrentIndex(index + 1)
            #     QgsMessageLog.logMessage('foundTypeMatch - sourceFieldName: ' + sourceFieldName + ', targetFieldName: ' + targetFieldName + ', targetFieldName index: ' + str(index + 1), 'Yleiskaava-työkalu', Qgis.Info)

    def getStringTypeForField(self, field):
        if field.typeName() == 'uuid':
            return 'uuid'
        elif field.type() == QVariant.Int:
            return 'Int'
        elif field.type() == QVariant.String:
            return 'String'
        elif field.type() == QVariant.Double:
            return 'Double'
        elif field.type() == QVariant.Date:
            return 'Date'
        else:
            return str(field.type())