from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSettings, QVariant
from qgis.core import (Qgis, QgsDataSourceUri, QgsVectorLayer, QgsFeature, QgsWkbTypes, QgsMessageLog)
from qgis.gui import QgsFileWidget

import os.path
#import psycopg2
from configparser import ConfigParser
import uuid

class YleiskaavaDatabase:

    def __init__(self, iface):

        self.iface = iface

        self.yleiskaavaUtils = None

        self.plugin_dir = os.path.dirname(__file__)

        self.settingsDialog = uic.loadUi(os.path.join(self.plugin_dir, 'db_settings.ui'))

        self.connParams = None

        self.yleiskaava_target_tables = [
            {"name": "yk_yleiskaava.yleiskaava", "userFriendlyTableName": 'Yleiskaavan ulkorajaus (yleiskaava)', "geomFieldName": "kaavan_ulkorajaus", "geometryType": QgsWkbTypes.PolygonGeometry, "showInCopySourceToTargetUI": False},
            {"name": "yk_yleiskaava.kaavaobjekti_alue", "userFriendlyTableName": 'Aluevaraukset', "geomFieldName": "geom", "geometryType": QgsWkbTypes.PolygonGeometry, "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.kaavaobjekti_alue_taydentava", "userFriendlyTableName": 'Täydentävät aluekohteet (osa-alueet)', "geomFieldName": "geom", "geometryType": QgsWkbTypes.PolygonGeometry, "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.kaavaobjekti_viiva", "userFriendlyTableName": 'Viivamaiset kaavakohteet', "geomFieldName": "geom", "geometryType": QgsWkbTypes.LineGeometry, "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.kaavaobjekti_piste", "userFriendlyTableName": 'Pistemäiset kaavakohteet', "geomFieldName": "geom", "geometryType": QgsWkbTypes.PointGeometry, "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.yleismaarays", "userFriendlyTableName": 'yleismääräykset', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_yleiskaava.kaavamaarays", "userFriendlyTableName": 'kaavamääräykset', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_kuvaustekniikka.teema", "userFriendlyTableName": 'teemat', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_prosessi.lahtoaineisto", "userFriendlyTableName": 'lahtoaineisto', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_prosessi.dokumentti", "userFriendlyTableName": 'kaavaan liittyvät dokumentit', "geomFieldName": None, "showInCopySourceToTargetUI": False}
        ]

        self.yleiskaava_spatial_target_fields = [
            { "name": "muokkaaja", "userFriendlyName": "Muokkaaja", "type": "String" },
            { "name": "kaavamaaraysotsikko", "userFriendlyName": "Kaavamääräysotsikko", "type": "String" },
            { "name": "kayttotarkoitus_lyhenne", "userFriendlyName": "Käyttötarkoituksen lyhenne (esim. A, C)", "type": "String" },
            { "name": "nro", "userFriendlyName": "Kohteen numero", "type": "String" },
            { "name": "paikan_nimi", "userFriendlyName": "Paikan nimi", "type": "String" },
            { "name": "katuosoite", "userFriendlyName": "Katuosoite", "type": "String" },
            { "name": "karttamerkinta_teksti", "userFriendlyName": "Karttamerkintä (visualisoinnin tuki)", "type": "String" },
            { "name": "pinta_ala_ha", "userFriendlyName": "Pinta-ala (ha)", "type": "Double" },
            { "name": "luokittelu", "userFriendlyName": "Luokittelu (vapaavalintainen)", "type": "String" },
            { "name": "lisatieto", "userFriendlyName": "Lisätietoa kohteesta", "type": "String" },
            { "name": "lisatieto2", "userFriendlyName": "Lisätietoa kohteesta (2)", "type": "String" },
            { "name": "muutos_lisatieto", "userFriendlyName": "Muutokseen liittyvä lisätieto", "type": "String" },
            { "name": "aineisto_lisatieto", "userFriendlyName": "Kohteen tuontiin liittyvä lisätieto", "type": "String" },
            { "name": "voimaantulopvm", "userFriendlyName": "Kohteen voimaantulopäivämäärä", "type": "Date" },
            { "name": "kumoamispvm", "userFriendlyName": "Kohteen mahdollinen kumoamispäivämäärä", "type": "Date" },
            { "name": "version_alkamispvm", "userFriendlyName": "Kohteen luomispäivämäärä", "type": "Date" },
            { "name": "version_loppumispvm", "userFriendlyName": "Kohteen loppumispäivämäärä (milloin poistettu kaavasta)", "type": "Date" },
            { "name": "rakennusoikeus_kem", "userFriendlyName": "Rakennusoikeus (kerrosneliömetriä)", "type": "String" },
            { "name": "rakennusoikeus_lkm", "userFriendlyName": "Rakennusoikeus (lkm)", "type": "String" },
            { "name": "id_yleiskaava", "userFriendlyName": "Kohde kuuluu kaavaan", "type": "uuid" },
            { "name": "id_kansallinen_prosessin_vaihe", "userFriendlyName": "Kaavoitusprosessin vaihe (kansallinen)", "type": "uuid" },
            { "name": "id_kaavakohteen_olemassaolo", "userFriendlyName": "Jos kohteella useampi aluevaraus, niiden suhde (INSPIRE)", "type": "uuid" },
            { "name": "id_kansallisen_kaavakohteen_olemassaolo", "userFriendlyName": "Jos kohteella useampi aluevaraus, niiden suhde (kansallinen)", "type": "uuid" },
            { "name": "id_laillinen_sitovuus", "userFriendlyName": "Laillinen sitovuus (INSPIRE)", "type": "uuid" },
            { "name": "id_prosessin_vaihe", "userFriendlyName": "Prosessin vaihe (INSPIRE)", "type": "uuid" },
            { "name": "id_kaavoitusprosessin_tila", "userFriendlyName": "Kaavoitusprosessin tila", "type": "uuid" }
        ]


    def setYleiskaavaUtils(self, yleiskaavaUtils):
        self.yleiskaavaUtils = yleiskaavaUtils


    def getUserFriendlyTargetSchemaTableNames(self):
        return [item["userFriendlyTableName"] for item in self.yleiskaava_target_tables]


    def getTargetSchemaTableNamesShownInCopySourceToTargetUI(self, geometry_type):
        names = []
        for item in self.yleiskaava_target_tables:
            if item['showInCopySourceToTargetUI'] == True and item["geometryType"] == geometry_type:
                names.append(item['userFriendlyTableName'])
        return names


    def getUserFriendlyTableNameForTargetSchemaTableName(self, name):
        userFriendlyTableName = None
        for item in self.yleiskaava_target_tables:
            if item['showInCopySourceToTargetUI'] == True and item['name'] == name:
                userFriendlyTableName = item['userFriendlyTableName']
                break

        return userFriendlyTableName


    def getTargetSchemaTableNameForUserFriendlyTableName(self, userFriendlyTableName):
        name = None
        for item in self.yleiskaava_target_tables:
            if item['showInCopySourceToTargetUI'] == True and item['userFriendlyTableName'] == userFriendlyTableName:
                name = item['name']
                break

        return name
                

    def getTargetSchemaTableByName(self, name):
        table_item = next((item for item in self.yleiskaava_target_tables if item["name"] == name), None)
        return table_item


    # def getPolgyonFeatureLayer(self):
    #     return self.createLayerByTargetSchemaTableName("yk_yleiskaava.kaavaobjekti_alue")

    # def getSupplementaryPolgyonFeatureLayer(self):
    #     return self.createLayerByTargetSchemaTableName("yk_yleiskaava.kaavaobjekti_alue_taydentava")

    # def getLineFeatureLayer(self):
    #     return self.createLayerByTargetSchemaTableName("yk_yleiskaava.kaavaobjekti_viiva")

    # def getPointFeatureLayer(self):
    #     return self.createLayerByTargetSchemaTableName("yk_yleiskaava.kaavaobjekti_piste")


    def createLayerByTargetSchemaTableName(self, name):
        table_item = self.getTargetSchemaTableByName(name)
        schema, table_name = name.split('.')
        uri = self.createDbURI(schema, table_name, table_item["geomFieldName"])
        targetLayer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")
        #if targetLayer.isValid():
        return targetLayer
        #else:
        #    return None


    def getSpatialPlans(self):
        layer = self.createLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
        features = layer.getFeatures()

        plans = []
        for index, feature in enumerate(features):
            planLevelCode = None
            if feature['id_kaavan_taso'] is not None:
                planLevelCode = self.getYleiskaavaPlanLevelCode(feature['id_kaavan_taso'])

            plans.append({
                "id": feature['id'],
                "nimi": feature['nimi'],
                "nro": feature['nro'],
                "kaavan_taso_koodi": planLevelCode
                })

        return plans


    def getPlanNumberForName(self, planName):
        planNumber = None

        layer = self.createLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
        features = layer.getFeatures()

        plans = []
        for index, feature in enumerate(features):
            if feature['nimi'] == planName:
                if feature['nro'] is not None:
                    planNumber = feature['nro']
                break

        return planNumber


    def getPlanNumberForPlanID(self, planID):
        planNumber = None

        layer = self.createLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
        features = layer.getFeatures()

        plans = []
        for index, feature in enumerate(features):
            if feature['id'] == planID:
                if feature['nro'] is not None:
                    planNumber = feature['nro']
                break

        return planNumber
        

    def getYleiskaavaPlanLevelCodeWithPlanName(self, planName):
        planLevelCode = None

        layer = self.createLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
        features = layer.getFeatures()

        plans = []
        for index, feature in enumerate(features):
            if feature['nimi'] == planName:
                if feature['id_kaavan_taso'] is not None:
                    planLevelCode = self.getYleiskaavaPlanLevelCode(feature['id_kaavan_taso'])
                break

        return planLevelCode


    def getYleiskaavaPlanLevelCode(self, idPlanLevel):
        planLevelCode = None

        planLevelList = self.getYleiskaavaPlanLevelList()
        for planLevel in planLevelList:
            if planLevel["id"] == idPlanLevel:
                planLevelCode = planLevel ["koodi"]
                break

        return planLevelCode


    def getYleiskaavaPlanLevelList(self):
        uri = self.createDbURI("yk_koodiluettelot", "kaavan_taso", None)
        targetLayer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")

        features = targetLayer.getFeatures()
        planLevelList = []
        for index, feature in enumerate(features):
            planLevelList.append({
                "id": feature['id'],
                "koodi": feature['koodi'],
                "kuvaus": feature['kuvaus']})

        return planLevelList


    def getSpatialPlanIDForPlanName(self, planName):
        planID = None

        layer = self.createLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
        features = layer.getFeatures()

        plans = []
        for index, feature in enumerate(features):
            if feature['nimi'] == planName:
                planID = feature['id']
                break

        return planID


    def getSpatialFeaturesWithRegulationForType(self, regulationID, featureType):
        uri = self.createDbURI("yk_yleiskaava", "kaavaobjekti_kaavamaarays_yhteys", None)
        targetLayer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")

        spatialFeatures = []

        for feature in targetLayer.getFeatures():

            spatialFeature = None
            spatialFeatureType = None

            if feature["id_kaavaamarays"].value() == regulationID:
                if not feature["id_kaavaobjekti_" + featureType].isNull():
                    spatialFeature = self.getSpatialFeature(feature["id_kaavaobjekti_" + featureType], featureType)
                    spatialFeatureType = featureType

                if spatialFeature is not None:
                    ids = [tempFeature["feature"]["id"] for tempFeature in spatialFeatures]
                    if spatialFeature["id"] not in [ids]:
                        spatialFeatures.append({
                            "feature": spatialFeature,
                            "type": spatialFeatureType
                        })

                # NOTE ei voi break

        return spatialFeatures

    
    def getSpatialFeature(self, featureID, featureType):
        uri = self.createDbURI("yk_yleiskaava", "kaavaobjekti_" + featureType, None)
        layer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")
        feature = self.findSpatialFeatureFromFeatureLayerWithID(layer, featureID)
        return feature


    def findSpatialFeatureFromFeatureLayerWithID(self, layer, featureID):
        for feature in layer.getFeatures():
            if feature['id'] == featureID:
                return feature

        return None


    def getRegulationCountForSpatialFeature(self, featureID, featureType):
        uri = self.createDbURI("yk_yleiskaava", "kaavaobjekti_kaavamaarays_yhteys", None)
        targetLayer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres") 

        count = 0

        for feature in targetLayer.getFeatures():
            if feature["id_kaavaobjekti_" + featureType] == featureID:
                count += 1

        return count


    def getSpecificRegulations(self):
        uri = self.createDbURI("yk_yleiskaava", "kaavamaarays", None)
        targetLayer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")

        features = targetLayer.getFeatures()
        regulationList = []
        for index, feature in enumerate(features):
            kaavamaarays_otsikko = QVariant(feature["kaavamaarays_otsikko"])
            maaraysteksti = QVariant(feature['maaraysteksti'])
            kuvausteksti = QVariant(feature['kuvaus_teksti'])

            if not kaavamaarays_otsikko.isNull():
                regulationList.append({
                    "id": feature['id'],
                    "alpha_sort_key": str(kaavamaarays_otsikko.value()),
                    "kaavamaarays_otsikko": kaavamaarays_otsikko,
                    "maaraysteksti": maaraysteksti,
                    "kuvaus_teksti": kuvausteksti
                    })

        return regulationList


    def updateRegulation(self, regulationID, regulationTitle, regulationText, regulationDescription):
        uri = self.createDbURI("yk_yleiskaava", "kaavamaarays", None)
        layer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")

        layer.startEditing()

        for feature in layer.getFeatures():
            if feature["id"] == regulationID:
                index = layer.fields().indexFromName("kaavamaarays_otsikko")
                success = layer.changeAttributeValue(feature.id(), index, regulationTitle)
                if not success:
                    self.iface.messageBar().pushMessage('updateRegulation - kaavamaarays_otsikko - changeAttributeValue() failed', Qgis.Critical)
                    return False
                index = layer.fields().indexFromName("maaraysteksti")
                success = layer.changeAttributeValue(feature.id(), index, regulationText)
                if not success:
                    self.iface.messageBar().pushMessage('updateRegulation - maaraysteksti - changeAttributeValue() failed', Qgis.Critical)
                    return False
                index = layer.fields().indexFromName("kuvaus_teksti")
                success = layer.changeAttributeValue(feature.id(), index, regulationDescription)
                if not success:
                    self.iface.messageBar().pushMessage('updateRegulation - kuvaus_teksti - changeAttributeValue() failed', Qgis.Critical)
                    return False
                success = layer.commitChanges()
                if not success:
                    self.iface.messageBar().pushMessage('updateRegulation - commitChanges() failed, reason(s): "', Qgis.Critical)
                    # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - commitChanges() failed, reason(s): ", 'Yleiskaava-työkalu', Qgis.Critical)
                    for error in layer.commitErrors():
                        self.iface.messageBar().pushMessage(error + ".", Qgis.Critical)
                        # QgsMessageLog.logMessage(error + ".", 'Yleiskaava-työkalu', Qgis.Critical)
                    return False
                break

        return True


    def updateSpatialFeatureRegulationAndLandUseClassification(self, featureID, featureType, regulationID, regulationTitle, shouldRemoveOldRegulationRelations):
        # remove old regulation relations if shouldRemoveOldRegulationRelations
        # lisää yhteys kaavaobjekti_kaavamaarays_yhteys-tauluun, jos yhteyttä ei vielä ole


        if shouldRemoveOldRegulationRelations:
            self.removeRegulationRelationsFromSpatialFeature(featureID, featureType)

        if not self.existsFeatureRegulationRelation(featureID, featureType, regulationID):
            self.createFeatureRegulationRelationWithRegulationID("yk_yleiskaava.kaavaobjekti_" + featureType, featureID, regulationID)

        uri = self.createDbURI("yk_yleiskaava", "kaavaobjekti_" + featureType, None)
        layer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")
        feature = self.findSpatialFeatureFromFeatureLayerWithID(layer, featureID)

        layer.startEditing()

        index = layer.fields().indexFromName("kaavamaaraysotsikko")
        success = layer.changeAttributeValue(feature.id(), index, regulationTitle)
        if not success:
                self.iface.messageBar().pushMessage('updateSpatialFeatureRegulationAndLandUseClassificationTexts - kaavamaaraysotsikko - changeAttributeValue() failed', Qgis.Critical)
                return False
        index = layer.fields().indexFromName("kayttotarkoitus_lyhenne")
        landUseClassificationName = regulationTitle
        if not feature["id_yleiskaava"].isNull():
            planNumber = self.getPlanNumberForPlanID(feature["id_yleiskaava"].value())
            landUseClassificationName = self.yleiskaavaUtils.getLandUseClassificationNameForRegulation(planNumber, "kaavaobjekti_" + featureType, regulationTitle)
        success = layer.changeAttributeValue(feature.id(), index, landUseClassificationName)
        if not success:
            self.iface.messageBar().pushMessage('updateSpatialFeatureRegulationAndLandUseClassificationTexts - kayttotarkoitus_lyhenne - changeAttributeValue() failed', Qgis.Critical)

        success = layer.commitChanges()
        if not success:
            self.iface.messageBar().pushMessage('updateSpatialFeatureRegulationAndLandUseClassificationTexts - commitChanges() failed, reason(s): "', Qgis.Critical)
            # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - commitChanges() failed, reason(s): ", 'Yleiskaava-työkalu', Qgis.Critical)
            for error in layer.commitErrors():
                self.iface.messageBar().pushMessage(error + ".", Qgis.Critical)
                # QgsMessageLog.logMessage(error + ".", 'Yleiskaava-työkalu', Qgis.Critical)
            return False

        return True


    def existsFeatureRegulationRelation(self, featureID, featureType, regulationID):
        uri = self.createDbURI("yk_yleiskaava", "kaavaobjekti_kaavamaarays_yhteys", None)
        relationLayer = QgsVectorLayer(uri.uri(False), "temp relation layer", "postgres")

        for feature in relationLayer.getFeatures():
            if (feature["id_kaavamaarays"] == regulationID and feature["id_kaavaobjekti_" + featureType] == featureID):
                return True

        return False


    def removeRegulationRelationsFromSpatialFeature(self, featureID, featureType):
        uri = self.createDbURI("yk_yleiskaava", "kaavaobjekti_kaavamaarays_yhteys", None)
        relationLayer = QgsVectorLayer(uri.uri(False), "temp relation layer", "postgres")

        for feature in relationLayer.getFeatures():
            if (feature["id_kaavaobjekti_" + featureType] == featureID):
                relationLayer.dataProvider().deleteFeatures([feature["id"]])


    def createFeatureRegulationRelation(self, targetSchemaTableName, targetFeatureID, regulationTitle):
        regulationID = self.findRegulationID(regulationTitle)

        self.createFeatureRegulationRelationWithRegulationID(targetSchemaTableName, targetFeatureID, regulationID)


    def createFeatureRegulationRelationWithRegulationID(self, targetSchemaTableName, targetFeatureID, regulationID):
        # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - targetSchemaTableName: " + targetSchemaTableName + ", targetFeatureID: " + str(targetFeatureID) + ", regulationID: " + str(regulationID), 'Yleiskaava-työkalu', Qgis.Info)

        uri = self.createDbURI("yk_yleiskaava", "kaavaobjekti_kaavamaarays_yhteys", None)
        relationLayer = QgsVectorLayer(uri.uri(False), "temp relation layer", "postgres")

        schema, table_name = targetSchemaTableName.split('.')


        relationLayer.startEditing()

        relationLayerFeature = QgsFeature()
        relationLayerFeature.setFields(relationLayer.fields())
        relationLayerFeature.setAttribute("id", str(uuid.uuid4()))
        relationLayerFeature.setAttribute("id_" + table_name, targetFeatureID)
        relationLayerFeature.setAttribute("id_kaavamaarays", regulationID)

        provider = relationLayer.dataProvider()
        
        success = provider.addFeatures([relationLayerFeature])
        if not success:
            self.iface.messageBar().pushMessage('Bugi koodissa: createFeatureRegulationRelationWithRegulationID - addFeatures() failed"', Qgis.Critical)
            # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - addFeatures() failed", 'Yleiskaava-työkalu', Qgis.Critical)
        else:
            success = relationLayer.commitChanges()
            if not success:
                self.iface.messageBar().pushMessage('Bugi koodissa: createFeatureRegulationRelationWithRegulationID - commitChanges() failed, reason(s): "', Qgis.Critical)
                # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - commitChanges() failed, reason(s): ", 'Yleiskaava-työkalu', Qgis.Critical)
                for error in relationLayer.commitErrors():
                    self.iface.messageBar().pushMessage(error + ".", Qgis.Critical)
                    # QgsMessageLog.logMessage(error + ".", 'Yleiskaava-työkalu', Qgis.Critical)
            else:
                pass
                # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - commitChanges() success", 'Yleiskaava-työkalu', Qgis.Info)


    def findRegulationID(self, regulationName):
        regulationList = self.getSpecificRegulations()

        regulationID = None
        for regulation in regulationList:
            if regulation["kaavamaarays_otsikko"].value() == regulationName:
                regulationID = regulation["id"]
                break

        return regulationID


    def createSpecificRegulationAndFeatureRegulationRelation(self, targetSchemaTableName, targetFeatureID, regulationName):
        uri = self.createDbURI("yk_yleiskaava", "kaavamaarays", None)
        regulationLayer = QgsVectorLayer(uri.uri(False), "temp regulation layer", "postgres")

        regulationID = str(uuid.uuid4())

        regulationFeature = QgsFeature()
        regulationFeature.setFields(regulationLayer.fields())
        regulationFeature.setAttribute("id", regulationID)
        regulationFeature.setAttribute("kaavamaarays_otsikko", regulationName)
        regulationLayer.startEditing()
        provider = regulationLayer.dataProvider()
        provider.addFeatures([regulationFeature])
        regulationLayer.commitChanges()

        self.createFeatureRegulationRelationWithRegulationID(targetSchemaTableName, targetFeatureID, regulationID)


    def getCodeListValuesForPlanObjectField(self, targetFieldName):
        schema, table_name = ("yk_koodiluettelot." + targetFieldName[3:]).split('.')
        uri = self.createDbURI(schema, table_name, None)
        targetLayer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")
        features = targetLayer.getFeatures()
        values = None
        # if table_name == "kansallinen_prosessin_vaihe" or table_name == "prosessin_vaihe" or table_name == "kaavoitusprosessin_tila" or table_name == "laillinen_sitovuus":
        values = [feature['koodi'] for feature in features]

        return values


    def getCodeListUUIDForPlanObjectFieldCodeValue(self, targetFieldName, value):
        schema, table_name = ("yk_koodiluettelot." + targetFieldName[3:]).split('.')
        uri = self.createDbURI(schema, table_name, None)
        targetLayer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")
        features = targetLayer.getFeatures()
        uuid = None
        # if table_name == "kansallinen_prosessin_vaihe" or table_name == "prosessin_vaihe" or table_name == "kaavoitusprosessin_tila" or table_name == "laillinen_sitovuus":
        for feature in features:
            if feature['koodi'] == value:
                uuid =  feature['id']
                break
        return uuid


    def getSchemaTableFields(self, name):
        table_item = self.getTargetSchemaTableByName(name)
        schema, table_name = name.split('.')
        uri = self.createDbURI(schema, table_name, table_item["geomFieldName"])
        layer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")
        return layer.fields().toList()


    def createDbURI(self, schema, table_name, geomFieldName):
        self.connParams = self.readConnectionParamsFromInput()

        uri = QgsDataSourceUri()
        uri.setConnection(self.connParams['host'],\
            self.connParams['port'], self.connParams['database'],\
            self.connParams['user'], self.connParams['password'])

        uri.setDataSource(schema, table_name, geomFieldName)

        return uri


    # def createDbConnection(self):
    #     '''Creates a database connection and cursor based on connection params'''

    #     self.connParams = self.readConnectionParamsFromInput()
    #     # QgsMessageLog.logMessage(self.connParams['host'], 'Yleiskaava-työkalu', Qgis.Info)
    #     # QgsMessageLog.logMessage(self.connParams['port'], 'Yleiskaava-työkalu', Qgis.Info)
    #     # QgsMessageLog.logMessage(self.connParams['database'], 'Yleiskaava-työkalu', Qgis.Info)
    #     # QgsMessageLog.logMessage(self.connParams['user'], 'Yleiskaava-työkalu', Qgis.Info)
    #     # QgsMessageLog.logMessage(self.connParams['password'], 'Yleiskaava-työkalu', Qgis.Info)

    #     if '' in list(self.connParams.values()):
    #         raise Exception('Virhe yhdistäessä tietokantaan: täytä puuttuvat yhteystiedot')
    #     try:
    #         conn = psycopg2.connect(host=self.connParams['host'],\
    #             port=self.connParams['port'], database=self.connParams['database'],\
    #             user=self.connParams['user'], password=self.connParams['password'],\
    #             connect_timeout=3)
    #         return conn
    #     except Exception as e:
    #         raise e

    def displaySettingsDialog(self):
            '''Sets up and displays the settings dialog'''
            self.settingsDialog.show()
            self.settingsDialog.configFileInput.setStorageMode(QgsFileWidget.GetFile)
            self.settingsDialog.configFileInput.setFilePath(QSettings().value\
                ("/yleiskaava_tyokalu/configFilePath", "", type=str))
            self.settingsDialog.loadFileButton.clicked.connect(self.setConnectionParamsFromFile)

            #result = self.settingsDialog.show()
            #if result:
            #    self.connParams = self.readConnectionParamsFromInput()


    def setConnectionParamsFromFile(self):
        '''Reads connection parameters from file and sets them to the input fields'''
        filePath = self.settingsDialog.configFileInput.filePath()
        QSettings().setValue("/yleiskaava_tyokalu/configFilePath", filePath)

        try:
            dbParams = self.parseConfigFile(filePath)
        except Exception as e:
            self.iface.messageBar().pushMessage('Virhe luettaessa tiedostoa',\
                str(e), Qgis.Warning, duration=10)

        self.setConnectionParamsFromInput(dbParams)
        self.connParams = self.readConnectionParamsFromInput()


    def parseConfigFile(self, filePath):
        '''Reads configuration file and returns parameters as a dict'''
        # Setup an empty dict with correct keys to avoid keyerrors
        dbParams = {
            'host': '',
            'port': '',
            'database': '',
            'user': '',
            'password': ''
        }
        if not os.path.exists(filePath):
            self.iface.messageBar().pushMessage('Virhe', 'Tiedostoa ei voitu lukea',\
                Qgis.Warning)
            return dbParams

        parser = ConfigParser()
        parser.read(filePath)
        if parser.has_section('postgresql'):
            params = parser.items('postgresql')
            for param in params:
                dbParams[param[0]] = param[1]
        else:
            self.iface.messageBar().pushMessage('Virhe', 'Tiedosto ei sisällä\
                tietokannan yhteystietoja', Qgis.Warning)

        return dbParams


    def setConnectionParamsFromInput(self, params):
        '''Sets connection parameters to input fields'''
        self.settingsDialog.dbHost.setValue(params['host'])
        self.settingsDialog.dbPort.setValue(params['port'])
        self.settingsDialog.dbName.setValue(params['database'])
        self.settingsDialog.dbUser.setValue(params['user'])
        self.settingsDialog.dbPass.setText(params['password'])


    def readConnectionParamsFromInput(self):
        '''Reads connection parameters from user input and returns a dictionary'''
        params = {}
        params['host'] = self.settingsDialog.dbHost.value()
        params['port'] = self.settingsDialog.dbPort.value()
        params['database'] = self.settingsDialog.dbName.value()
        params['user'] = self.settingsDialog.dbUser.value()
        params['password'] = self.settingsDialog.dbPass.text()
        return params


    def getUserFriendlyschemaTableName(self, schemaTableName):
        userFriendlyTableName = schemaTableName

        for table in self.yleiskaava_target_tables:
            if table["name"] == schemaTableName:
                userFriendlyTableName = table["userFriendlyTableName"]
                break

        return userFriendlyTableName


    def getTableNameForUserFriendlyschemaTableName(self, userFriendlyTableName):
        schemaTableName = userFriendlyTableName

        for table in self.yleiskaava_target_tables:
            if table["userFriendlyTableName"] == userFriendlyTableName:
                schemaTableName = table["name"]
                break

        return schemaTableName


    def getUserFriendlytargetFieldName(self, targetFieldName):
        userFriendlyFieldName = targetFieldName

        for field in self.yleiskaava_spatial_target_fields:
            if field["name"] == targetFieldName:
                userFriendlyFieldName = field["userFriendlyName"]
                break

        return userFriendlyFieldName


    def getFieldNameForUserFriendlytargetFieldName(self, userFriendlyFieldName):
        targetFieldName = userFriendlyFieldName

        for field in self.yleiskaava_spatial_target_fields:
            if field["userFriendlyName"] == userFriendlyFieldName:
                targetFieldName = field["name"]
                break

        return targetFieldName


    def getTypeOftargetField(self, targetFieldName):

        targetFieldType = None

        for field in self.yleiskaava_spatial_target_fields:
            if field["name"] == targetFieldName:
                targetFieldType = field["type"]
                break

        return targetFieldType

