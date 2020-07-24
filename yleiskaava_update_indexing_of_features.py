

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QVariant

from qgis.core import (Qgis, QgsProject, QgsFeature, QgsMessageLog)

import os.path
from operator import itemgetter


class UpdateIndexingOfFeatures:

    INDEX_DIRECTION_NAME_ASC = "nouseva"
    INDEX_DIRECTION_NAME_DESC = "laskeva"

    LETTERS = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "å", "ä", "ö"]


    def __init__(self, iface, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = os.path.dirname(__file__)

        self.dialogUpdateIndexingOfFeatures = uic.loadUi(os.path.join(self.plugin_dir, 'yleiskaava_dialog_update_indexing_of_features.ui'))

        self.selectedLayer = None
        

    def setup(self):
        # targetTableNames = sorted(self.yleiskaavaDatabase.getAllTargetSchemaTableNamesShownInCopySourceToTargetUI())
        targetTableNames = self.yleiskaavaDatabase.getAllTargetSchemaTableNamesShownInCopySourceToTargetUI()
        targetTableNames.insert(0, "Valitse kohdekarttataso")
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.addItems(targetTableNames)
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.currentIndexChanged.connect(self.handleComboBoxChooseTargetLayerIndexChanged)
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseLandUseClassification.currentIndexChanged.connect(self.handleComboBoxChooseLandUseClassificationIndexChanged)
        self.dialogUpdateIndexingOfFeatures.pushButtonChooseFeatureToAddBetween.clicked.connect(self.chooseLayerFeatureToAddBetween)
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseIndexFieldToUpdate.currentIndexChanged.connect(self.handleComboBoxChooseIndexFieldToUpdateIndexChanged)
        self.dialogUpdateIndexingOfFeatures.lineEditPrefix.textEdited.connect(self.handleLineEditPrefixEdited)
        self.dialogUpdateIndexingOfFeatures.lineEditPostfix.textEdited.connect(self.handleLineEditPostfixEdited)
        self.dialogUpdateIndexingOfFeatures.lineEditNewIndexValueForFeatureToAddBetween.textEdited.connect(self.handleLineEditNewIndexValueForFeatureToAddBetweenEdited)
        self.dialogUpdateIndexingOfFeatures.comboBoxIndexDirection.addItems([UpdateIndexingOfFeatures.INDEX_DIRECTION_NAME_ASC, UpdateIndexingOfFeatures.INDEX_DIRECTION_NAME_DESC])
        self.dialogUpdateIndexingOfFeatures.comboBoxIndexDirection.currentIndexChanged.connect(self.handleComboBoxIndexDirectionCurrentIndexChanged)
        
        self.dialogUpdateIndexingOfFeatures.pushButtonUpdate.clicked.connect(self.handlePushButtonUpdateClicked)
        self.dialogUpdateIndexingOfFeatures.pushButtonClose.clicked.connect(self.dialogUpdateIndexingOfFeatures.hide)
        

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

        self.selectedLayer = None 


    def clearForm(self):
        self.reset()
        # päivitä kaikki lomakkeeen osat
        self.dialogUpdateIndexingOfFeatures.pushButtonUpdate.setEnabled(False)
        self.dialogUpdateIndexingOfFeatures.pushButtonChooseFeatureToAddBetween.setEnabled(False)
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseIndexFieldToUpdate.clear()
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseLandUseClassification.clear()
        self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesCurrent.clear()
        self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesAfterUpdate.clear()
        self.clearTableWidgetTargetFeatureInfo()
        self.dialogUpdateIndexingOfFeatures.lineEditPrefix.clear()
        self.dialogUpdateIndexingOfFeatures.lineEditPostfix.clear()
        self.dialogUpdateIndexingOfFeatures.lineEditNewIndexValueForFeatureToAddBetween.clear()

    def clearTableWidgetTargetFeatureInfo(self):
        self.dialogUpdateIndexingOfFeatures.tableWidgetTargetFeatureInfo.clearContents()
        self.dialogUpdateIndexingOfFeatures.tableWidgetTargetFeatureInfo.setRowCount(0)
        self.dialogUpdateIndexingOfFeatures.tableWidgetTargetFeatureInfo.setColumnCount(0)
        self.dialogUpdateIndexingOfFeatures.tableWidgetTargetFeatureInfo.setHorizontalHeaderLabels([])

    def handleComboBoxChooseTargetLayerIndexChanged(self, index):
        self.clearForm()
        if index > 0:
            self.fillComboBoxChooseRegulation()
            self.dialogUpdateIndexingOfFeatures.pushButtonChooseFeatureToAddBetween.setEnabled(True)
            self.addFieldInfoToComboBoxChooseIndexFieldToUpdate()


    def fillComboBoxChooseRegulation(self):
        userFriendlyTableName = self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.currentText()
        self.yleiskaavaDatabase.getDistinctLandUseClassificationsOfLayer(userFriendlyTableName)
        landUseClassificationNames = sorted(self.yleiskaavaDatabase.getDistinctLandUseClassificationsOfLayer(userFriendlyTableName))
        landUseClassificationNames.insert(0, "Valitse")
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseLandUseClassification.clear()
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseLandUseClassification.addItems(landUseClassificationNames)
        
        
    def addFieldInfoToComboBoxChooseIndexFieldToUpdate(self):
        userFriendlyTableName = self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.currentText()
        featureType = self.yleiskaavaDatabase.getFeatureTypeForUserFriendlyTargetSchemaTableName(userFriendlyTableName)
        fieldNamesAndTypes = self.yleiskaavaDatabase.getFieldNamesAndTypes(featureType)
        self.shownFieldNamesAndTypes = self.yleiskaavaUtils.getShownFieldNamesAndTypes(fieldNamesAndTypes)

        targetFieldComboBoxTexts = ['Valitse']

        for index, fieldNamesAndType in enumerate(self.shownFieldNamesAndTypes):
            fieldName = fieldNamesAndType["name"]
            fieldTypeName =  fieldNamesAndType["typeName"]
            if fieldTypeName in self.yleiskaavaUtils.getIndexableTypes():
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

    def handleComboBoxChooseLandUseClassificationIndexChanged(self, index):
        self.fillComboBoxTargetLayerFeatureIndexValuesCurrent()
        if index == 0:
            # TODO tyhjennä lomake tarvittavin osin
            pass
        else:
            pass


    def fillComboBoxTargetLayerFeatureIndexValuesCurrent(self):
        if self.dialogUpdateIndexingOfFeatures.comboBoxChooseLandUseClassification.currentIndex() > 0 and self.dialogUpdateIndexingOfFeatures.comboBoxChooseLandUseClassification.currentIndex() > 0 and self.dialogUpdateIndexingOfFeatures.comboBoxChooseIndexFieldToUpdate.currentIndex() > 0:
            userFriendlyTableName = self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.currentText()
            landUseClassification = self.dialogUpdateIndexingOfFeatures.comboBoxChooseLandUseClassification.currentText()
            fieldNameText = self.dialogUpdateIndexingOfFeatures.comboBoxChooseIndexFieldToUpdate.currentText()
            userFriendlyFieldName, fieldName, fieldTypeName = self.getTargetFieldNameAndTypeFromComboBoxText(fieldNameText)
            values = self.yleiskaavaDatabase.getLayerFieldValuesFeaturesHavingLanduseClassification(userFriendlyTableName, landUseClassification, fieldName)
            sortedValues = self.getValidAndSortedValues(values)
            self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesCurrent.clear()
            self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesCurrent.addItems(sortedValues)
            if len(sortedValues) == 0:
                self.iface.messageBar().pushMessage("Valitulla kaavakohdekarttatasolla, käyttötarkoituksella ja indeksikentällä ei ole indeksiarvoja", Qgis.Info, 5)
                # self.iface.messageBar().pushMessage("Valitulla kaavakohdekarttatasolla, käyttötarkoituksella, indeksikentällä ja vakioalku- ja loppuosalla ei voi muodostaa automaattista indeksiä", Qgis.Warning)
        else:
            self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesCurrent.clear()


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
        if self.selectedLayer.selectedFeatureCount() == 1:
            self.handleFeatureSelectionChanged()
        

    def handleFeatureSelectionChanged(self):
        if self.selectedLayer.selectedFeatureCount() == 1:
            features = self.selectedLayer.getSelectedFeatures()
            feature = QgsFeature()
            features.nextFeature(feature)
            self.fillTableWidgetTargetFeatureInfo(feature)
        else:
            self.clearTableWidgetTargetFeatureInfo()
            self.iface.messageBar().pushMessage('' + userFriendlyTableName + ' karttatasolla on valittuna useita kohteita', Qgis.Info, 20)


    def fillTableWidgetTargetFeatureInfo(self, feature):
        self.clearTableWidgetTargetFeatureInfo()
        userFriendlyTableName = self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.currentText()
        featureType = self.yleiskaavaDatabase.getFeatureTypeForUserFriendlyTargetSchemaTableName(userFriendlyTableName)
        fieldNamesAndTypes = self.yleiskaavaDatabase.getFieldNamesAndTypes(featureType)
        shownFieldNamesAndTypes = self.yleiskaavaUtils.getShownFieldNamesAndTypes(fieldNamesAndTypes)

        self.dialogUpdateIndexingOfFeatures.tableWidgetTargetFeatureInfo.setRowCount(1)
        self.dialogUpdateIndexingOfFeatures.tableWidgetTargetFeatureInfo.setColumnCount(len(shownFieldNamesAndTypes))

        userFriendlyFieldNames = []

        for index, fieldNamesAndType in enumerate(shownFieldNamesAndTypes):
            fieldName = fieldNamesAndType["name"]
            fieldTypeName =  fieldNamesAndType["typeName"]
            userFriendlyFieldName = self.yleiskaavaDatabase.getUserFriendlytargetFieldName(fieldName)
            userFriendlyFieldNames.append(userFriendlyFieldName)

            widget = self.yleiskaavaUtils.getWidgetForSpatialFeatureFieldType(fieldTypeName, fieldName)

            if widget != None:
                self.yleiskaavaUtils.setWidgetValueWithFieldType(widget, fieldTypeName, feature[fieldName], fieldName)
                widget.setEnabled(False)
                self.dialogUpdateIndexingOfFeatures.tableWidgetTargetFeatureInfo.setCellWidget(0, index, widget)
            else:
                self.iface.messageBar().pushMessage('Bugi koodissa: fillTableWidgetTargetFeatureInfo widget == None', Qgis.Warning)

        self.dialogUpdateIndexingOfFeatures.tableWidgetTargetFeatureInfo.setHorizontalHeaderLabels(userFriendlyFieldNames)
        self.dialogUpdateIndexingOfFeatures.tableWidgetTargetFeatureInfo.resizeColumnsToContents()


    def handleComboBoxChooseIndexFieldToUpdateIndexChanged(self, index):
        self.fillComboBoxTargetLayerFeatureIndexValuesCurrent()

        if index == 0:
            pass
        else:
            pass
    

    def handleLineEditPrefixEdited(self, text):
        self.fillComboBoxTargetLayerFeatureIndexValuesCurrent()


    def handleLineEditPostfixEdited(self, text):
        self.fillComboBoxTargetLayerFeatureIndexValuesCurrent()


    def handleLineEditNewIndexValueForFeatureToAddBetweenEdited(self, text):
        self.fillComboBoxTargetLayerFeatureIndexValuesAfterUpdate(text)


    def handleComboBoxIndexDirectionCurrentIndexChanged(self, index):
        self.fillComboBoxTargetLayerFeatureIndexValuesCurrent()
        

    def handlePushButtonUpdateClicked(self):
        pass


    def shouldReverse(self):
        if self.dialogUpdateIndexingOfFeatures.comboBoxIndexDirection.currentText() == UpdateIndexingOfFeatures.INDEX_DIRECTION_NAME_ASC:
            return False

        return True


    def getValuePartIfValid(self, value):
        isValid = False
        valuePart = None

        prefix = self.dialogUpdateIndexingOfFeatures.lineEditPrefix.text()
        postfix = self.dialogUpdateIndexingOfFeatures.lineEditPostfix.text()
        # Karsitaan arvot, joilla ei prefix ja postfix
        if value.startswith(prefix) and value.endswith(postfix):
            latterPart = value.split(prefix, 1)[1] if prefix != '' else value
            if latterPart != '' and latterPart.endswith(postfix):
                valuePart = latterPart.rsplit(postfix, 1)[0] if postfix != '' else latterPart
                if valuePart != '':
                    isValid = True

        return isValid, valuePart


    def getValidValuesAndValueParts(self, values):
        validValuesAndValueParts = []
        for value in values:
            isValid, valuePart = self.getValuePartIfValid(value)
            if isValid:
                validValuesAndValueParts.append({
                    'value': value,
                    'valuePart': valuePart
                })

        return validValuesAndValueParts


    def getIndexValueTypesForValues(self, values):

        validValuesAndValueParts = self.getValidValuesAndValueParts(values)

        return self.getIndexValueTypes([valueAndValuePart['valuePart'] for valueAndValuePart in validValuesAndValueParts])
        

    def getIndexValueTypeForValuePart(self, valuePart):
        try:
            int(valuePart)
            return 'Int'
        except ValueError:
            try:
                float(valuePart)
                return 'Float'
            except ValueError:
                pass

        return 'String'


    def getIndexValueTypes(self, valueParts):
        hasFloats = False
        hasInts = False
        hasStrings = False
        # canIndex = True
        for valuePart in valueParts:
            isNumber = False
            try:
                int(valuePart)
                hasInts = True
                isNumber = True
            except ValueError:
                try:
                    float(valuePart)
                    hasFloats = True
                    isNumber = True
                except ValueError:
                    pass
            
            if not isNumber:
                QgsMessageLog.logMessage("getIndexValueTypes - not isNumber, valuePart: " + valuePart, 'Yleiskaava-työkalu', Qgis.Info)
                hasStrings = True

        return hasFloats, hasInts, hasStrings


    def getValidAndSortedValuesAndValueParts(self, values, shouldLowerValueParts):
        validValuesAndValueParts = self.getValidValuesAndValueParts(values)

        # Haetaan indeksiarvojen tyyppi
        hasFloats, hasInts, hasStrings = self.getIndexValueTypes([valueAndValuePart['valuePart'] for valueAndValuePart in validValuesAndValueParts])
        
        # if (hasInts and hasStrings) or (hasFloats and hasStrings):
        #    canIndex = False

        sortedValidValuesAndValueParts = None

        # if canIndex:
        shouldReverse = self.shouldReverse()
        if hasStrings:
            QgsMessageLog.logMessage("getValidAndSortedValues - hasStrings", 'Yleiskaava-työkalu', Qgis.Info)
            sortedValidValuesAndValueParts = sorted(validValuesAndValueParts, key=lambda x: x['valuePart'], reverse = shouldReverse)
            if shouldLowerValueParts:
                for index, sortedValidValuesAndValuePart in enumerate(sortedValidValuesAndValueParts):
                    sortedValidValuesAndValueParts[index]['valuePart'] = sortedValidValuesAndValueParts[index]['valuePart'].lower()

        elif hasFloats:
            QgsMessageLog.logMessage("getValidAndSortedValues - hasFloats", 'Yleiskaava-työkalu', Qgis.Info)
            sortedValidValuesAndValueParts = sorted(validValuesAndValueParts, key=lambda x: float(x['valuePart']), reverse = shouldReverse)
        elif hasInts:
            QgsMessageLog.logMessage("getValidAndSortedValues - hasInts", 'Yleiskaava-työkalu', Qgis.Info)
            sortedValidValuesAndValueParts = sorted(validValuesAndValueParts, key=lambda x: int(x['valuePart']), reverse = shouldReverse)
        else:
            self.iface.messageBar().pushMessage('Bugi koodissa: getValidAndSortedValues', Qgis.Critical)

        return sortedValidValuesAndValueParts


    def getValidAndSortedValues(self, values):
        sortedValues = []
        sortedValidValuesAndValueParts = self.getValidAndSortedValuesAndValueParts(values, False)
        sortedValues = [sortedValidValuesAndValuePart['value'] for sortedValidValuesAndValuePart in sortedValidValuesAndValueParts]
        return sortedValues


    def fillComboBoxTargetLayerFeatureIndexValuesAfterUpdate(self, text):
        isValid = False

        isValid, valuePart = self.getValuePartIfValid(text)
        if isValid:
            currentIndexValues = [self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesCurrent.itemText(i) for i in range(self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesCurrent.count())]
        
            success, newIndexValues = self.getNewIndexValuesSorted(text, valuePart, currentIndexValues)
            if success:
                self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesAfterUpdate.clear()
                self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesAfterUpdate.addItems(newIndexValues)

                self.dialogUpdateIndexingOfFeatures.pushButtonUpdate.setEnabled(True)
            else:
                self.dialogUpdateIndexingOfFeatures.pushButtonUpdate.setEnabled(False)

        else: # ei validi
            self.dialogUpdateIndexingOfFeatures.pushButtonUpdate.setEnabled(False)


    def getNewIndexValuesSorted(self, value, valuePart, currentIndexValues):
        success = False

        if value not in currentIndexValues:
            currentIndexValues.append(value)
            success = True
            newIndexValues = self.getValidAndSortedValues(currentIndexValues)
            return success, newIndexValues
        else:
            # hasFloats, hasInts, hasStrings = self.getIndexValueTypesForValues()
            valueType = self.getIndexValueTypeForValuePart(valuePart)
            sortedValidValuesAndValueParts = self.getValidAndSortedValuesAndValueParts(currentIndexValues, True)

            if valueType == 'String':
                success, newIndexValues = self.addExistingIndexValueToStringValues(value, valuePart.lower(), sortedValidValuesAndValueParts)
                return success, newIndexValues
            elif valueType == 'Float':
                success, newIndexValues = self.addExistingIndexValueToFloatValues(value, valuePart, sortedValidValuesAndValueParts)
                return success, newIndexValues
            else: # if valueType == 'Int':
                success, newIndexValues = self.addExistingIndexValueToIntValues(value, valuePart, sortedValidValuesAndValueParts)
                return success, newIndexValues
                

    def addExistingIndexValueToStringValues(self, value, valuePart, sortedValidValuesAndValueParts):
        # käsittele isoilla ja pienillä kirjaimilla:
        #  - a, b, c, ..
        #  TODO - aa, bb, cc, ..
        #  TODO - i, ii, iii, ..
        success = False
        newIndexValues = []

        currentIndexValues = [sortedValidValuesAndValuePart['value'] for sortedValidValuesAndValuePart in sortedValidValuesAndValueParts]
        currentIndexValueParts = [sortedValidValuesAndValuePart['valuePart'] for sortedValidValuesAndValuePart in sortedValidValuesAndValueParts]
        if not self.yleiskaavaUtils.allStringsInListHaveEqualLength(currentIndexValueParts):
            currentIndexValues.append(value)
            success = True
            newIndexValues = self.getValidAndSortedValues(currentIndexValues)
            return success, newIndexValues
        else:
            indexOfValuePart = currentIndexValueParts.index(valuePart)

            # TODO shouldReverse = self.shouldReverse()

            if currentIndexValueParts[0] == 'a':
                countOfValuesToGet = len(currentIndexValueParts) - indexOfValuePart
                grownIndexValues = self.getAlphaValuesFromLetter(indexOfValuePart, currentIndexValueParts, countOfValuesToGet, value.islower())
                success = True
                newIndexValues = currentIndexValues[:indexOfValuePart] + [value] + grownIndexValues
                return success, newIndexValues
    
        return success, newIndexValues


    def getAlphaValuesFromLetter(self, indexOfValuePart, currentIndexValueParts, countOfValuesToGet, isLower):
        grownIndexValues = []
        prefix = self.dialogUpdateIndexingOfFeatures.lineEditPrefix.text()
        postfix = self.dialogUpdateIndexingOfFeatures.lineEditPostfix.text()

        for i in range(countOfValuesToGet):
            letter = self.getNextLetterFromLetter(currentIndexValueParts[indexOfValuePart + i])
            if not isLower:
                letter = letter.upper()
            grownIndexValues.append(prefix + letter + postfix)

        return grownIndexValues


    def getNextLetterFromLetter(self, letter):
        indexOfLetter = UpdateIndexingOfFeatures.LETTERS.index(letter) + 1
        if indexOfLetter >= len(UpdateIndexingOfFeatures.LETTERS):
            return UpdateIndexingOfFeatures.LETTERS[len(UpdateIndexingOfFeatures.LETTERS) - 1]
        else:
            return UpdateIndexingOfFeatures.LETTERS[indexOfLetter]


    def addExistingIndexValueToFloatValues(self, value, valuePart, sortedValidValuesAndValueParts):
        # TODO käsittele:
        # - 0.1, 0.2, 0.3, ..
        success = False
        newIndexValues = []
        return success, newIndexValues
    

    def addExistingIndexValueToIntValues(self, value, valuePart, sortedValidValuesAndValueParts):
        # käsittele:
        # - 1, 2, 3, ..
        success = False
        newIndexValues = []

        currentIndexValues = [sortedValidValuesAndValuePart['value'] for sortedValidValuesAndValuePart in sortedValidValuesAndValueParts]
        currentIndexValueParts = [sortedValidValuesAndValuePart['valuePart'] for sortedValidValuesAndValuePart in sortedValidValuesAndValueParts]

        indexOfValuePart = currentIndexValueParts.index(valuePart)
        countOfValuesToGet = len(currentIndexValueParts) - indexOfValuePart
        
        prefix = self.dialogUpdateIndexingOfFeatures.lineEditPrefix.text()
        postfix = self.dialogUpdateIndexingOfFeatures.lineEditPostfix.text()

        grownIndexValues = []
        for i in range(countOfValuesToGet):
            grownValue = int(currentIndexValueParts[indexOfValuePart + i]) + 1
            grownIndexValues.append(prefix + str(grownValue) + postfix)

        success = True
        newIndexValues = currentIndexValues[:indexOfValuePart] + [value] + grownIndexValues
        return success, newIndexValues

    