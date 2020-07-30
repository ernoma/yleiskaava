from qgis.PyQt.QtCore import QVariant

from qgis.core import (
    Qgis, QgsFeature,
    QgsMessageLog, QgsMapLayer,
    QgsGeometry, QgsCoordinateTransform,
    QgsTask)

import uuid


class CopySourceDataToDatabaseTask(QgsTask):
    def __init__(self, yleiskaavaUtils, yleiskaavaDatabase, transformContext, planNumber, sourceFeatures, sourceCRS, sourceLayerFields, targetLayer, targetSchemaTableName, shouldLinkToSpatialPlan, spatialPlanName, fieldMatches, includeFieldNamesForMultiValues, targetFieldValueSeparator, defaultFieldNameValueInfos, shouldCreateNewRegulation, shouldFillLandUseClassificationWithRegulation, specificRegulations):
        super().__init__('Kopioidaan kohteita tietokantaan', QgsTask.CanCancel)
        self.exception = None

        self.yleiskaavaUtils = yleiskaavaUtils
        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.transformContext = transformContext
        self.planNumber = planNumber
        self.sourceFeatures = sourceFeatures
        self.sourceCRS = sourceCRS
        self.sourceLayerFields = sourceLayerFields
        self.targetLayer = targetLayer
        self.targetSchemaTableName = targetSchemaTableName
        self.shouldLinkToSpatialPlan = shouldLinkToSpatialPlan
        self.spatialPlanName = spatialPlanName
        self.fieldMatches = fieldMatches
        self.includeFieldNamesForMultiValues = includeFieldNamesForMultiValues
        self.targetFieldValueSeparator = targetFieldValueSeparator
        self.defaultFieldNameValueInfos = defaultFieldNameValueInfos
        self.shouldCreateNewRegulation = shouldCreateNewRegulation
        self.shouldFillLandUseClassificationWithRegulation = shouldFillLandUseClassificationWithRegulation
        self.specificRegulations = specificRegulations
        self.shouldClone = True

    def run(self):
        if self.exception:
            return False

        success = self.copySourceFeaturesToTargetLayer()
        
        return success


    def finished(self, success):
        if not success:
            QgsMessageLog.logMessage('CopySourceDataToDatabaseTask - poikkeus: ' + str(self.exception), 'Yleiskaava-työkalu', Qgis.Critical)
            # raise self.exception
            self.cancel()


    def cancel(self):
        QgsMessageLog.logMessage(
            'CopySourceDataToDatabaseTask "{name}" keskeytettiin'.format(
                name=self.description()),
            'Yleiskaava-työkalu', Qgis.Info)
        super().cancel()
    

    def copySourceFeaturesToTargetLayer(self):
        sourceCRS = self.sourceCRS
        targetCRS = self.targetLayer.crs()
        transform = None
        if sourceCRS != targetCRS:
            transform = QgsCoordinateTransform(sourceCRS, targetCRS, self.transformContext)

        sourceFeatures = self.sourceFeatures

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

            provider = self.targetLayer.dataProvider()
            success = provider.addFeatures([targetLayerFeature])
            if not success:
                pass
                # TODO varoita jotekin käyttäjää
                # self.iface.messageBar().pushMessage('Bugi koodissa: copySourceFeaturesToTargetLayer - addFeatures() failed"', Qgis.Critical)
                # QgsMessageLog.logMessage("copySourceFeaturesToTargetLayer - addFeatures() failed", 'Yleiskaava-työkalu', Qgis.Critical)
            else:
                success = self.targetLayer.commitChanges()
                if not success:
                    pass
                    # TODO varoita jotekin käyttäjää
                    # self.iface.messageBar().pushMessage('Bugi koodissa: copySourceFeaturesToTargetLayer - commitChanges() failed, reason(s): "', Qgis.Critical)
                    # # QgsMessageLog.logMessage("copySourceFeaturesToTargetLayer - commitChanges() failed, reason(s): ", 'Yleiskaava-työkalu', Qgis.Critical)
                    # for error in self.targetLayer.commitErrors():
                    #     self.iface.messageBar().pushMessage(error + ".", Qgis.Critical)
                    #     # QgsMessageLog.logMessage(error + ".", 'Yleiskaava-työkalu', Qgis.Critical)
                else:
                    # pass
                    # QgsMessageLog.logMessage("copySourceFeaturesToTargetLayer - commitChanges() success", 'Yleiskaava-työkalu', Qgis.Info)

                    #targetLayerFeatures.append(targetLayerFeature)

                    # Kaavakohteen pitää olla jo tallennettuna tietokannassa, jotta voidaan lisätä relaatio kaavamääräykseen
                    self.handleRegulationAndLandUseClassificationInSourceToTargetCopy(sourceFeature, self.targetSchemaTableName, targetLayerFeature, True)

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
                            if attrValue != None:
                                attrNames.append(sourceAttrDataItem["name"])
                                attrValues.append(attrValue)
                            else:
                                pass
                                # TODO varoita jotekin käyttäjää
                                # self.iface.messageBar().pushMessage('Lähderivin sarakkeen ' + sourceAttrDataItem["name"] + ' arvoa ei voitu kopioida kohderiville', Qgis.Warning)
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
                        
                        if not defaultTargetFieldInfo["value"].isNull():
                            attrValue = self.yleiskaavaUtils.getAttributeValueInCompatibleType(targetFieldDataItem["name"], targetFieldDataItem["type"], defaultTargetFieldInfo["type"], defaultTargetFieldInfo["value"])
                            if attrValue != None:
                                targetFeature.setAttribute(targetFieldDataItem["name"], attrValue)
                            else:
                                pass
                                # TODO varoita jotekin käyttäjää
                                # self.iface.messageBar().pushMessage('Oletusarvoa ei voitu kopioida kohderiville ' + targetFieldDataItem["name"], Qgis.Warning)
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
                        
                        if not defaultTargetFieldInfo["value"].isNull():
                            # QgsMessageLog.logMessage("setTargetFeatureValues, not foundFieldMatch - not defaultTargetFieldInfo['value'].isNull()", 'Yleiskaava-työkalu', Qgis.Info)

                            attrValue = self.yleiskaavaUtils.getAttributeValueInCompatibleType(targetFieldDataItem["name"], targetFieldDataItem["type"], defaultTargetFieldInfo["type"], defaultTargetFieldInfo["value"])

                            # QgsMessageLog.logMessage("setTargetFeatureValues, not foundFieldMatch - attrValue: " + str(attrValue), 'Yleiskaava-työkalu', Qgis.Info)

                            if attrValue != None:
                                targetFeature.setAttribute(targetFieldDataItem["name"], attrValue)
                            else:
                                pass
                                # TODO varoita jotekin käyttäjää
                                # self.iface.messageBar().pushMessage('Oletusarvoa ei voitu kopioida kohderiville ' + targetFieldDataItem["name"], Qgis.Warning)
                        break


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


    def handleSpatialPlanRelationInSourceToTargetCopy(self, targetFeature):
        # yleiskaavaan yhdistäminen, jos asetus "Yhdistä kaavakohteet yleiskaavaan"

        if self.shouldLinkToSpatialPlan:
            spatialPlanID = self.yleiskaavaDatabase.getSpatialPlanIDForPlanName(self.spatialPlanName)
            if spatialPlanID != None:
                targetFeature.setAttribute("id_yleiskaava", spatialPlanID)


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
            regulationList = self.specificRegulations
            regulationNames = [regulation["kaavamaarays_otsikko"].value() for regulation in regulationList]

            if shouldCreateRelation:
                if sourceRegulationName.value() in regulationNames:
                    # QgsMessageLog.logMessage("handleRegulationInSourceToTargetCopy - sourceRegulationName.value() in regulationNames", 'Yleiskaava-työkalu', Qgis.Info)
                    self.yleiskaavaDatabase.createFeatureRegulationRelation(self.targetSchemaTableName, targetFeature["id"], sourceRegulationName.value(), self.shouldClone)
                elif self.shouldCreateNewRegulation: # uusi otsikko & kaavamääräys (tai muuten virhe otsikon oikeinkirjoituksessa, tms)
                    self.yleiskaavaDatabase.createSpecificRegulationAndFeatureRegulationRelation(self.targetSchemaTableName, targetFeature["id"], sourceRegulationName, self.shouldClone)
            else:
                if self.shouldFillLandUseClassificationWithRegulation:
                    self.fillLandUseClassificationWithRegulation(sourceRegulationName, targetSchemaTableName, targetFeature)


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

            regulationList = self.specificRegulations
            regulationNames = [regulation["kaavamaarays_otsikko"].value() for regulation in regulationList]

            if shouldCreateRelation:
                if regulationName in regulationNames:
                    self.yleiskaavaDatabase.createFeatureRegulationRelation(self.targetSchemaTableName, targetFeature["id"], regulationName, self.shouldClone)
                elif self.shouldCreateNewRegulation: # uusi otsikko & kaavamääräys (tai muuten virhe otsikon oikeinkirjoituksessa, tms)
                    self.yleiskaavaDatabase.createSpecificRegulationAndFeatureRegulationRelation(self.targetSchemaTableName, targetFeature["id"], regulationName, self.shouldClone)
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



