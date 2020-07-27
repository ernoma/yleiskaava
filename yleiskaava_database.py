from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSettings, QVariant
from qgis.core import (Qgis, QgsProject, QgsFeature, QgsWkbTypes, QgsMessageLog)
from qgis.gui import QgsFileWidget

import os.path
import uuid

class YleiskaavaDatabase:

    def __init__(self, iface):

        self.iface = iface

        self.yleiskaavaUtils = None

        self.plugin_dir = os.path.dirname(__file__)

        self.yleiskaava_target_tables = [
            {"name": "yk_yleiskaava.yleiskaava", "userFriendlyTableName": 'Yleiskaavan ulkorajaus (yleiskaava)', "geomFieldName": "kaavan_ulkorajaus", "geometryType": QgsWkbTypes.PolygonGeometry, "showInCopySourceToTargetUI": False},
            {"name": "yk_yleiskaava.kaavaobjekti_alue", "userFriendlyTableName": 'Aluevaraukset', "featureType": "alue", "geomFieldName": "geom", "geometryType": QgsWkbTypes.PolygonGeometry, "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.kaavaobjekti_alue_taydentava", "userFriendlyTableName": 'Täydentävät aluekohteet (osa-alueet)', "featureType": "alue_taydentava", "geomFieldName": "geom", "geometryType": QgsWkbTypes.PolygonGeometry, "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.kaavaobjekti_viiva", "userFriendlyTableName": 'Viivamaiset kaavakohteet', "featureType": "viiva", "geomFieldName": "geom", "geometryType": QgsWkbTypes.LineGeometry, "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.kaavaobjekti_piste", "userFriendlyTableName": 'Pistemäiset kaavakohteet', "featureType": "piste", "geomFieldName": "geom", "geometryType": QgsWkbTypes.PointGeometry, "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.yleismaarays", "userFriendlyTableName": 'yleismääräykset', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_yleiskaava.kaavamaarays", "userFriendlyTableName": 'kaavamääräykset', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_kuvaustekniikka.teema", "userFriendlyTableName": 'teemat', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_prosessi.lahtoaineisto", "userFriendlyTableName": 'lahtoaineisto', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_prosessi.dokumentti", "userFriendlyTableName": 'kaavaan liittyvät dokumentit', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_koodiluettelot.kaavan_taso", "userFriendlyTableName": 'kaavan_taso', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_koodiluettelot.kansallinen_kaavatyyppi", "userFriendlyTableName": 'kansallinen_kaavatyyppi', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_koodiluettelot.laillinen_sitovuus", "userFriendlyTableName": 'laillinen_sitovuus', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_koodiluettelot.kaavoitusprosessin_tila", "userFriendlyTableName": 'kaavoitusprosessin_tila', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_koodiluettelot.prosessin_vaihe", "userFriendlyTableName": 'prosessin_vaihe', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_koodiluettelot.kansallinen_prosessin_vaihe", "userFriendlyTableName": 'kansallinen_prosessin_vaihe', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_koodiluettelot.kaavakohde_luokka", "userFriendlyTableName": 'kaavakohde_luokka  / HILUCS', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_koodiluettelot.kansallinen_kaavakohde_luokka", "userFriendlyTableName": 'kansallinen_kaavakohde_luokka', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_koodiluettelot.taydentava_kaavamerkinta_luokka", "userFriendlyTableName": 'taydentava_kaavamerkinta_luokka  / HSRCL', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_koodiluettelot.kansallinen_taydentava_kaavamerkinta_luokka", "userFriendlyTableName": 'kansallinen_taydentava_kaavamerkinta_luokka', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_inspire.kaavakohteen_olemassaolo", "userFriendlyTableName": 'kaavakohteen_olemassaolo', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_inspire.kansallisen_kaavakohteen_olemassaolo", "userFriendlyTableName": 'kansallisen_kaavakohteen_olemassaolo', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_inspire.kaavakohde", "userFriendlyTableName": 'kaavakohde', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_inspire.kansallinen_kaavakohde", "userFriendlyTableName": 'kansallinen_kaavakohde', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_inspire.taydentava_kaavamerkinta", "userFriendlyTableName": 'taydentava_kaavamerkinta', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_inspire.kansallinen_taydentava_kaavamerkinta", "userFriendlyTableName": 'kansallinen_taydentava_kaavamerkinta-yhteys', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys", "userFriendlyTableName": 'kaavaobjekti_kaavamaarays_yhteys', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_kuvaustekniikka.kaavaobjekti_teema_yhteys", "userFriendlyTableName": 'kaavaobjekti_teema_yhteys', "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_kuvaustekniikka.lahtoaineisto_yleiskaava_yhteys", "userFriendlyTableName": 'lahtoaineisto_yleiskaava_yhteys', "geomFieldName": None, "showInCopySourceToTargetUI": False}
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


    def getProjectLayer(self, name):
        layer = None

        for targetTableInfo in self.yleiskaava_target_tables:
            # QgsMessageLog.logMessage('getProjectLayer - name: ' + name + ', targetTableInfo["name"]: ' + str(targetTableInfo["name"]), 'Yleiskaava-työkalu', Qgis.Info)
            if targetTableInfo["name"] == name:
                # QgsMessageLog.logMessage('getProjectLayer - name: ' + name + ', targetTableInfo["userFriendlyTableName"]: ' + str(targetTableInfo["userFriendlyTableName"]), 'Yleiskaava-työkalu', Qgis.Info)
                layer = QgsProject.instance().mapLayersByName(targetTableInfo["userFriendlyTableName"])[0]
                break

        return layer


    def getUserFriendlyTargetSchemaTableNames(self):
        return [item["userFriendlyTableName"] for item in self.yleiskaava_target_tables]


    def getTargetSchemaTableNamesShownInCopySourceToTargetUI(self, geometry_type):
        names = []
        for item in self.yleiskaava_target_tables:
            if item['showInCopySourceToTargetUI'] == True and item["geometryType"] == geometry_type:
                names.append(item['userFriendlyTableName'])
        return names


    def getAllTargetSchemaTableNamesShownInCopySourceToTargetUI(self):
        names = []
        for item in self.yleiskaava_target_tables:
            if item['showInCopySourceToTargetUI'] == True:
                names.append(item['userFriendlyTableName'])
        return names

    
    def getTargetLayersWithGeometry(self):
        layers = []

        for item in self.yleiskaava_target_tables:
            if item["geometryType"] != None:
                layer = self.getLayerByTargetSchemaTableName(item["name"])
                layers.append(layer)

        return layers


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


    def getFeatureTypeForUserFriendlyTargetSchemaTableName(self, userFriendlyTableName):
        for item in self.yleiskaava_target_tables:
            if userFriendlyTableName ==  item['userFriendlyTableName']:
                return item['featureType']


    def getTargetSchemaTableByName(self, name):
        table_item = next((item for item in self.yleiskaava_target_tables if item["name"] == name), None)
        return table_item


    def getLayerByTargetSchemaTableName(self, name):
        targetLayer = self.getProjectLayer(name)
        #if targetLayer.isValid():
        return targetLayer
        #else:
        #    return None


    def getSpatialPlans(self):
        layer = self.getLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
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

        layer = self.getLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
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

        layer = self.getLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
        features = layer.getFeatures()

        plans = []
        for index, feature in enumerate(features):
            if feature['id'] == planID:
                if feature['nro'] is not None:
                    planNumber = feature['nro']
                break

        return planNumber
        

    def getPlanNameForPlanID(self, planID):
        planName = None

        layer = self.getLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
        features = layer.getFeatures()

        plans = []
        for index, feature in enumerate(features):
            if feature['id'] == planID:
                if feature['nimi'] is not None:
                    planName = feature['nimi']
                break

        return planName


    def getYleiskaavaPlanLevelCodeWithPlanName(self, planName):
        planLevelCode = None

        layer = self.getLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
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

        targetLayer = self.getProjectLayer("yk_koodiluettelot.kaavan_taso")

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

        layer = self.getLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
        features = layer.getFeatures()

        plans = []
        for index, feature in enumerate(features):
            if feature['nimi'] == planName:
                planID = feature['id']
                break

        return planID


    def getSpatialFeaturesWithRegulationForType(self, regulationID, featureType):
        targetLayer = self.getProjectLayer("yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys")

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
        layer = self.getProjectLayer("yk_yleiskaava.kaavaobjekti_" + featureType)
        feature = self.findSpatialFeatureFromFeatureLayerWithID(layer, featureID)
        return feature


    def findSpatialFeatureFromFeatureLayerWithID(self, layer, featureID):
        for feature in layer.getFeatures():
            if feature['id'] == featureID:
                return feature

        return None


    def getRegulationCountForSpatialFeature(self, featureID, featureType):
        targetLayer = self.getProjectLayer("yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys")

        count = 0

        for feature in targetLayer.getFeatures():
            if feature["id_kaavaobjekti_" + featureType] == featureID:
                count += 1

        return count


    def getDistinctLandUseClassificationsOfLayer(self, userFriendlyTableName):
        featureType = self.getFeatureTypeForUserFriendlyTargetSchemaTableName(userFriendlyTableName)
        layer = self.getProjectLayer("yk_yleiskaava.kaavaobjekti_" + featureType)

        classifications = []

        for feature in layer.getFeatures():
            if feature['kayttotarkoitus_lyhenne'] not in classifications:
                classifications.append(feature['kayttotarkoitus_lyhenne'])

        return classifications


    def getLayerFeatureIDsAndFieldValuesForFeaturesHavingLanduseClassification(self, userFriendlyTableName, landUseClassification, fieldName):
        featureIDsAndValues = []

        featureType = self.getFeatureTypeForUserFriendlyTargetSchemaTableName(userFriendlyTableName)
        layer = self.getProjectLayer("yk_yleiskaava.kaavaobjekti_" + featureType)
        for feature in layer.getFeatures():
            if feature['kayttotarkoitus_lyhenne'] == landUseClassification:
                if not QVariant(feature[fieldName]).isNull() and str(feature[fieldName]) != '':
                    featureIDsAndValues.append({
                        "id": feature["id"],
                        "value": str(feature[fieldName])
                    })

        return featureIDsAndValues


    def getRegulationsForSpatialFeature(self, featureID, featureType):
        regulationList = []

        regulations = self.getSpecificRegulations()

        targetLayer = self.getProjectLayer("yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys")
        #targetLayer = QgsProject.instance().mapLayersByName("kaavaobjekti_kaavamaarays_yhteys")[0]


        for feature in targetLayer.getFeatures():
            if feature["id_kaavaobjekti_" + featureType] == featureID:
                # QgsMessageLog.logMessage("getRegulationsForSpatialFeature - kaavakohde löytyi yhteyksistä, id_kaavaobjekti_*: " + str(feature["id_kaavaobjekti_" + featureType]), 'Yleiskaava-työkalu', Qgis.Info)
                for regulation in regulations:
                    if regulation["id"] == feature["id_kaavamaarays"]:
                        # QgsMessageLog.logMessage("getRegulationsForSpatialFeature - kaavamääräys lisätään palautettavaan listaan, jos kaavamaarays_otsikko ei null, feature['kaavamaarays_otsikko']: " + str(regulation['kaavamaarays_otsikko'].value()), 'Yleiskaava-työkalu', Qgis.Info)
                        if not regulation["kaavamaarays_otsikko"].isNull():
                            # QgsMessageLog.logMessage("getRegulationsForSpatialFeature - kaavamääräys lisätään palautettavaan listaan, regulation['kaavamaarays_otsikko']: " + str(regulation['kaavamaarays_otsikko'].value()), 'Yleiskaava-työkalu', Qgis.Info)
                            regulationList.append(regulation)
                        break

        return regulationList


    def getSpecificRegulations(self):
        targetLayer = self.getProjectLayer("yk_yleiskaava.kaavamaarays")

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
        layer = self.getProjectLayer("yk_yleiskaava.kaavamaarays")

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


    def removeSpatialFeatureRegulationAndLandUseClassification(self, featureID, featureType, shouldUpdateOnlyRelation):
        self.removeRegulationRelationsFromSpatialFeature(featureID, featureType)

        layer = self.getProjectLayer("yk_yleiskaava.kaavaobjekti_" + featureType)
        feature = self.findSpatialFeatureFromFeatureLayerWithID(layer, featureID)

        if not shouldUpdateOnlyRelation:
            layer.startEditing()

            index = layer.fields().indexFromName("kaavamaaraysotsikko")
            success = layer.changeAttributeValue(feature.id(), index, None)
            if not success:
                    self.iface.messageBar().pushMessage('removeSpatialFeatureRegulationAndLandUseClassification - kaavamaaraysotsikko - changeAttributeValue() failed', Qgis.Critical)
                    return False
            index = layer.fields().indexFromName("kayttotarkoitus_lyhenne")
            # landUseClassificationName = None
            # if feature["id_yleiskaava"] is not None:
            #     planNumber = self.getPlanNumberForPlanID(feature["id_yleiskaava"])
                # landUseClassificationName = self.yleiskaavaUtils.getLandUseClassificationNameForRegulation(planNumber, "yk_yleiskaava.kaavaobjekti_" + featureType, regulationTitle)
            success = layer.changeAttributeValue(feature.id(), index, None)
            if not success:
                self.iface.messageBar().pushMessage('removeSpatialFeatureRegulationAndLandUseClassification - kayttotarkoitus_lyhenne - changeAttributeValue() failed', Qgis.Critical)

            success = layer.commitChanges()
            if not success:
                self.iface.messageBar().pushMessage('removeSpatialFeatureRegulationAndLandUseClassification - commitChanges() failed, reason(s): "', Qgis.Critical)
                # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - commitChanges() failed, reason(s): ", 'Yleiskaava-työkalu', Qgis.Critical)
                for error in layer.commitErrors():
                    self.iface.messageBar().pushMessage(error + ".", Qgis.Critical)
                    # QgsMessageLog.logMessage(error + ".", 'Yleiskaava-työkalu', Qgis.Critical)
                return False

        return True


    def removeSpatialFeatureThemes(self, featureID, featureType):
        self.removeThemeRelationsFromSpatialFeature(featureID, featureType)

        return True
        

    def updateSpatialFeatureRegulationAndLandUseClassification(self, featureID, featureType, regulationID, regulationTitle, shouldRemoveOldRegulationRelations, shouldUpdateOnlyRelation):
        # remove old regulation relations if shouldRemoveOldRegulationRelations
        # lisää yhteys kaavaobjekti_kaavamaarays_yhteys-tauluun, jos yhteyttä ei vielä ole

        if shouldRemoveOldRegulationRelations:
            self.removeRegulationRelationsFromSpatialFeature(featureID, featureType)

        if not self.existsFeatureRegulationRelation(featureID, featureType, regulationID):
            self.createFeatureRegulationRelationWithRegulationID("yk_yleiskaava.kaavaobjekti_" + featureType, featureID, regulationID)

        layer = self.getProjectLayer("yk_yleiskaava.kaavaobjekti_" + featureType)
        feature = self.findSpatialFeatureFromFeatureLayerWithID(layer, featureID)

        if not shouldUpdateOnlyRelation:
            layer.startEditing()

            index = layer.fields().indexFromName("kaavamaaraysotsikko")
            success = layer.changeAttributeValue(feature.id(), index, regulationTitle)
            if not success:
                    self.iface.messageBar().pushMessage('updateSpatialFeatureRegulationAndLandUseClassificationTexts - kaavamaaraysotsikko - changeAttributeValue() failed', Qgis.Critical)
                    return False
            index = layer.fields().indexFromName("kayttotarkoitus_lyhenne")
            landUseClassificationName = regulationTitle
            if feature["id_yleiskaava"] is not None:
                planNumber = self.getPlanNumberForPlanID(feature["id_yleiskaava"])
                landUseClassificationName = self.yleiskaavaUtils.getLandUseClassificationNameForRegulation(planNumber, "yk_yleiskaava.kaavaobjekti_" + featureType, regulationTitle)
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
        relationLayer = self.getProjectLayer("yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys")

        for feature in relationLayer.getFeatures():
            if (feature["id_kaavamaarays"] == regulationID and feature["id_kaavaobjekti_" + featureType] == featureID):
                return True

        return False


    def removeRegulationRelationsFromSpatialFeature(self, featureID, featureType):
        relationLayer = self.getProjectLayer("yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys")

        relationLayer.startEditing()

        for feature in relationLayer.getFeatures():
            if (feature["id_kaavaobjekti_" + featureType] == featureID):
                relationLayer.deleteFeature(feature.id())

        relationLayer.commitChanges()


    def deleteSpatialFeature(self, featureID, featureType):
        layer = self.getLayerByTargetSchemaTableName("yk_yleiskaava.kaavaobjekti_" + featureType)
        layer.startEditing()
        for feature in layer.getFeatures():
            if (feature["id"] == featureID):
                layer.deleteFeature(feature.id())
                break
        layer.commitChanges()


    def createFeatureRegulationRelation(self, targetSchemaTableName, targetFeatureID, regulationTitle):
        regulationID = self.findRegulationID(regulationTitle)

        self.createFeatureRegulationRelationWithRegulationID(targetSchemaTableName, targetFeatureID, regulationID)


    def createFeatureRegulationRelationWithRegulationID(self, targetSchemaTableName, targetFeatureID, regulationID):
        # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - targetSchemaTableName: " + targetSchemaTableName + ", targetFeatureID: " + str(targetFeatureID) + ", regulationID: " + str(regulationID), 'Yleiskaava-työkalu', Qgis.Info)

        relationLayer = self.getProjectLayer("yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys")
        #relationLayer = QgsProject.instance().mapLayersByName("kaavaobjekti_kaavamaarays_yhteys")[0]

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
                # pass
                QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - relationLayer.commitChanges() success", 'Yleiskaava-työkalu', Qgis.Info)


    def addRegulationRelationsToLayer(self, sourceFeatureID, targetFeatureID, featureType):
        # NOTE ilmeisesti toimii vain, jos targetFeatureID löytyy jo tallennettuna tietokannasta ko. kaavaobjekti-taulusta
        regulations = self.getRegulationsForSpatialFeature(sourceFeatureID, featureType)
        targetSchemaTableName = "yk_yleiskaava.kaavaobjekti_" + featureType
        for regulation in regulations:
            QgsMessageLog.logMessage("addRegulationRelationsToLayer - regulation relation lisätään kaavakohteelle, fid: " + str(targetFeatureID), 'Yleiskaava-työkalu', Qgis.Info)
            self.createFeatureRegulationRelationWithRegulationID(targetSchemaTableName, targetFeatureID, regulation["id"])


    def getThemes(self):
        targetLayer = self.getProjectLayer("yk_kuvaustekniikka.teema")

        features = targetLayer.getFeatures()
        themeList = []
        for index, feature in enumerate(features):
            nimi = QVariant(feature["nimi"])
            kuvaus = QVariant(feature['kuvaus'])
            id_yleiskaava = QVariant(feature['id_yleiskaava'])

            if not nimi.isNull():
                themeList.append({
                    "id": feature['id'],
                    "alpha_sort_key": str(nimi.value()),
                    "nimi": nimi,
                    "kuvaus": kuvaus,
                    "id_yleiskaava": id_yleiskaava,
                    "yleiskaava_nimi": QVariant(self.getPlanNameForPlanID(id_yleiskaava))
                    })

        return themeList


    def getThemesForSpatialFeature(self, featureID, featureType):
        themeList = []

        themes = self.getThemes()

        themeRelationLayer = self.getProjectLayer("yk_kuvaustekniikka.kaavaobjekti_teema_yhteys")
        #targetLayer = QgsProject.instance().mapLayersByName("kaavaobjekti_kaavamaarays_yhteys")[0]

        for feature in themeRelationLayer.getFeatures():
            if feature["id_kaavaobjekti_" + featureType] == featureID:
                # QgsMessageLog.logMessage("getRegulationsForSpatialFeature - kaavakohde löytyi yhteyksistä, id_kaavaobjekti_*: " + str(feature["id_kaavaobjekti_" + featureType]), 'Yleiskaava-työkalu', Qgis.Info)
                for theme in themes:
                    if theme["id"] == feature["id_teema"]:
                        # QgsMessageLog.logMessage("getRegulationsForSpatialFeature - kaavamääräys lisätään palautettavaan listaan, jos kaavamaarays_otsikko ei null, feature['kaavamaarays_otsikko']: " + str(regulation['kaavamaarays_otsikko'].value()), 'Yleiskaava-työkalu', Qgis.Info)
                        if not theme["nimi"].isNull():
                            # QgsMessageLog.logMessage("getRegulationsForSpatialFeature - kaavamääräys lisätään palautettavaan listaan, regulation['kaavamaarays_otsikko']: " + str(regulation['kaavamaarays_otsikko'].value()), 'Yleiskaava-työkalu', Qgis.Info)
                            themeList.append(theme)
                        break

        return themeList


    def createFeatureThemeRelationWithThemeID(self, targetSchemaTableName, targetFeatureID, themeID):
        # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - targetSchemaTableName: " + targetSchemaTableName + ", targetFeatureID: " + str(targetFeatureID) + ", regulationID: " + str(regulationID), 'Yleiskaava-työkalu', Qgis.Info)

        relationLayer = self.getProjectLayer("yk_kuvaustekniikka.kaavaobjekti_teema_yhteys")
        #relationLayer = QgsProject.instance().mapLayersByName("kaavaobjekti_kaavamaarays_yhteys")[0]

        schema, table_name = targetSchemaTableName.split('.')

        relationLayer.startEditing()

        relationLayerFeature = QgsFeature()
        relationLayerFeature.setFields(relationLayer.fields())
        relationLayerFeature.setAttribute("id", str(uuid.uuid4()))
        relationLayerFeature.setAttribute("id_" + table_name, targetFeatureID)
        relationLayerFeature.setAttribute("id_teema", themeID)

        provider = relationLayer.dataProvider()
        
        success = provider.addFeatures([relationLayerFeature])
        if not success:
            self.iface.messageBar().pushMessage('Bugi koodissa: createFeatureThemeRelationWithThemeID - addFeatures() failed"', Qgis.Critical)
            # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - addFeatures() failed", 'Yleiskaava-työkalu', Qgis.Critical)
        else:
            success = relationLayer.commitChanges()
            if not success:
                self.iface.messageBar().pushMessage('Bugi koodissa: createFeatureThemeRelationWithThemeID - commitChanges() failed, reason(s): "', Qgis.Critical)
                # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - commitChanges() failed, reason(s): ", 'Yleiskaava-työkalu', Qgis.Critical)
                for error in relationLayer.commitErrors():
                    self.iface.messageBar().pushMessage(error + ".", Qgis.Critical)
                    # QgsMessageLog.logMessage(error + ".", 'Yleiskaava-työkalu', Qgis.Critical)
            else:
                # pass
                QgsMessageLog.logMessage("createFeatureThemeRelationWithThemeID - relationLayer.commitChanges() success", 'Yleiskaava-työkalu', Qgis.Info)


    def addThemeRelationsToLayer(self, sourceFeatureID, targetFeatureID, featureType):
        themes = self.getThemesForSpatialFeature(sourceFeatureID, featureType)
        targetSchemaTableName = "yk_yleiskaava.kaavaobjekti_" + featureType
        for theme in themes:
            # QgsMessageLog.logMessage("addThemeRelationsToLayer - teema relation lisätään kaavakohteelle, fid: " + str(targetFeatureID), 'Yleiskaava-työkalu', Qgis.Info)
            self.createFeatureThemeRelationWithThemeID(targetSchemaTableName, targetFeatureID, theme["id"])


    def findRegulationID(self, regulationName):
        regulationList = self.getSpecificRegulations()

        regulationID = None
        for regulation in regulationList:
            if regulation["kaavamaarays_otsikko"].value() == regulationName:
                regulationID = regulation["id"]
                break

        return regulationID


    def createSpecificRegulationAndFeatureRegulationRelation(self, targetSchemaTableName, targetFeatureID, regulationName):
        regulationLayer = self.getProjectLayer("yk_yleiskaava.kaavamaarays")

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
        name = "yk_koodiluettelot." + targetFieldName[3:]
        # QgsMessageLog.logMessage('getCodeListValuesForPlanObjectField - targetFieldName: ' + targetFieldName + ', name: ' + str(name), 'Yleiskaava-työkalu', Qgis.Info)
        
        targetLayer = self.getProjectLayer(name)
        features = targetLayer.getFeatures()
        values = None
        # if table_name == "kansallinen_prosessin_vaihe" or table_name == "prosessin_vaihe" or table_name == "kaavoitusprosessin_tila" or table_name == "laillinen_sitovuus":
        values = [feature['koodi'] for feature in features]

        return values

    def getCodeListValueForPlanObjectFieldUUID(self, targetFieldName, value):
        codeValue = None
        name = "yk_koodiluettelot." + targetFieldName[3:]
        targetLayer = self.getProjectLayer(name)
        features = targetLayer.getFeatures()

        for feature in features:
            if feature['id'] == value:
                codeValue =  feature['koodi']
                break
        return codeValue


    def getCodeListUUIDForPlanObjectFieldCodeValue(self, targetFieldName, value):
        uuid = None
        name = "yk_koodiluettelot." + targetFieldName[3:]
        targetLayer = self.getProjectLayer(name)
        features = targetLayer.getFeatures()
        
        # if table_name == "kansallinen_prosessin_vaihe" or table_name == "prosessin_vaihe" or table_name == "kaavoitusprosessin_tila" or table_name == "laillinen_sitovuus":
        for feature in features:
            if feature['koodi'] == value:
                uuid =  feature['id']
                break
        return uuid


    def getSchemaTableFields(self, name):
        layer = self.getProjectLayer(name)
        return layer.fields().toList()


    def getFieldNamesAndTypes(self, featureType):
        fieldNamesAndTypes = []

        layer = self.getLayerByTargetSchemaTableName("yk_yleiskaava.kaavaobjekti_" + featureType)

        for index, field in enumerate(layer.fields().toList()):
            fieldName = field.name()
            fieldTypeName = self.yleiskaavaUtils.getStringTypeForFeatureField(field)
            fieldNamesAndTypes.append({
                "name": fieldName,
                "typeName": fieldTypeName
            })

        return fieldNamesAndTypes


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


    def getUserFriendlySpatialFeatureTypeName(self, featureType):
        userFriendlyFeatureTypeName = None

        if featureType == 'alue':
            return 'aluevaraus'
        elif featureType == 'alue_taydentava':
            return 'täydentävä aluekohde'
        elif featureType == 'viiva':
            return 'viivamainen kohde'
        elif featureType == 'piste':
            return 'pistemäinen kohde'


    def getSelectedFeatures(self, featureType):
        layer = self.getTargetLayer(featureType)

        # QgsMessageLog.logMessage("getSelectedFeatures - layer.selectedFeatureCount(): " + str(layer.selectedFeatureCount()), 'Yleiskaava-työkalu', Qgis.Info)

        return layer.getSelectedFeatures()


    def getTargetLayer(self, featureType):
        layer = None

        if featureType == "alue":
            layer = QgsProject.instance().mapLayersByName("Aluevaraukset")[0]
        elif featureType == "alue_taydentava":
            layer = QgsProject.instance().mapLayersByName("Täydentävät aluekohteet (osa-alueet)")[0]
        elif featureType == "viiva":
            layer = QgsProject.instance().mapLayersByName("Viivamaiset kaavakohteet")[0]
        elif featureType == "piste":
            layer = QgsProject.instance().mapLayersByName("Pistemäiset kaavakohteet")[0]

        return layer

    
    def updateSpatialFeaturesWithFieldValues(self, layer, featureIDsAndValues, fieldName):
        features = layer.getFeatures()
        index = layer.fields().indexFromName(fieldName)
        layer.startEditing()

        for feature in features:
            for featureIDsAndValue in featureIDsAndValues:
                if feature["id"] == featureIDsAndValue["id"]:
                    # QgsMessageLog.logMessage("updateSpatialFeaturesWithFieldValues - changing attribute value for feature id: " + featureIDsAndValue["id"] + ", value: " + featureIDsAndValue["value"], 'Yleiskaava-työkalu', Qgis.Info)
                    layer.changeAttributeValue(feature.id(), index, featureIDsAndValue["value"])

        success = layer.commitChanges()

        if not success:
            self.iface.messageBar().pushMessage('Bugi koodissa: updateSpatialFeaturesWithFieldValues - commitChanges() failed, reason(s): "', Qgis.Critical)
            # QgsMessageLog.logMessage("copySourceFeaturesToTargetLayer - commitChanges() failed, reason(s): ", 'Yleiskaava-työkalu', Qgis.Critical)
            for error in self.targetLayer.commitErrors():
                self.iface.messageBar().pushMessage(error + ".", Qgis.Critical)
                # QgsMessageLog.logMessage(error + ".", 'Yleiskaava-työkalu', Qgis.Critical)

            return False
        else:
            pass

        return True


    def updateSelectedSpatialFeaturesWithFieldValues(self, featureType, updatedFieldData):
        layer = self.getTargetLayer(featureType)
        features = layer.getSelectedFeatures()

        layer.startEditing()

        for feature in features:
            for updatedFieldDataItem in updatedFieldData:
                index = layer.fields().indexFromName(updatedFieldDataItem["fieldName"])
                layer.changeAttributeValue(feature.id(), index, updatedFieldDataItem["value"])

        success = layer.commitChanges()

        if not success:
            self.iface.messageBar().pushMessage('Bugi koodissa: updateSelectedSpatialFeaturesWithFieldValues - commitChanges() failed, reason(s): "', Qgis.Critical)
            # QgsMessageLog.logMessage("copySourceFeaturesToTargetLayer - commitChanges() failed, reason(s): ", 'Yleiskaava-työkalu', Qgis.Critical)
            for error in self.targetLayer.commitErrors():
                self.iface.messageBar().pushMessage(error + ".", Qgis.Critical)
                # QgsMessageLog.logMessage(error + ".", 'Yleiskaava-työkalu', Qgis.Critical)

            return False
        else:
            pass

        return True


    def updateTheme(self, themeID, themeName, themeDescription):
        layer = QgsProject.instance().mapLayersByName("teema")[0]

        layer.startEditing()

        for feature in layer.getFeatures():
            if feature["id"] == themeID:
                index = layer.fields().indexFromName("nimi")
                success = layer.changeAttributeValue(feature.id(), index, themeName)
                if not success:
                    self.iface.messageBar().pushMessage('updateTheme - nimi - changeAttributeValue() failed', Qgis.Critical)
                    return False
                index = layer.fields().indexFromName("kuvaus")
                success = layer.changeAttributeValue(feature.id(), index, themeDescription)
                if not success:
                    self.iface.messageBar().pushMessage('updateTheme - kuvaus - changeAttributeValue() failed', Qgis.Critical)
                    return False
    
                success = layer.commitChanges()
                if not success:
                    self.iface.messageBar().pushMessage('updateTheme - commitChanges() failed, reason(s): "', Qgis.Critical)
                    # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - commitChanges() failed, reason(s): ", 'Yleiskaava-työkalu', Qgis.Critical)
                    for error in layer.commitErrors():
                        self.iface.messageBar().pushMessage(error + ".", Qgis.Critical)
                        # QgsMessageLog.logMessage(error + ".", 'Yleiskaava-työkalu', Qgis.Critical)
                    return False
                break

        return True

    
    def getThemeCountForSpatialFeature(self, featureID, featureType):
        relationLayer = QgsProject.instance().mapLayersByName("kaavaobjekti_teema_yhteys")[0]

        count = 0

        for feature in relationLayer.getFeatures():
            if feature["id_kaavaobjekti_" + featureType] == featureID:
                count += 1

        return count


    def updateSpatialFeatureTheme(self, featureID, featureType, themeID, themeName, shouldRemoveOldThemeRelations):
        # poista vanhat teemat jos shouldRemoveOldThemeRelations
        # lisää yhteys kaavaobjekti_teema_yhteys-tauluun, jos yhteyttä ei vielä ole

        if shouldRemoveOldThemeRelations:
            self.removeThemeRelationsFromSpatialFeature(featureID, featureType)

        if not self.existsFeatureThemeRelation(featureID, featureType, themeID):
            self.createFeatureThemeRelationWithThemeID("yk_yleiskaava.kaavaobjekti_" + featureType, featureID, themeID)

        return True


    def createFeatureThemeRelationWithThemeID(self, targetSchemaTableName, targetFeatureID, themeID):
        # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - targetSchemaTableName: " + targetSchemaTableName + ", targetFeatureID: " + str(targetFeatureID) + ", regulationID: " + str(regulationID), 'Yleiskaava-työkalu', Qgis.Info)

        relationLayer = QgsProject.instance().mapLayersByName("kaavaobjekti_teema_yhteys")[0]

        schema, table_name = targetSchemaTableName.split('.')


        relationLayer.startEditing()

        relationLayerFeature = QgsFeature()
        relationLayerFeature.setFields(relationLayer.fields())
        relationLayerFeature.setAttribute("id", str(uuid.uuid4()))
        relationLayerFeature.setAttribute("id_" + table_name, targetFeatureID)
        relationLayerFeature.setAttribute("id_teema", themeID)

        provider = relationLayer.dataProvider()
        
        success = provider.addFeatures([relationLayerFeature])
        if not success:
            self.iface.messageBar().pushMessage('Bugi koodissa: createFeatureThemeRelationWithThemeID - addFeatures() failed"', Qgis.Critical)
            # QgsMessageLog.logMessage("createFeatureThemeRelationWithThemeID - addFeatures() failed", 'Yleiskaava-työkalu', Qgis.Critical)
        else:
            success = relationLayer.commitChanges()
            if not success:
                self.iface.messageBar().pushMessage('Bugi koodissa: createFeatureThemeRelationWithThemeID - commitChanges() failed, reason(s): "', Qgis.Critical)
                # QgsMessageLog.logMessage("createFeatureThemeRelationWithThemeID - commitChanges() failed, reason(s): ", 'Yleiskaava-työkalu', Qgis.Critical)
                for error in relationLayer.commitErrors():
                    self.iface.messageBar().pushMessage(error + ".", Qgis.Critical)
                    # QgsMessageLog.logMessage(error + ".", 'Yleiskaava-työkalu', Qgis.Critical)
            else:
                # pass
                QgsMessageLog.logMessage("createFeatureThemeRelationWithThemeID - relationLayer.commitChanges() success", 'Yleiskaava-työkalu', Qgis.Info)


    def existsFeatureThemeRelation(self, featureID, featureType, themeID):
        relationLayer = QgsProject.instance().mapLayersByName("kaavaobjekti_teema_yhteys")[0]

        for feature in relationLayer.getFeatures():
            if (feature["id_teema"] == themeID and feature["id_kaavaobjekti_" + featureType] == featureID):
                return True

        return False


    def removeThemeRelationsFromSpatialFeature(self, featureID, featureType):
        relationLayer = QgsProject.instance().mapLayersByName("kaavaobjekti_teema_yhteys")[0]

        relationLayer.startEditing()

        for feature in relationLayer.getFeatures():
            if (feature["id_kaavaobjekti_" + featureType] == featureID):
                relationLayer.deleteFeature(feature.id())

        relationLayer.commitChanges()


    def getSourceDataFeatures(self, linkType):
        layer = QgsProject.instance().mapLayersByName("lahtoaineisto")[0] # <- jos filteröity UI:ssa, niin ei toimi
        
        features = []

        for feature in layer.getFeatures():
            if feature["linkitys_tyyppi"] == linkType:
                features.append(feature)

        return features


    def getLinkedFeatureIDAndSourceDataFeature(self, spatialFeatureLayer, sourceLayerFeatureInfo, linkType):
        linkedFeatureID = None
        linkedSourceDataFeature = self.getLinkedSourceDataFeature(linkType, sourceLayerFeatureInfo)

        if linkedSourceDataFeature is not None:
            featureIDs = self.getLinkedFeatureIDsForSourceDataFeature(spatialFeatureLayer, linkedSourceDataFeature)
            if len(featureIDs) > 1:
                self.iface.messageBar().pushMessage('Löydettiin useita lähdeaineistokohteeseen "' + sourceLayerFeatureInfo["nimi"] + '" linkitettyjä kaavakohteita', Qgis.Warning)
            if len(featureIDs) >= 1:
                linkedFeatureID = featureIDs[0]

        return linkedFeatureID, linkedSourceDataFeature


    def getLinkedSourceDataFeature(self, linkType, sourceLayerFeatureInfo):
        linkedSourceDataFeature = None
        sourceDataFeatures = self.getSourceDataFeatures(linkType)
        for feature in sourceDataFeatures:
            if linkType == "tre_siiri":
                if sourceLayerFeatureInfo["linkki_data"] == feature["linkki_data"]:
                     linkedSourceDataFeature = feature
                     break

        return linkedSourceDataFeature


    def getLinkedFeatureIDsForSourceDataFeature(self, spatialFeatureLayer, linkedSourceDataFeature):
        linkedFeatureIDs = []

        relationLayer = QgsProject.instance().mapLayersByName("lahtoaineisto_yleiskaava_yhteys")[0] # <- jos filteröity UI:ssa, niin ei toimi

        targetSchemaTableName = self.getTargetSchemaTableNameForUserFriendlyTableName(spatialFeatureLayer.name())
        schema, table_name = targetSchemaTableName.split('.')

        for relationFeature in relationLayer.getFeatures():
            if relationFeature["id_lahtoaineisto"] == linkedSourceDataFeature["id"] and relationFeature["id_" + table_name] is not None:
                linkedFeatureIDs.append(relationFeature["id_" + table_name])

        return linkedFeatureIDs


    def createSourceDataFeature(self, sourceData):
        sourceDataLayer = QgsProject.instance().mapLayersByName("lahtoaineisto")[0] # <- jos filteröity UI:ssa, niin ei toimi

        sourceDataFeatureID = str(uuid.uuid4())

        sourceDataFeature = QgsFeature()
        sourceDataFeature.setFields(sourceDataLayer.fields())
        sourceDataFeature.setAttribute("id", sourceDataFeatureID)
        for key in sourceData.keys():
            sourceDataFeature.setAttribute(key, sourceData[key])
        sourceDataLayer.startEditing()
        provider = sourceDataLayer.dataProvider()
        success = provider.addFeatures([sourceDataFeature])
        if not success:
            self.iface.messageBar().pushMessage('Bugi koodissa: createSourceDataFeature - addFeatures() failed"', Qgis.Critical)
        else:
            success = sourceDataLayer.commitChanges()
            if not success:
                self.iface.messageBar().pushMessage('Bugi koodissa: createSourceDataFeature - commitChanges() failed, reason(s): "', Qgis.Critical)
                # QgsMessageLog.logMessage("createFeatureThemeRelationWithThemeID - commitChanges() failed, reason(s): ", 'Yleiskaava-työkalu', Qgis.Critical)
                for error in sourceDataLayer.commitErrors():
                    self.iface.messageBar().pushMessage(error + ".", Qgis.Critical)
                    # QgsMessageLog.logMessage(error + ".", 'Yleiskaava-työkalu', Qgis.Critical)
            else:
                pass
                # QgsMessageLog.logMessage("createFeatureThemeRelationWithThemeID - relationLayer.commitChanges() success", 'Yleiskaava-työkalu', Qgis.Info)
        if success:
            return sourceDataFeatureID
        else:
            return None


    def createSourceDataFeatureAndRelationToSpatialFeature(self, sourceData, spatialFeatureLayer, targetFeatureID):
        # lisää tarvittaessa uusi lähdeaineistorivi tietokantaan,
        # lisää relaatio kaavakohteen ja lähdeaineistorivin välille

        linkedSourceDataFeatureID = None

        linkedSourceDataFeature = self.getLinkedSourceDataFeature(sourceData["linkitys_tyyppi"], sourceData)
        if linkedSourceDataFeature is not None:
            linkedSourceDataFeatureID = linkedSourceDataFeature["id"]
        else:
            linkedSourceDataFeatureID = self.createSourceDataFeature(sourceData)

        success = False

        if linkedSourceDataFeatureID is not None:
            relationFeatureID = self.createSourceDataRelationToSpatialFeature(linkedSourceDataFeatureID, spatialFeatureLayer, targetFeatureID)
            if relationFeatureID is not None:
                success = True
        
        return success


    def createSourceDataRelationToSpatialFeature(self, linkedSourceDataFeatureID, spatialFeatureLayer, targetFeatureID):
        relationLayer = QgsProject.instance().mapLayersByName("lahtoaineisto_yleiskaava_yhteys")[0] # <- jos filteröity UI:ssa, niin ei toimi

        targetSchemaTableName = self.getTargetSchemaTableNameForUserFriendlyTableName(spatialFeatureLayer.name())
        schema, table_name = targetSchemaTableName.split('.')

        relationFeatureID = str(uuid.uuid4())

        relationFeature = QgsFeature()
        relationFeature.setFields(relationLayer.fields())
        relationFeature.setAttribute("id", relationFeatureID)
        relationFeature.setAttribute("id_lahtoaineisto", linkedSourceDataFeatureID)
        relationFeature.setAttribute("id_" + table_name, targetFeatureID)
        relationLayer.startEditing()
        provider = relationLayer.dataProvider()
        success = provider.addFeatures([relationFeature])
        if not success:
            self.iface.messageBar().pushMessage('Bugi koodissa: createSourceDataFeature - addFeatures() failed"', Qgis.Critical)
        else:
            success = relationLayer.commitChanges()
            if not success:
                self.iface.messageBar().pushMessage('Bugi koodissa: createSourceDataFeature - commitChanges() failed, reason(s): "', Qgis.Critical)
                # QgsMessageLog.logMessage("createFeatureThemeRelationWithThemeID - commitChanges() failed, reason(s): ", 'Yleiskaava-työkalu', Qgis.Critical)
                for error in relationLayer.commitErrors():
                    self.iface.messageBar().pushMessage(error + ".", Qgis.Critical)
                    # QgsMessageLog.logMessage(error + ".", 'Yleiskaava-työkalu', Qgis.Critical)
            else:
                pass
                # QgsMessageLog.logMessage("createFeatureThemeRelationWithThemeID - relationLayer.commitChanges() success", 'Yleiskaava-työkalu', Qgis.Info)

        if success:
            return relationFeatureID
        else:
            return None
