

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QVariant

from qgis.core import (Qgis, QgsProject, QgsMessageLog)

import os.path


class UpdateIndexingOfFeatures:

    def __init__(self, iface, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = os.path.dirname(__file__)

        self.dialogUpdateIndexingOfFeatures = uic.loadUi(os.path.join(self.plugin_dir, 'yleiskaava_dialog_update_indexing_of_features.ui'))

        self.selectedLayer = None


    def setup(self):
        targetTableNames = sorted(self.yleiskaavaDatabase.getAllTargetSchemaTableNamesShownInCopySourceToTargetUI())
        targetTableNames.insert(0, "Valitse kohdekarttataso")
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.addItems(targetTableNames)
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.currentIndexChanged.connect(self.handleComboBoxChooseTargetLayerIndexChanged)

        self.dialogUpdateIndexingOfFeatures.pushButtonChooseFeatureToAddBetween.clicked.connect(self.chooseLayerFeatureToAddBetween)

        self.dialogUpdateIndexingOfFeatures.comboBoxChooseIndexFieldToUpdate.currentIndexChanged.connect(self.handleComboBoxChooseIndexFieldToUpdateIndexChanged)

    def openDialogUpdateIndexingOfFeatures(self):
        self.dialogUpdateIndexingOfFeatures.show()


    def reset(self):
        if self.selectedLayer is not None:
            try:
                self.selectedLayer.selectionChanged.disconnect(self.handleFeatureSelectionChanged)
            except TypeError:
                pass
            except RuntimeError:
                pass


    def clearForm(self):
        self.reset()
        # TODO päivitä kaikki lomakkeeen osat
        self.dialogUpdateIndexingOfFeatures.pushButtonChooseFeatureToAddBetween.setEnabled(False)
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseIndexFieldToUpdate.clear()

        
    def handleComboBoxChooseTargetLayerIndexChanged(self, index):
        if index == 0:
            self.clearForm()
        else:
            self.dialogUpdateIndexingOfFeatures.pushButtonChooseFeatureToAddBetween.setEnabled(True)
            self.addFieldInfoToComboBoxChooseIndexFieldToUpdate()

        
    def addFieldInfoToComboBoxChooseIndexFieldToUpdate(self):
        userFriendlyTableName = self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.currentText()
        featureType = self.yleiskaavaDatabase.getFeatureTypeForUserFriendlyTargetSchemaTableName(userFriendlyTableName)
        fieldNamesAndTypes = self.yleiskaavaDatabase.getFieldNamesAndTypes(featureType)
        self.shownFieldNamesAndTypes = self.yleiskaavaUtils.getShownFieldNamesAndTypes(fieldNamesAndTypes)

        targetFieldComboBoxTexts = ['Valitse']

        for index, fieldNamesAndType in enumerate(self.shownFieldNamesAndTypes):
            fieldName = fieldNamesAndType["name"]
            fieldTypeName =  fieldNamesAndType["typeName"]
            userFriendlyFieldName = self.yleiskaavaDatabase.getUserFriendlytargetFieldName(fieldName)
            text = self.getTargetFieldComboBoxText(userFriendlyFieldName, fieldName, fieldTypeName)
            targetFieldComboBoxTexts.append(text)

        self.dialogUpdateIndexingOfFeatures.comboBoxChooseIndexFieldToUpdate.clear()
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseIndexFieldToUpdate.addItems(targetFieldComboBoxTexts)


    def getTargetFieldComboBoxText(self, userFriendlyFieldName, targetFieldName, targetFieldTypeName):
        return '' + userFriendlyFieldName + ' (' + targetFieldName + ', ' + targetFieldTypeName + ')'


    def getTargetFieldNameAndTypeFromComboBoxText(self, text):
        QgsMessageLog.logMessage('getTargetFieldNameAndTypeFromComboBoxText, text: ' + str(text), 'Yleiskaava-työkalu', Qgis.Info)
        userFriendlyFieldName, targetFieldNameAndTypeName = text.rsplit(' (', 1)
        targetFieldName, targetFieldTypeName = targetFieldNameAndTypeName[0:-1].split(', ')
        return userFriendlyFieldName, targetFieldName, targetFieldTypeName


    def chooseLayerFeatureToAddBetween(self):
        userFriendlyTableName = self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.currentText()
        if self.selectedLayer is not None:
            try:
                self.selectedLayer.selectionChanged.disconnect(self.handleFeatureSelectionChanged)
            except TypeError:
                pass
            except RuntimeError:
                pass
        self.selectedLayer = QgsProject.instance().mapLayersByName(userFriendlyTableName)[0]
        if self.selectedLayer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('' + userFriendlyTableName + ' karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.selectedLayer.selectionChanged.connect(self.handleFeatureSelectionChanged)
        self.iface.showAttributeTable(self.selectedLayer)
        

    def handleFeatureSelectionChanged(self):
        if self.selectedLayer.selectedFeatureCount() == 1:
            pass
        else:
            pass

    
    def handleComboBoxChooseIndexFieldToUpdateIndexChanged(self, index):
        if index == 0:
            pass
        else:
            pass
    