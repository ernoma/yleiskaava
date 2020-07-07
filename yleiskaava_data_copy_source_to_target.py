

from qgis.PyQt.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox

from qgis.core import (Qgis, QgsProject, QgsFeature, QgsField, QgsMessageLog, QgsMapLayer, QgsVectorLayer, QgsAuxiliaryLayer, QgsMapLayerProxyModel)

import psycopg2.extras
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
            "Valitse kohde taulu",
            "yk_yleiskaava.yleiskaava",
            "yk_yleiskaava.kaavaobjekti_alue",
            "yk_yleiskaava.kaavaobjekti_alue_taydentava",
            "yk_yleiskaava.kaavaobjekti_viiva",
            "yk_yleiskaava.kaavaobjekti_piste",
            "yk_yleiskaava.yleismaarays",
            "yk_yleiskaava.kaavamaarays",
            "yk_kuvaustekniikka.teema",
            "yk_prosessi.lahtoaineisto",
            "yk_prosessi.dokumentti"
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

    def updateUIBasedOnSourceLayer(self, layer):

        #self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch = QGridLayout()
        #self.dialogCopySourceDataToDatabasegridLayoutSourceTargetMatch.setObjectName("gridLayoutSourceTargetMatch")
        for i in reversed(range(self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.count())): 
            widgetToRemove = self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.itemAt(i).widget()
            # remove it from the layout list
            self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)

        #self.targetFieldNameComboBoxes = []

        for index, field in enumerate(layer.fields().toList()):
            sourceFieldnameLabel = QLabel(field.name())
            sourceFieldtypeLabel = QLabel(field.typeName())
            targetTableComboBox = QComboBox()
            targetTableComboBox.addItems(sorted(self.tables_yleiskaava))
            targetFieldNameComboBox = QComboBox()
            #self.targetFieldNameComboBoxes.append(targetFieldNameComboBox)
            self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.addWidget(sourceFieldnameLabel, index, DataCopySourceToTarget.SOURCE_FIELD_NAME_INDEX, 1, 1)
            self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.addWidget(sourceFieldtypeLabel, index, DataCopySourceToTarget.SOURCE_FIELD_TYPE_NAME_INDEX, 1, 1)
            self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.addWidget(targetTableComboBox, index, DataCopySourceToTarget.TARGET_TABLE_NAME_INDEX, 1, 1)
            self.dialogCopySourceDataToDatabase.gridLayoutSourceTargetMatch.addWidget(targetFieldNameComboBox, index, DataCopySourceToTarget.TARGET_TABLE_FIELD_NAME_INDEX, 1, 1)

            targetTableComboBox.currentTextChanged.connect(partial(self.handleTargetTableSelectChanged, index, targetTableComboBox, targetFieldNameComboBox))

    def handleTargetTableSelectChanged(self, row, targetTableComboBox, targetFieldNameComboBox):
        # QgsMessageLog.logMessage('handleTargetTableSelectChanged', 'Yleiskaava-työkalu', Qgis.Info)
        targetTableName = targetTableComboBox.currentText()
        QgsMessageLog.logMessage('targetTableName: ' + targetTableName + ', rowIndex: ' + str(row), 'Yleiskaava-työkalu', Qgis.Info)
        if targetTableName != "Valitse kohde taulu":
            schema, table_name = targetTableName.split('.')

            #query = "SELECT * FROM {} LIMIT 0".format(targetTableName)

            connection = self.yleiskaavaDatabase.createDbConnection()
            cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

            query = """select *
               from information_schema.columns
               where table_schema IN ('yk_yleiskaava', 'yk_kuvaustekniikka', 'yk_prosessi')
               order by table_schema, table_name"""

            try:
                cursor.execute(query)
            except Exception as e:
                connection.close()
                self.iface.messageBar().pushMessage('Virhe tietokantakyselyssä tiedostoa',\
                str(e), Qgis.Critical)
                return

            #colnames = [desc.name for desc in curs.description]

            targetFieldNames = []

            for cursorRow in cursor:
                if cursorRow['table_schema'] == schema and cursorRow['table_name'] == table_name:
                    targetFieldNames.append('' + cursorRow['column_name'] + ' (' + cursorRow['data_type'] + ')')

            connection.close()

            #for index, comboBox in enumerate(self.targetFieldNameComboBoxes):
                #comboBox.addItems(colnames)
            #    comboBox.
            targetFieldNameComboBox.clear()
            targetFieldNameComboBox.addItems(targetFieldNames)

