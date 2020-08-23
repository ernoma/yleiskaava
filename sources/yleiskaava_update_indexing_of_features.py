

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QVariant

from qgis.core import (
    Qgis, QgsProject,
    QgsFeature, QgsMessageLog,
    QgsFeatureRequest)

import os.path
from operator import itemgetter


class UpdateIndexingOfFeatures:

    INDEX_DIRECTION_NAME_ASC = "nouseva"
    INDEX_DIRECTION_NAME_DESC = "laskeva"

    LETTERS = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "å", "ä", "ö"]


    def __init__(self, iface, plugin_dir, yleiskaavaSettings, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaSettings = yleiskaavaSettings
        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = plugin_dir

        self.dialogUpdateIndexingOfFeatures = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_update_indexing_of_features.ui'))

        self.selectedLayer = None
        self.selectedFeatureID = None
        self.selectedFieldName = None
        self.sortedFeatureIDsAndValues = None
        self.featureIDsAndNewIndexValues = None

    def setup(self):
        self.yleiskaavaDatabase.reconnectToDB()

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
        # self.dialogUpdateIndexingOfFeatures.comboBoxIndexDirection.addItems([UpdateIndexingOfFeatures.INDEX_DIRECTION_NAME_ASC, UpdateIndexingOfFeatures.INDEX_DIRECTION_NAME_DESC])
        # self.dialogUpdateIndexingOfFeatures.comboBoxIndexDirection.currentIndexChanged.connect(self.handleComboBoxIndexDirectionCurrentIndexChanged)
        
        self.dialogUpdateIndexingOfFeatures.pushButtonUpdate.clicked.connect(self.handlePushButtonUpdateClicked)
        self.dialogUpdateIndexingOfFeatures.pushButtonUpdateAndClose.clicked.connect(self.handlePushButtonUpdateAndCloseClicked)
        self.dialogUpdateIndexingOfFeatures.pushButtonClose.clicked.connect(self.dialogUpdateIndexingOfFeatures.hide)
        

    def openDialogUpdateIndexingOfFeatures(self):
        if self.yleiskaavaSettings.shouldKeepDialogsOnTop():
            self.dialogUpdateIndexingOfFeatures.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        else:
            self.dialogUpdateIndexingOfFeatures.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
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
        self.selectedFeatureID = None
        self.selectedFieldName = None
        self.sortedFeatureIDsAndValues = None
        self.featureIDsAndNewIndexValues = None

    def clearForm(self):
        self.reset()
        # päivitä kaikki lomakkeeen osat
        self.dialogUpdateIndexingOfFeatures.pushButtonUpdate.setEnabled(False)
        self.dialogUpdateIndexingOfFeatures.pushButtonUpdateAndClose.setEnabled(False)
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
        self.yleiskaavaDatabase.reconnectToDB()

        userFriendlyTableName = self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.currentText()
        landUseClassificationNames = sorted(self.yleiskaavaDatabase.getDistinctLandUseClassificationsOfLayer(userFriendlyTableName))
        landUseClassificationNames.insert(0, "Valitse")
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseLandUseClassification.clear()
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseLandUseClassification.addItems(landUseClassificationNames)
        
        
    def addFieldInfoToComboBoxChooseIndexFieldToUpdate(self):
        self.yleiskaavaDatabase.reconnectToDB()

        userFriendlyTableName = self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.currentText()
        featureType = self.yleiskaavaDatabase.getFeatureTypeForUserFriendlyTargetSchemaTableName(userFriendlyTableName)
        fieldNamesAndTypes = self.yleiskaavaDatabase.getFieldNamesAndTypes(featureType)
        self.shownFieldNamesAndTypes = self.yleiskaavaUtils.getShownFieldNamesAndTypes(fieldNamesAndTypes)

        targetFieldComboBoxTexts = ['Valitse']

        for index, fieldNamesAndType in enumerate(self.shownFieldNamesAndTypes):
            fieldName = fieldNamesAndType["name"]
            fieldTypeName =  fieldNamesAndType["type"]
            if fieldTypeName in self.yleiskaavaUtils.getIndexableTypes():
                userFriendlyFieldName = self.yleiskaavaDatabase.getUserFriendlytargetFieldName(fieldName)
                text = self.getTargetFieldComboBoxText(userFriendlyFieldName, fieldName, fieldTypeName)
                targetFieldComboBoxTexts.append(text)

        self.dialogUpdateIndexingOfFeatures.comboBoxChooseIndexFieldToUpdate.clear()
        self.dialogUpdateIndexingOfFeatures.comboBoxChooseIndexFieldToUpdate.addItems(targetFieldComboBoxTexts)


    def getTargetFieldComboBoxText(self, userFriendlyFieldName, targetFieldName, targetFieldTypeName):
        return '' + userFriendlyFieldName + ' (' + targetFieldName + ', ' + targetFieldTypeName + ')'


    def getTargetFieldNameAndTypeFromComboBoxText(self, text):
        # QgsMessageLog.logMessage('getTargetFieldNameAndTypeFromComboBoxText, text: ' + str(text), 'Yleiskaava-työkalu', Qgis.Info)
        userFriendlyFieldName, targetFieldNameAndTypeName = text.rsplit(' (', 1)
        targetFieldName, targetFieldTypeName = targetFieldNameAndTypeName[0:-1].split(', ')
        return userFriendlyFieldName, targetFieldName, targetFieldTypeName

    def handleComboBoxChooseLandUseClassificationIndexChanged(self, index):
        self.fillComboBoxTargetLayerFeatureIndexValuesCurrent()
        if index == 0:
            pass
        else:
            pass


    def fillComboBoxTargetLayerFeatureIndexValuesCurrent(self):
        if self.dialogUpdateIndexingOfFeatures.comboBoxChooseLandUseClassification.currentIndex() > 0 and self.dialogUpdateIndexingOfFeatures.comboBoxChooseLandUseClassification.currentIndex() > 0 and self.dialogUpdateIndexingOfFeatures.comboBoxChooseIndexFieldToUpdate.currentIndex() > 0:
            self.yleiskaavaDatabase.reconnectToDB()

            userFriendlyTableName = self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.currentText()
            landUseClassification = self.dialogUpdateIndexingOfFeatures.comboBoxChooseLandUseClassification.currentText()
            fieldNameText = self.dialogUpdateIndexingOfFeatures.comboBoxChooseIndexFieldToUpdate.currentText()
            userFriendlyFieldName, fieldName, fieldTypeName = self.getTargetFieldNameAndTypeFromComboBoxText(fieldNameText)
            self.selectedFieldName = fieldName
            featureIDsAndValues = self.yleiskaavaDatabase.getLayerFeatureIDsAndFieldValuesForFeaturesHavingLanduseClassification(userFriendlyTableName, landUseClassification, fieldName)
            self.sortedFeatureIDsAndValues = self.getValidAndSortedfeatureIDsAndValues(featureIDsAndValues)
            self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesCurrent.clear()
            self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesCurrent.addItems([item["value"] for item in self.sortedFeatureIDsAndValues])
            if len(self.sortedFeatureIDsAndValues) == 0:
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
        if self.dialogUpdateIndexingOfFeatures.isVisible():
            if self.selectedLayer.selectedFeatureCount() == 1:
                featureRequest = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)
                features = self.selectedLayer.getSelectedFeatures(featureRequest)
                feature = QgsFeature()
                features.nextFeature(feature)
                self.selectedFeatureID = feature["id"]
                self.fillTableWidgetTargetFeatureInfo(feature)
            else:
                self.clearTableWidgetTargetFeatureInfo()
                userFriendlyTableName = self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.currentText()
                self.iface.messageBar().pushMessage('' + userFriendlyTableName + ' karttatasolla on valittuna useita kohteita', Qgis.Info, 20)


    def fillTableWidgetTargetFeatureInfo(self, feature):
        self.clearTableWidgetTargetFeatureInfo()
        userFriendlyTableName = self.dialogUpdateIndexingOfFeatures.comboBoxChooseTargetLayer.currentText()
        
        self.yleiskaavaDatabase.reconnectToDB()

        featureType = self.yleiskaavaDatabase.getFeatureTypeForUserFriendlyTargetSchemaTableName(userFriendlyTableName)
        fieldNamesAndTypes = self.yleiskaavaDatabase.getFieldNamesAndTypes(featureType)
        shownFieldNamesAndTypes = self.yleiskaavaUtils.getShownFieldNamesAndTypes(fieldNamesAndTypes)

        self.dialogUpdateIndexingOfFeatures.tableWidgetTargetFeatureInfo.setRowCount(1)
        self.dialogUpdateIndexingOfFeatures.tableWidgetTargetFeatureInfo.setColumnCount(len(shownFieldNamesAndTypes))

        userFriendlyFieldNames = []

        for index, fieldNamesAndType in enumerate(shownFieldNamesAndTypes):
            fieldName = fieldNamesAndType["name"]
            fieldTypeName =  fieldNamesAndType["type"]
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
        self.updateFeatureValues()

    def handlePushButtonUpdateAndCloseClicked(self):
        self.updateFeatureValues()
        self.dialogUpdateIndexingOfFeatures.hide()


    def shouldReverse(self):
        return False
        # if self.dialogUpdateIndexingOfFeatures.comboBoxIndexDirection.currentText() == UpdateIndexingOfFeatures.INDEX_DIRECTION_NAME_ASC:
        #     return False

        # return True


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


    def getValidFeatureIDsAndValuesAndValueParts(self, featureIDsAndValues):
        validFeatureIDsAndValuesAndValueParts = []
        for featureIDsAndValue in featureIDsAndValues:
            isValid, valuePart = self.getValuePartIfValid(featureIDsAndValue["value"])
            if isValid:
                validFeatureIDsAndValuesAndValueParts.append({
                    'id': featureIDsAndValue["id"],
                    'value': featureIDsAndValue["value"],
                    'valuePart': valuePart
                })

        return validFeatureIDsAndValuesAndValueParts


    # def getIndexFeatureIDsAndValueTypesForValues(self, values):

    #     validValuesAndValueParts = self.getValidFeatureIDsAndValuesAndValueParts(values)

    #     return self.getIndexValueTypes([valueAndValuePart['valuePart'] for valueAndValuePart in validValuesAndValueParts])
        

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
                # QgsMessageLog.logMessage("getIndexValueTypes - not isNumber, valuePart: " + valuePart, 'Yleiskaava-työkalu', Qgis.Info)
                hasStrings = True

        return hasFloats, hasInts, hasStrings


    def getValidAndSortedFeatureIDsAndValuesAndValueParts(self, featureIDsAndValues, shouldLowerValueParts):
        validFeatureIDsAndValuesAndValueParts = self.getValidFeatureIDsAndValuesAndValueParts(featureIDsAndValues)

        # Haetaan indeksiarvojen tyyppi
        hasFloats, hasInts, hasStrings = self.getIndexValueTypes([validFeatureIDsAndValuesAndValuePart['valuePart'] for validFeatureIDsAndValuesAndValuePart in validFeatureIDsAndValuesAndValueParts])
        
        # if (hasInts and hasStrings) or (hasFloats and hasStrings):
        #    canIndex = False

        sortedFeatureIDsAndValidValuesAndValueParts = None

        # if canIndex:
        shouldReverse = self.shouldReverse()
        if hasStrings:
            # QgsMessageLog.logMessage("getValidAndSortedFeatureIDsAndValuesAndValueParts - hasStrings", 'Yleiskaava-työkalu', Qgis.Info)
            sortedFeatureIDsAndValidValuesAndValueParts = sorted(validFeatureIDsAndValuesAndValueParts, key=lambda x: x['valuePart'], reverse = shouldReverse)
            if shouldLowerValueParts:
                for index, sortedFeatureIDsAndValidValuesAndValuePart in enumerate(sortedFeatureIDsAndValidValuesAndValueParts):
                    sortedFeatureIDsAndValidValuesAndValueParts[index]['valuePart'] = sortedFeatureIDsAndValidValuesAndValueParts[index]['valuePart'].lower()

        elif hasFloats:
            # QgsMessageLog.logMessage("getValidAndSortedFeatureIDsAndValuesAndValueParts - hasFloats", 'Yleiskaava-työkalu', Qgis.Info)
            sortedFeatureIDsAndValidValuesAndValueParts = sorted(validFeatureIDsAndValuesAndValueParts, key=lambda x: float(x['valuePart']), reverse = shouldReverse)
        elif hasInts:
            # QgsMessageLog.logMessage("getValidAndSortedFeatureIDsAndValuesAndValueParts - hasInts", 'Yleiskaava-työkalu', Qgis.Info)
            sortedFeatureIDsAndValidValuesAndValueParts = sorted(validFeatureIDsAndValuesAndValueParts, key=lambda x: int(x['valuePart']), reverse = shouldReverse)
        else:
            self.iface.messageBar().pushMessage('Bugi koodissa: getValidAndSortedFeatureIDsAndValuesAndValueParts', Qgis.Critical)

        return sortedFeatureIDsAndValidValuesAndValueParts


    def getValidAndSortedfeatureIDsAndValues(self, featureIDsAndValues):
        sortedFeatureIDsAndValues = []
        sortedValidFeatureIDsAndValuesAndValueParts = self.getValidAndSortedFeatureIDsAndValuesAndValueParts(featureIDsAndValues, False)
        sortedFeatureIDsAndValues = [ { "id": sortedValidFeatureIDsAndValuesAndValuePart['id'], "value": sortedValidFeatureIDsAndValuesAndValuePart['value'] } for sortedValidFeatureIDsAndValuesAndValuePart in sortedValidFeatureIDsAndValuesAndValueParts]
        return sortedFeatureIDsAndValues


    def fillComboBoxTargetLayerFeatureIndexValuesAfterUpdate(self, text):
        isValid = False

        isValid, valuePart = self.getValuePartIfValid(text)
        if isValid:
            currentFeatureIDsAndIndexValues = self.sortedFeatureIDsAndValues
            #currentIndexValues = [self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesCurrent.itemText(i) for i in range(self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesCurrent.count())]
        
            success, self.featureIDsAndNewIndexValues = self.getFeatureIDsAndNewIndexValuesSorted(text, valuePart, currentFeatureIDsAndIndexValues)
            if success:
                self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesAfterUpdate.clear()
                self.dialogUpdateIndexingOfFeatures.comboBoxTargetLayerFeatureIndexValuesAfterUpdate.addItems([item["value"] for item in self.featureIDsAndNewIndexValues])

                self.dialogUpdateIndexingOfFeatures.pushButtonUpdate.setEnabled(True)
                self.dialogUpdateIndexingOfFeatures.pushButtonUpdateAndClose.setEnabled(True)
            else:
                self.dialogUpdateIndexingOfFeatures.pushButtonUpdate.setEnabled(False)
                self.dialogUpdateIndexingOfFeatures.pushButtonUpdateAndClose.setEnabled(False)

        else: # ei validi
            self.featureIDsAndNewIndexValues = None
            # self.dialogUpdateIndexingOfFeatures.lineEditNewIndexValueForFeatureToAddBetween.clear()
            self.dialogUpdateIndexingOfFeatures.pushButtonUpdate.setEnabled(False)
            self.dialogUpdateIndexingOfFeatures.pushButtonUpdateAndClose.setEnabled(False)


    def getFeatureIDsAndNewIndexValuesSorted(self, value, valuePart, currentFeatureIDsAndIndexValues):
        success = False

        if value not in [currentFeatureIDsAndIndexValue["value"] for currentFeatureIDsAndIndexValue in currentFeatureIDsAndIndexValues]:
            currentFeatureIDsAndIndexValues.append({
                "id": self.selectedFeatureID,
                "value": value})
            success = True
            featureIDsAndNewIndexValues = self.getValidAndSortedfeatureIDsAndValues(currentFeatureIDsAndIndexValues)
            return success, featureIDsAndNewIndexValues
        else:
            valueType = self.getIndexValueTypeForValuePart(valuePart)
            sortedValidFeatureIDsAndValuesAndValueParts = self.getValidAndSortedFeatureIDsAndValuesAndValueParts(currentFeatureIDsAndIndexValues, True)

            if valueType == 'String':
                success, featureIDsAndNewIndexValues = self.addExistingIndexValueToStringValues(self.selectedFeatureID, value, valuePart.lower(), sortedValidFeatureIDsAndValuesAndValueParts)
                return success, featureIDsAndNewIndexValues
            elif valueType == 'Float':
                success, featureIDsAndNewIndexValues = self.addExistingIndexValueToFloatValues(self.selectedFeatureID, value, valuePart, sortedValidFeatureIDsAndValuesAndValueParts)
                return success, featureIDsAndNewIndexValues
            else: # if valueType == 'Int':
                success, featureIDsAndNewIndexValues = self.addExistingIndexValueToIntValues(self.selectedFeatureID, value, valuePart, sortedValidFeatureIDsAndValuesAndValueParts)
                return success, featureIDsAndNewIndexValues
                

    def addExistingIndexValueToStringValues(self, featureID, value, valuePart, sortedValidFeatureIDsAndValuesAndValueParts):
        # käsittele isoilla ja pienillä kirjaimilla:
        #  - a, b, c, ..
        success = False
        featureIDsAndnewIndexValues = []

        # currentIndexValues = [sortedValidFeatureIDsAndValuesAndValuePart['value'] for sortedValidFeatureIDsAndValuesAndValuePart in sortedValidFeatureIDsAndValuesAndValueParts]
        currentIndexValueParts = [sortedValidFeatureIDsAndValuesAndValuePart['valuePart'] for sortedValidFeatureIDsAndValuesAndValuePart in sortedValidFeatureIDsAndValuesAndValueParts]
        if not self.yleiskaavaUtils.allStringsInListHaveEqualLength(currentIndexValueParts):
            sortedValidFeatureIDsAndValuesAndValueParts.append({
                "id": featureID,
                "value": value,
                "valuePart": valuePart
            })
            success = True
            featureIDsAndnewIndexValues = self.getValidAndSortedfeatureIDsAndValues(sortedValidFeatureIDsAndValuesAndValueParts)
            return success, featureIDsAndnewIndexValues
        else:
            indexOfValuePart = currentIndexValueParts.index(valuePart)

            # shouldReverse = self.shouldReverse()

            if currentIndexValueParts[0] == 'a':
                countOfValuesToGet = len(currentIndexValueParts) - indexOfValuePart
                featureIDsAndGrownIndexValues = self.getFeatureIDsAndAlphaValuesFromLetter(indexOfValuePart, sortedValidFeatureIDsAndValuesAndValueParts, countOfValuesToGet, value.islower())
                success = True
                addedFeatureIDAndIndexValue = [{
                    "id": featureID,
                    "value": value,
                    "valuePart": valuePart
                }]
                featureIDsAndnewIndexValues = sortedValidFeatureIDsAndValuesAndValueParts[:indexOfValuePart] + addedFeatureIDAndIndexValue + featureIDsAndGrownIndexValues
                return success, featureIDsAndnewIndexValues
    
        return success, featureIDsAndnewIndexValues


    def getFeatureIDsAndAlphaValuesFromLetter(self, indexOfValuePart, sortedValidFeatureIDsAndValuesAndValueParts, countOfValuesToGet, isLower):
        featureIDsAndGrownIndexValues = []
        prefix = self.dialogUpdateIndexingOfFeatures.lineEditPrefix.text()
        postfix = self.dialogUpdateIndexingOfFeatures.lineEditPostfix.text()

        for i in range(countOfValuesToGet):
            letter = self.getNextLetterFromLetter(sortedValidFeatureIDsAndValuesAndValueParts[indexOfValuePart + i]["valuePart"])
            if not isLower:
                letter = letter.upper()
            featureIDsAndGrownIndexValues.append({
                "id": sortedValidFeatureIDsAndValuesAndValueParts[indexOfValuePart + i]["id"],
                "value": prefix + letter + postfix,
                "valuePart": letter })

        return featureIDsAndGrownIndexValues


    def getNextLetterFromLetter(self, letter):
        indexOfLetter = UpdateIndexingOfFeatures.LETTERS.index(letter) + 1
        if indexOfLetter >= len(UpdateIndexingOfFeatures.LETTERS):
            return UpdateIndexingOfFeatures.LETTERS[len(UpdateIndexingOfFeatures.LETTERS) - 1]
        else:
            return UpdateIndexingOfFeatures.LETTERS[indexOfLetter]


    def addExistingIndexValueToFloatValues(self, featureID, value, valuePart, sortedFeatureIDsAndValidValuesAndValueParts):
        success = False
        featureIDsAndNewIndexValues = []
        return success, featureIDsAndNewIndexValues
    

    def addExistingIndexValueToIntValues(self, featureID, value, valuePart, sortedFeatureIDsAndValidValuesAndValueParts):
        # käsittele:
        # - 1, 2, 3, ..
        success = False
        featureIDsAndNewIndexValues = []

        # currentIndexValues = [sortedValidValuesAndValuePart['value'] for sortedValidValuesAndValuePart in sortedValidValuesAndValueParts]
        currentIndexValueParts = [sortedFeatureIDsAndValidValuesAndValuePart['valuePart'] for sortedFeatureIDsAndValidValuesAndValuePart in sortedFeatureIDsAndValidValuesAndValueParts]

        indexOfValuePart = currentIndexValueParts.index(valuePart)
        countOfValuesToGet = len(currentIndexValueParts) - indexOfValuePart
        
        prefix = self.dialogUpdateIndexingOfFeatures.lineEditPrefix.text()
        postfix = self.dialogUpdateIndexingOfFeatures.lineEditPostfix.text()

        featureIDsAndGrownIndexValues = []
        for i in range(countOfValuesToGet):
            grownValue = int(currentIndexValueParts[indexOfValuePart + i]) + 1
            featureIDsAndGrownIndexValues.append({
                "id": sortedFeatureIDsAndValidValuesAndValueParts[indexOfValuePart + i]["id"],
                "value": prefix + str(grownValue) + postfix,
                "valuePart": str(grownValue) })

        success = True
        addedFeatureIDAndIndexValue = [{
            "id": featureID,
            "value": value,
            "valuePart": valuePart
        }]
        featureIDsAndnewIndexValues = sortedFeatureIDsAndValidValuesAndValueParts[:indexOfValuePart] + addedFeatureIDAndIndexValue + featureIDsAndGrownIndexValues
        return success, featureIDsAndnewIndexValues

    
    def updateFeatureValues(self):
        self.yleiskaavaDatabase.reconnectToDB()
        
        success = self.yleiskaavaDatabase.updateSpatialFeaturesWithFieldValues(self.selectedLayer, self.featureIDsAndNewIndexValues, self.selectedFieldName)
        if success:
            self.iface.messageBar().pushMessage('Kaavakohteiden indeksointi päivitetty', Qgis.Info, 30)
            self.clearForm()
            self.yleiskaavaUtils.refreshTargetLayersInProject()
        else:
            self.iface.messageBar().pushMessage('Kaavakohteiden indeksointi ei onnistunut', Qgis.Critical)

            