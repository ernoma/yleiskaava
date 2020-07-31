from qgis.PyQt.QtCore import QVariant #, pyqtSignal

from qgis.core import (
    Qgis, QgsFeature,
    QgsMessageLog, QgsMapLayer,
    QgsGeometry, QgsCoordinateTransform,
    QgsTask)

import uuid

from .yleiskaava_database import YleiskaavaDatabase



class CopySourceDataToDatabaseTask(QgsTask):

    # # SIGNALS
    # createFeatureRegulationRelation = pyqtSignal(str, str, str)
    # createSpecificRegulationAndFeatureRegulationRelation = pyqtSignal(str, str, str) 

    def __init__(self, yleiskaavaUtils, yleiskaavaDatabase, transformContext, planNumber, targetSchemaTableName, shouldLinkToSpatialPlan, spatialPlanName, spatialPlanID, fieldMatches, includeFieldNamesForMultiValues, targetFieldValueSeparator, defaultFieldNameValueInfos, shouldCreateNewRegulation, shouldFillLandUseClassificationWithRegulation, regulationNames):
        super().__init__('Kopioidaan kohteita tietokantaan', QgsTask.CanCancel)
        self.exceptions = []

        self.yleiskaavaUtils = yleiskaavaUtils
        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.transformContext = transformContext
        self.planNumber = planNumber
        self.targetSchemaTableName = targetSchemaTableName
        self.shouldLinkToSpatialPlan = shouldLinkToSpatialPlan
        self.spatialPlanName = spatialPlanName
        self.spatialPlanID = spatialPlanID
        self.fieldMatches = fieldMatches
        self.includeFieldNamesForMultiValues = includeFieldNamesForMultiValues
        self.targetFieldValueSeparator = targetFieldValueSeparator
        self.defaultFieldNameValueInfos = defaultFieldNameValueInfos
        self.shouldCreateNewRegulation = shouldCreateNewRegulation
        self.shouldFillLandUseClassificationWithRegulation = shouldFillLandUseClassificationWithRegulation
        self.regulationNames = regulationNames

        self.sourceLayer = None
        self.sourceFeatures = None
        self.sourceFeatureCount = None
        self.sourceCRS = None
        self.sourceLayerFields = None
        self.targetLayer = None
        self.targetCRS = None


    def run(self):
        success, reason = self.copySourceFeaturesToTargetLayer()
        # QgsMessageLog.logMessage('run - success: ' + str(success), 'Yleiskaava-työkalu', Qgis.Info)
        return success


    def finished(self, success):
        if not success:
            QgsMessageLog.logMessage('CopySourceDataToDatabaseTask - poikkeuksia: ', 'Yleiskaava-työkalu', Qgis.Critical)
            for exception in self.exceptions:
                QgsMessageLog.logMessage(str(self.exception), 'Yleiskaava-työkalu', Qgis.Critical)
            # raise self.exception
            # self.cancel()


    def cancel(self):
        QgsMessageLog.logMessage(
            'CopySourceDataToDatabaseTask "{name}" keskeytettiin'.format(
                name=self.description()),
            'Yleiskaava-työkalu', Qgis.Info)
        super().cancel()
    

    def copySourceFeaturesToTargetLayer(self):
        success = True
        layers = self.dependentLayers()
        for layer in layers:
            if layer.name() != YleiskaavaDatabase.KAAVAOBJEKTI_ALUE and layer.name() != YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA and layer.name() != YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA and layer.name() != YleiskaavaDatabase.KAAVAOBJEKTI_PISTE and layer.name() != "kaavaobjekti_kaavamaarays_yhteys" and layer.name() != "kaavamääräykset":
                self.sourceLayer = layer
                self.sourceFeatures = layer.selectedFeatures()
                self.sourceFeatureCount = layer.selectedFeatureCount()
                self.sourceCRS = layer.sourceCrs()
                self.sourceLayerFields = layer.fields().toList()
            elif layer.name() != "kaavaobjekti_kaavamaarays_yhteys" and layer.name() != "kaavamääräykset":
                self.targetLayer = layer
                self.targetCRS = layer.sourceCrs()
        
        transform = None
        if self.sourceCRS != self.targetCRS:
            transform = QgsCoordinateTransform(self.sourceCRS, self.targetCRS, self.transformContext)

        for index, sourceFeature in enumerate(self.sourceFeatures):

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

            success = self.setTargetFeatureValues(sourceFeature, targetLayerFeature)
            if not success:
                return success

            # QgsMessageLog.logMessage("copySourceFeaturesToTargetLayer - targetLayerFeature['nro']: " + str(targetLayerFeature['nro']), 'Yleiskaava-työkalu', Qgis.Info)

            self.handleRegulationAndLandUseClassificationInSourceToTargetCopy(sourceFeature, self.targetSchemaTableName, targetLayerFeature, False)
            self.handleSpatialPlanRelationInSourceToTargetCopy(targetLayerFeature)

            provider = self.targetLayer.dataProvider()
            success = provider.addFeatures([targetLayerFeature])
            if not success:
                exception = "provider.addFeatures([targetLayerFeature]) epäonnistui, sourceFeature-attribuutit: "
                for field in self.targetLayer.fields().toList():
                    if sourceFeature[field.name()]:
                        exception += str(sourceFeature[field.name()]) + ", "
                exception = exception[:-2]
                self.exceptions.append(exception)
                break
            else:
                # Kaavakohteen pitää olla jo tallennettuna tietokannassa, jotta voidaan lisätä relaatio kaavamääräykseen
                self.handleRegulationAndLandUseClassificationInSourceToTargetCopy(sourceFeature, self.targetSchemaTableName, targetLayerFeature, True)

                if self.isCanceled():
                    break

                progress = (index / self.sourceFeatureCount) * 100
                self.setProgress(progress)

        return success


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
            sourceHadValue = False

            attrNames = []
            attrValues = []

            for sourceAttrDataItem in sourceAttrData: # Jos käyttäjä täsmännyt lähdekentän kohdekenttään ja lähdekentässä on arvo, niin käytä sitä, muuten käytä kohdekenttään oletusarvoa, jos käyttäjä antanut sen

                # foundFieldMatch = False
                # sourceHadValue = False

                for fieldMatch in fieldMatches:
                    # QgsMessageLog.logMessage("fieldMatch - source: " + fieldMatch["source"] + ", sourceFieldTypeName: " + fieldMatch["sourceFieldTypeName"] + ", target:" + fieldMatch["target"] + ", targetFieldTypeName:" + fieldMatch["targetFieldTypeName"], 'Yleiskaava-työkalu', Qgis.Info)
 
                    if fieldMatch["source"] == sourceAttrDataItem["name"] and fieldMatch["target"] == targetFieldDataItem["name"]:
                        if not sourceAttrDataItem["value"].isNull():
                            # QgsMessageLog.logMessage("setTargetFeatureValues, fieldMatch - sourceHadValue = True - source: " + fieldMatch["source"] + ", sourceFieldTypeName: " + fieldMatch["sourceFieldTypeName"] + ", sourceValue: " + str(sourceAttrDataItem["value"].value()) + ", target:" + fieldMatch["target"] + ", targetFieldTypeName:" + fieldMatch["targetFieldTypeName"], 'Yleiskaava-työkalu', Qgis.Info)

                            attrValue = self.yleiskaavaUtils.getAttributeValueInCompatibleType(targetFieldDataItem["name"], targetFieldDataItem["type"], sourceAttrDataItem["type"], sourceAttrDataItem["value"])
                            if attrValue is not None:
                                attrNames.append(sourceAttrDataItem["name"])
                                attrValues.append(attrValue)
                            else:
                                self.exceptions.append('Lähderivin sarakkeen ' + sourceAttrDataItem["name"] + ' arvoa ei voitu kopioida kohderiville')
                                return False
                            sourceHadValue = True
                        # foundFieldMatch = True
                        foundFieldMatchForTarget = True
                        break                

            if foundFieldMatchForTarget and not sourceHadValue:
                # QgsMessageLog.logMessage("setTargetFeatureValues, foundFieldMatch and not sourceHadValue - targetFieldName: " + targetFieldDataItem["name"] + ", sourceAttrName:" + sourceAttrDataItem["name"], 'Yleiskaava-työkalu', Qgis.Info)
                for defaultTargetFieldInfo in defaultTargetFieldInfos:
                    # QgsMessageLog.logMessage("defaultTargetFieldInfo - defaultTargetName: " + defaultTargetFieldInfo["name"] + ", targetFieldName: " + targetFieldDataItem["name"], 'Yleiskaava-työkalu', Qgis.Info)
                    
                    if defaultTargetFieldInfo["name"] == targetFieldDataItem["name"]:
                        # QgsMessageLog.logMessage("setTargetFeatureValues, foundFieldMatch and not sourceHadValue, defaultTargetFieldInfo - defaultTargetName = targetFieldName: " + defaultTargetFieldInfo["name"] + ", defaultTargetValue: " + str(defaultTargetFieldInfo["value"].value()), 'Yleiskaava-työkalu', Qgis.Info)
                        
                        if defaultTargetFieldInfo["value"] is not None:
                            attrValue = self.yleiskaavaUtils.getAttributeValueInCompatibleType(targetFieldDataItem["name"], targetFieldDataItem["type"], defaultTargetFieldInfo["type"], defaultTargetFieldInfo["value"])
                            if attrValue is not None:
                                targetFeature.setAttribute(targetFieldDataItem["name"], attrValue)
                            else:
                                self.exceptions.append('Oletusarvoa ei voitu kopioida kohderiville ' + targetFieldDataItem["name"])
                                return False
                        break
            elif foundFieldMatchForTarget and sourceHadValue:
                # QgsMessageLog.logMessage("setTargetFeatureValues - foundFieldMatch and sourceHadValue - targetFieldName: " + targetFieldDataItem["name"], 'Yleiskaava-työkalu', Qgis.Info)
                if len(attrValues) == 1:
                    targetFeature.setAttribute(targetFieldDataItem["name"], attrValue)
                else: # len(attrValues) > 1
                    combinedAttrValues = ""
                    for index, attrValue in enumerate(attrValues):
                        if self.includeFieldNamesForMultiValues:
                            combinedAttrValues += attrNames[index] + ": "
                        combinedAttrValues += str(QVariant(attrValue).value()) + self.targetFieldValueSeparator
                    if combinedAttrValues != "" and len(self.targetFieldValueSeparator) > 0:
                        combinedAttrValues = combinedAttrValues[:-(len(self.targetFieldValueSeparator))]
                    targetFeature.setAttribute(targetFieldDataItem["name"], combinedAttrValues)
                    # QgsMessageLog.logMessage("setTargetFeatureValues - foundFieldMatch and sourceHadValue - targetFieldName: " + targetFieldDataItem["name"] + ", combinedAttrValues:" + combinedAttrValues, 'Yleiskaava-työkalu', Qgis.Info)
            elif not foundFieldMatchForTarget:
                for defaultTargetFieldInfo in defaultTargetFieldInfos:
                    # QgsMessageLog.logMessage("setTargetFeatureValues, not foundFieldMatch - targetFieldName: " + targetFieldDataItem["name"] + ", targetFieldType: " + targetFieldDataItem["type"], 'Yleiskaava-työkalu', Qgis.Info)
                    # QgsMessageLog.logMessage("setTargetFeatureValues, not foundFieldMatch - defaultTargetName: " + defaultTargetFieldInfo["name"] + ", defaultTargetType: " + defaultTargetFieldInfo["type"]  + ", defaultTargetValue: " + str(defaultTargetFieldInfo["value"].value()), 'Yleiskaava-työkalu', Qgis.Info)
                    
                    if defaultTargetFieldInfo["name"] == targetFieldDataItem["name"]:
                        # QgsMessageLog.logMessage("defaultTargetFieldInfo - defaultTargetName = targetFieldName: " + defaultTargetFieldInfo["name"], 'Yleiskaava-työkalu', Qgis.Info)
                        
                        if defaultTargetFieldInfo["value"] is not None:
                            # QgsMessageLog.logMessage("setTargetFeatureValues, not foundFieldMatch - not defaultTargetFieldInfo['value'].isNull()", 'Yleiskaava-työkalu', Qgis.Info)

                            attrValue = self.yleiskaavaUtils.getAttributeValueInCompatibleType(targetFieldDataItem["name"], targetFieldDataItem["type"], defaultTargetFieldInfo["type"], defaultTargetFieldInfo["value"])

                            # QgsMessageLog.logMessage("setTargetFeatureValues - not foundFieldMatchForTarget, default attrValue: " + str(attrValue), 'Yleiskaava-työkalu', Qgis.Info)

                            if attrValue is not None:
                                targetFeature.setAttribute(targetFieldDataItem["name"], attrValue)
                            else:
                                self.exceptions.append('Oletusarvoa ei voitu kopioida kohderiville ' + targetFieldDataItem["name"])
                                return False
                        break

        return True


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
        elif self.getDefaultValuesRegulationValue() is not None:
            self.handleRegulationInSourceToTargetCopy(sourceFeature, targetFeature, self.getDefaultValuesRegulationValue(), targetSchemaTableName, shouldCreateRelation)
        elif self.getDefaultValuesLandUseClassificationValue() is not None:
            self.handleLandUseClassificationInSourceToTargetCopy(sourceFeature, targetFeature, self.getDefaultValuesLandUseClassificationValue(), targetSchemaTableName, shouldCreateRelation)


    def handleSpatialPlanRelationInSourceToTargetCopy(self, targetFeature):
        # yleiskaavaan yhdistäminen, jos asetus "Yhdistä kaavakohteet yleiskaavaan"

        if self.shouldLinkToSpatialPlan:
            if self.spatialPlanID is not None:
                targetFeature.setAttribute("id_yleiskaava", self.spatialPlanID)


    def getSourceFeatureAttributesWithInfo(self, sourceFeature):
        data = []
        for index, field in enumerate(self.sourceLayerFields):
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

    
    def getSourceTargetFieldMatches(self):
        return self.fieldMatches


    def getDefaultTargetFieldInfo(self):
        return self.defaultFieldNameValueInfos


    def getSourceFeatureValueForSourceTargetFieldMatch(self, fieldMatches, sourceFeature, targetFieldName):
        value = QVariant()
        for fieldMatch in fieldMatches:
            if targetFieldName == fieldMatch["target"]:
                value = QVariant(sourceFeature[fieldMatch["source"]])
                break
        return value


    def handleRegulationInSourceToTargetCopy(self, sourceFeature, targetFeature, sourceRegulationName, targetSchemaTableName, shouldCreateRelation):
        # QgsMessageLog.logMessage("handleRegulationInSourceToTargetCopy - sourceRegulationName: " + sourceRegulationName.value(), 'Yleiskaava-työkalu', Qgis.Info)
        if sourceRegulationName.value() != "":

            if shouldCreateRelation:
                if sourceRegulationName.value() in self.regulationNames:
                    # QgsMessageLog.logMessage("handleRegulationInSourceToTargetCopy - sourceRegulationName.value() in regulationNames", 'Yleiskaava-työkalu', Qgis.Info)
                     self.yleiskaavaDatabase.createFeatureRegulationRelation(self.targetSchemaTableName, targetFeature["id"], sourceRegulationName.value())
                elif self.shouldCreateNewRegulation: # uusi otsikko & kaavamääräys (tai muuten virhe otsikon oikeinkirjoituksessa, tms)
                    self.yleiskaavaDatabase.createSpecificRegulationAndFeatureRegulationRelation(self.targetSchemaTableName, targetFeature["id"], sourceRegulationName)
                    self.regulationNames.append(sourceRegulationName)
            else:
                if self.shouldFillLandUseClassificationWithRegulation:
                    self.fillLandUseClassificationWithRegulation(sourceRegulationName, targetSchemaTableName, targetFeature)


    def getDefaultValuesRegulationValue(self):
        defaultTargetFieldInfos = self.getDefaultTargetFieldInfo()

        for defaultTargetFieldInfo in defaultTargetFieldInfos:
            if defaultTargetFieldInfo["name"] == "kaavamaaraysotsikko":
                return QVariant(defaultTargetFieldInfo["value"])


    def getDefaultValuesLandUseClassificationValue(self):
        defaultTargetFieldInfos = self.getDefaultTargetFieldInfo()

        for defaultTargetFieldInfo in defaultTargetFieldInfos:
            if defaultTargetFieldInfo["name"] == "kayttotarkoitus_lyhenne":
                return QVariant(defaultTargetFieldInfo["value"])


    def handleLandUseClassificationInSourceToTargetCopy(self, sourceFeature, targetFeature, sourceLandUseClassificationName, targetSchemaTableName, shouldCreateRelation):
        if sourceLandUseClassificationName.value() != "":
            regulationName = self.yleiskaavaUtils.getRegulationNameForLandUseClassification(self.planNumber, targetSchemaTableName, sourceLandUseClassificationName.value())

            if shouldCreateRelation:
                if regulationName in self.regulationNames:
                    self.yleiskaavaDatabase.createFeatureRegulationRelation(self.targetSchemaTableName, targetFeature["id"], regulationName)
                elif self.shouldCreateNewRegulation: # uusi otsikko & kaavamääräys (tai muuten virhe otsikon oikeinkirjoituksessa, tms)
                    self.yleiskaavaDatabase.createSpecificRegulationAndFeatureRegulationRelation(self.targetSchemaTableName, targetFeature["id"], regulationName)
                    self.regulationNames.append(regulationName)
            else:
                if self.shouldFillLandUseClassificationWithRegulation:
                    self.fillRegulationWithLandUseClassification(sourceLandUseClassificationName, targetSchemaTableName, targetFeature)


    def fillRegulationWithLandUseClassification(self, landUseClassificationName, targetSchemaTableName, targetFeature):
        regulationName = self.yleiskaavaUtils.getRegulationNameForLandUseClassification(self.planNumber, targetSchemaTableName, landUseClassificationName.value())

        targetFeature.setAttribute("kaavamaaraysotsikko", regulationName)

    
    def fillLandUseClassificationWithRegulation(self, sourceRegulationName, targetSchemaTableName, targetFeature):
        # QgsMessageLog.logMessage("fillLandUseClassificationWithRegulation - planNumber: " + str(self.planNumber) + ", targetSchemaTableName: " + targetSchemaTableName + ", sourceRegulationName: " + str(sourceRegulationName.value()), 'Yleiskaava-työkalu', Qgis.Info)

        landUseClassificationName = self.yleiskaavaUtils.getLandUseClassificationNameForRegulation(self.planNumber, targetSchemaTableName, sourceRegulationName.value())

        targetFeature.setAttribute("kayttotarkoitus_lyhenne", landUseClassificationName)



