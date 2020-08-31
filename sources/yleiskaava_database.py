from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSettings, QVariant, QDateTime
from qgis.core import (Qgis, QgsProject,
    QgsFeature, QgsWkbTypes,
    QgsMessageLog, QgsFeatureRequest)
from qgis.gui import QgsFileWidget

import os.path
import uuid

import psycopg2
import psycopg2.extras

import socket


class YleiskaavaDatabase:

    KAAVAOBJEKTI_ALUE = "Aluevaraukset"
    KAAVAOBJEKTI_ALUE_TAYDENTAVA = "Täydentävät aluekohteet (osa-alueet)"
    KAAVAOBJEKTI_VIIVA = "Viivamaiset kaavakohteet"
    KAAVAOBJEKTI_PISTE = "Pistemäiset kaavakohteet"

    QGS_SETTINGS_PSYCOPG2_PARAM_MAP = {
        'database': 'dbname',
        'host': 'host',
        'password': 'password',
        'port': 'port',
        'username': 'user'
    }


    def __init__(self, iface, plugin_dir):

        self.iface = iface

        self.yleiskaavaUtils = None

        self.plugin_dir = plugin_dir

        self.dbConnection = None
        self.databaseConnectionParams = None

        self.codeTableCodes = {} # {'id': , row['id'], 'koodi': row['koodi'] }

        self.plans = None
        self.planLevelList = None
        self.themes = None

        self.layerPlans = None
        self.layerPlanLevelList = None
        self.layerThemes = None

        self.yleiskaava_target_tables = [
            {"name": "yk_yleiskaava.yleiskaava", "userFriendlyTableName": 'Yleiskaavan ulkorajaus (yleiskaava)', "geomFieldName": "kaavan_ulkorajaus", "geometryType": QgsWkbTypes.PolygonGeometry, "showInCopySourceToTargetUI": False},
            {"name": "yk_yleiskaava.kaavaobjekti_alue", "userFriendlyTableName": YleiskaavaDatabase.KAAVAOBJEKTI_ALUE, "featureType": "alue", "geomFieldName": "geom", "geometryType": QgsWkbTypes.PolygonGeometry, "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.kaavaobjekti_alue_taydentava", "userFriendlyTableName": YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA, "featureType": "alue_taydentava", "geomFieldName": "geom", "geometryType": QgsWkbTypes.PolygonGeometry, "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.kaavaobjekti_viiva", "userFriendlyTableName": YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA, "featureType": "viiva", "geomFieldName": "geom", "geometryType": QgsWkbTypes.LineGeometry, "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.kaavaobjekti_piste", "userFriendlyTableName": YleiskaavaDatabase.KAAVAOBJEKTI_PISTE, "featureType": "piste", "geomFieldName": "geom", "geometryType": QgsWkbTypes.PointGeometry, "showInCopySourceToTargetUI": True},
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

        self.fieldInfosSpatialFeature = [
            {
            "name": "id",
            "type": "uuid"
            },
            {
            "name": "muokkaaja",
            "type": "String"
            },
            {
            "name": "voimaantulopvm",
            "type": "Date"
            },
            {
            "name": "kumoamispvm",
            "type": "Date"
            },
            {
            "name": "version_alkamispvm",
            "type": "Date"
            },
            {
            "name": "version_loppumispvm",
            "type": "Date"
            },
            {
            "name": "kaavamaaraysotsikko",
            "type": "String"
            },
            {
            "name": "kayttotarkoitus_lyhenne",
            "type": "String"
            },
            {
            "name": "nro",
            "type": "String"
            },
            {
            "name": "paikan_nimi",
            "type": "String"
            },
            {
            "name": "katuosoite",
            "type": "String"
            },
            {
            "name": "karttamerkinta_teksti",
            "type": "String"
            },
            {
            "name": "pinta_ala_ha",
            "type": "Double"
            },
            {
            "name": "luokittelu",
            "type": "String"
            },
            {
            "name": "lisatieto",
            "type": "String"
            },
            {
            "name": "lisatieto2",
            "type": "String"
            },
            {
            "name": "muutos_lisatieto",
            "type": "String"
            },
            {
            "name": "aineisto_lisatieto",
            "type": "String"
            },
            {
            "name": "id_yleiskaava",
            "type": "uuid"
            },
            {
            "name": "id_kansallinen_prosessin_vaihe",
            "type": "uuid"
            },
            {
            "name": "id_kaavakohteen_olemassaolo",
            "type": "uuid"
            },
            {
            "name": "id_kansallisen_kaavakohteen_olemassaolo",
            "type": "uuid"
            },
            {
            "name": "id_laillinen_sitovuus",
            "type": "uuid"
            },
            {
            "name": "id_prosessin_vaihe",
            "type": "uuid"
            },
            {
            "name": "id_kaavoitusprosessin_tila",
            "type": "uuid"
            },
            {
            "name": "rakennusoikeus_kem",
            "type": "Int"
            },
            {
            "name": "rakennusoikeus_lkm",
            "type": "Int"
            }]

        self.fieldInfosSuplementarySpatialFeature = [
            {
            "name": "id",
            "type": "uuid"
            },
            {
            "name": "muokkaaja",
            "type": "String"
            },
            {
            "name": "voimaantulopvm",
            "type": "Date"
            },
            {
            "name": "kumoamispvm",
            "type": "Date"
            },
            {
            "name": "version_alkamispvm",
            "type": "Date"
            },
            {
            "name": "version_loppumispvm",
            "type": "Date"
            },
            {
            "name": "kaavamaaraysotsikko",
            "type": "String"
            },
            {
            "name": "kayttotarkoitus_lyhenne",
            "type": "String"
            },
            {
            "name": "nro",
            "type": "String"
            },
            {
            "name": "paikan_nimi",
            "type": "String"
            },
            {
            "name": "katuosoite",
            "type": "String"
            },
            {
            "name": "karttamerkinta_teksti",
            "type": "String"
            },
            {
            "name": "pinta_ala_ha",
            "type": "Double"
            },
            {
            "name": "luokittelu",
            "type": "String"
            },
            {
            "name": "lisatieto",
            "type": "String"
            },
            {
            "name": "lisatieto2",
            "type": "String"
            },
            {
            "name": "muutos_lisatieto",
            "type": "String"
            },
            {
            "name": "aineisto_lisatieto",
            "type": "String"
            },
            {
            "name": "kohde_periytyy_muualta",
            "type": "Bool"
            },
            {
            "name": "kansallinen_laillinen_sitovuus",
            "type": "String"
            },
            {
            "name": "id_yleiskaava",
            "type": "uuid"
            },
            {
            "name": "id_kansallinen_prosessin_vaihe",
            "type": "uuid"
            },
            {
            "name": "id_kaavakohteen_olemassaolo",
            "type": "uuid"
            },
            {
            "name": "id_kansallisen_kaavakohteen_olemassaolo",
            "type": "uuid"
            },
            {
            "name": "id_laillinen_sitovuus",
            "type": "uuid"
            },
            {
            "name": "id_prosessin_vaihe",
            "type": "uuid"
            },
            {
            "name": "id_kaavoitusprosessin_tila",
            "type": "uuid"
            },
            {
            "name": "rakennusoikeus_kem",
            "type": "Int"
            },
            {
            "name": "rakennusoikeus_lkm",
            "type": "Int"
            }]

        self.fieldInfosLineFeature = [
            {
            "name": "id",
            "type": "uuid"
            },
            {
            "name": "muokkaaja",
            "type": "String"
            },
            {
            "name": "voimaantulopvm",
            "type": "Date"
            },
            {
            "name": "kumoamispvm",
            "type": "Date"
            },
            {
            "name": "version_alkamispvm",
            "type": "Date"
            },
            {
            "name": "version_loppumispvm",
            "type": "Date"
            },
            {
            "name": "kaavamaaraysotsikko",
            "type": "String"
            },
            {
            "name": "kayttotarkoitus_lyhenne",
            "type": "String"
            },
            {
            "name": "nro",
            "type": "String"
            },
            {
            "name": "paikan_nimi",
            "type": "String"
            },
            {
            "name": "katuosoite",
            "type": "String"
            },
            {
            "name": "karttamerkinta_teksti",
            "type": "String"
            },
            {
            "name": "pituus_km",
            "type": "Double"
            },
            {
            "name": "luokittelu",
            "type": "String"
            },
            {
            "name": "lisatieto",
            "type": "String"
            },
            {
            "name": "lisatieto2",
            "type": "String"
            },
            {
            "name": "muutos_lisatieto",
            "type": "String"
            },
            {
            "name": "aineisto_lisatieto",
            "type": "String"
            },
            {
            "name": "kohde_periytyy_muualta",
            "type": "Bool"
            },
            {
            "name": "kansallinen_laillinen_sitovuus",
            "type": "String"
            },
            {
            "name": "id_yleiskaava",
            "type": "uuid"
            },
            {
            "name": "id_kansallinen_prosessin_vaihe",
            "type": "uuid"
            },
            {
            "name": "id_kaavakohteen_olemassaolo",
            "type": "uuid"
            },
            {
            "name": "id_kansallisen_kaavakohteen_olemassaolo",
            "type": "uuid"
            },
            {
            "name": "id_laillinen_sitovuus",
            "type": "uuid"
            },
            {
            "name": "id_prosessin_vaihe",
            "type": "uuid"
            },
            {
            "name": "id_kaavoitusprosessin_tila",
            "type": "uuid"
            }]

        self.fieldInfosPointFeature = [
            {
            "name": "id",
            "type": "uuid"
            },
            {
            "name": "muokkaaja",
            "type": "String"
            },
            {
            "name": "voimaantulopvm",
            "type": "Date"
            },
            {
            "name": "kumoamispvm",
            "type": "Date"
            },
            {
            "name": "version_alkamispvm",
            "type": "Date"
            },
            {
            "name": "version_loppumispvm",
            "type": "Date"
            },
            {
            "name": "kaavamaaraysotsikko",
            "type": "String"
            },
            {
            "name": "kayttotarkoitus_lyhenne",
            "type": "String"
            },
            {
            "name": "nro",
            "type": "String"
            },
            {
            "name": "paikan_nimi",
            "type": "String"
            },
            {
            "name": "katuosoite",
            "type": "String"
            },
            {
            "name": "karttamerkinta_teksti",
            "type": "String"
            },
            {
            "name": "luokittelu",
            "type": "String"
            },
            {
            "name": "lisatieto",
            "type": "String"
            },
            {
            "name": "lisatieto2",
            "type": "String"
            },
            {
            "name": "muutos_lisatieto",
            "type": "String"
            },
            {
            "name": "aineisto_lisatieto",
            "type": "String"
            },
            {
            "name": "kohde_periytyy_muualta",
            "type": "Bool"
            },
            {
            "name": "kansallinen_laillinen_sitovuus",
            "type": "String"
            },
            {
            "name": "id_yleiskaava",
            "type": "uuid"
            },
            {
            "name": "id_kansallinen_prosessin_vaihe",
            "type": "uuid"
            },
            {
            "name": "id_kaavakohteen_olemassaolo",
            "type": "uuid"
            },
            {
            "name": "id_kansallisen_kaavakohteen_olemassaolo",
            "type": "uuid"
            },
            {
            "name": "id_laillinen_sitovuus",
            "type": "uuid"
            },
            {
            "name": "id_prosessin_vaihe",
            "type": "uuid"
            },
            {
            "name": "id_kaavoitusprosessin_tila",
            "type": "uuid"
            }]

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


    def getTargetLayerByUserFriendlyName(self, name):
        return QgsProject.instance().mapLayersByName(name)[0]


    def getLayerByTargetSchemaTableName(self, name):
        targetLayer = self.getProjectLayer(name)
        #if targetLayer.isValid():
        return targetLayer
        #else:
        #    return None


    def getSpatialPlans(self, shouldRetry=True):
        if self.plans is None:
            self.plans = []
            try:
                with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                    query = "SELECT id, nimi, nro, id_kaavan_taso FROM yk_yleiskaava.yleiskaava"
                    cursor.execute(query)
                    rows = cursor.fetchall()

                    planLevels = self.getYleiskaavaPlanLevelList()

                    for index, row in enumerate(rows):
                        planLevelCode = None
                        if row['id_kaavan_taso'] is not None:
                            for planLevel in planLevels:
                                if planLevel['id'] == row['id_kaavan_taso']:
                                    planLevelCode = planLevel['koodi']
                                    break

                        self.plans.append({
                            "id": row['id'],
                            "nimi": row['nimi'],
                            "nro": row['nro'],
                            "kaavan_taso_koodi": planLevelCode
                            })
            except psycopg2.Error as e:
                if shouldRetry:
                    success = self.reconnectToDB()
                    if success:
                        return self.getSpatialPlans(shouldRetry=False)


        return self.plans


    def getSpatialPlanIDAndNumberForPlanName(self, planName):
        id = None
        nro = None

        plans = self.getSpatialPlans()
        for plan in plans:
            if plan["nimi"] == planName:
                id = plan["id"]
                nro = plan["nro"]
                break

        return id, nro


    def getSpatialPlansAndPlanLevels(self, shouldRetry=True):

        planLevels = self.getYleiskaavaPlanLevelList()

        if self.plans is None:
            self.plans = []
            try:
                with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                    query = "SELECT id, nimi, nro, id_kaavan_taso FROM yk_yleiskaava.yleiskaava"
                    cursor.execute(query)
                    rows = cursor.fetchall()

                    for index, row in enumerate(rows):
                        planLevelCode = None
                        if row['id_kaavan_taso'] is not None:
                            for planLevel in planLevels:
                                if planLevel['id'] == row['id_kaavan_taso']:
                                    planLevelCode = planLevel['koodi']
                                    break

                        self.plans.append({
                            "id": row['id'],
                            "nimi": row['nimi'],
                            "nro": row['nro'],
                            "kaavan_taso_koodi": planLevelCode
                            })
            except psycopg2.Error as e:
                if shouldRetry:
                    success = self.reconnectToDB()
                    if success:
                        return self.getSpatialPlansAndPlanLevels(shouldRetry=False)

        # for planLevel in planLevels:
        #     QgsMessageLog.logMessage('getSpatialPlansAndPlanLevels - row[id]: ' + row['id'], 'Yleiskaava-työkalu', Qgis.Info)

        return self.plans, planLevels


    def getPlanNumberForName(self, planName):
        planNumber = None

        layer = self.getLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
        featureRequest = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(["nimi", "nro"], layer.fields())
        features = layer.getFeatures(featureRequest)

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
        featureRequest = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(["id", "nro"], layer.fields())
        features = layer.getFeatures(featureRequest)

        plans = []
        for index, feature in enumerate(features):
            if feature['id'] == planID:
                if feature['nro'] is not None:
                    planNumber = feature['nro']
                break

        return planNumber
        

    def getPlanNameForPlanID(self, planID):
        planName = None

        plans = self.getSpatialPlans()
    
        for index, plan in enumerate(plans):
            if plan['id'] == planID:
                if plan['nimi'] is not None:
                    planName = plan['nimi']
                break

        return planName


    def getYleiskaavaPlanLevelCodeWithPlanName(self, planName):
        planLevelCode = None

        layer = self.getLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
        featureRequest = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(["nimi", "id_kaavan_taso"], layer.fields())
        features = layer.getFeatures(featureRequest)

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


    def getYleiskaavaPlanLevelList(self, shouldRetry=True):

        if self.planLevelList == None:
            self.planLevelList = []

            try:
                with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                    query = "SELECT id, koodi, kuvaus FROM yk_koodiluettelot.kaavan_taso"
                    cursor.execute(query)
                    rows = cursor.fetchall()

                for row in rows:
                    # QgsMessageLog.logMessage('getYleiskaavaPlanLevelList - row[id]: ' + row['id'], 'Yleiskaava-työkalu', Qgis.Info)
                    self.planLevelList.append({
                        "id": row['id'],
                        "koodi": row['koodi'],
                        "kuvaus": row['kuvaus']})
            except psycopg2.Error as e:
                if shouldRetry:
                    success = self.reconnectToDB()
                    if success:
                        return self.getYleiskaavaPlanLevelList(shouldRetry=False)

        return self.planLevelList


    def getSpatialPlanIDForPlanName(self, planName):
        planID = None

        layer = self.getLayerByTargetSchemaTableName("yk_yleiskaava.yleiskaava")
        featureRequest = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(["id", "nimi"], layer.fields())
        features = layer.getFeatures(featureRequest)

        plans = []
        for index, feature in enumerate(features):
            if feature['nimi'] == planName:
                if not feature['id']:
                    planID = None
                else:
                    planID = feature['id']
                break

        return planID


    def getSpatialFeaturesWithRegulationForType(self, regulationID, featureType):
        spatialFeatures = []

        targetLayer = self.getProjectLayer("yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys")
        featureRequest = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(["id_kaavamaarays", "id_kaavaobjekti_" + featureType], targetLayer.fields())
        for feature in targetLayer.getFeatures(featureRequest):

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
        featureRequest = QgsFeatureRequest().setFilterExpression("\"id\"='{}'".format(featureID))
        features = layer.getFeatures(featureRequest)
        featureList = list(features)
        if len(featureList) > 0:
            return featureList[0]

        return None


    def getRegulationCountForSpatialFeature(self, featureID, featureType, shouldRetry=True):
        count = 0

        try:
            with self.dbConnection.cursor() as cursor:
                query = "SELECT COUNT(*) FROM yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys WHERE id_kaavaobjekti_{} = %s".format(featureType)
                cursor.execute(query, (featureID, ))
                row = cursor.fetchone()
                count = row[0]
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.getRegulationCountForSpatialFeature(featureID, featureType, shouldRetry=False)

        return count


    def getDistinctLandUseClassificationsOfLayer(self, userFriendlyTableName, shouldRetry=True):
        classifications = []
        featureType = self.getFeatureTypeForUserFriendlyTargetSchemaTableName(userFriendlyTableName)

        try:
            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                query = "SELECT DISTINCT kayttotarkoitus_lyhenne FROM yk_yleiskaava.kaavaobjekti_{} WHERE kayttotarkoitus_lyhenne IS NOT NULL AND kayttotarkoitus_lyhenne != ''".format(featureType)
                cursor.execute(query)
                rows = cursor.fetchall()
                for row in rows:
                    classifications.append(row['kayttotarkoitus_lyhenne'])
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.getDistinctLandUseClassificationsOfLayer(userFriendlyTableName, shouldRetry=False)

        return classifications


    def getLayerFeatureIDsAndFieldValuesForFeaturesHavingLanduseClassification(self, userFriendlyTableName, landUseClassification, fieldName, shouldRetry=True):
        featureIDsAndValues = []

        featureType = self.getFeatureTypeForUserFriendlyTargetSchemaTableName(userFriendlyTableName)

        try:
            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                query = "SELECT id, {} FROM yk_yleiskaava.kaavaobjekti_{} WHERE %(fieldName)s IS NOT NULL AND %(fieldName)s != '' AND kayttotarkoitus_lyhenne = %(landUseClassification)s".format(fieldName, featureType)
                cursor.execute(query, {"fieldName" : fieldName, "landUseClassification": landUseClassification})
                rows = cursor.fetchall()
                for row in rows:
                    featureIDsAndValues.append({
                        "id": row["id"],
                        "value": row[fieldName]
                    })
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.getLayerFeatureIDsAndFieldValuesForFeaturesHavingLanduseClassification(userFriendlyTableName, landUseClassification, fieldName, shouldRetry=False)

        return featureIDsAndValues


    def getRegulationsForSpatialFeature(self, featureID, featureType, shouldRetry=True):
        regulationList = []

        regulations = None
        if featureType == "alue":
            regulations = self.getSpecificRegulations(includeSuplementaryAreaRegulations=False, includeLineRegulations=False, includePointRegulations=False)
        elif featureType == "alue_taydentava":
            regulations = self.getSpecificRegulations(includeAreaRegulations=False, includeLineRegulations=False, includePointRegulations=False)
        elif featureType == "viiva":
            regulations = self.getSpecificRegulations(includeAreaRegulations=False, includeSuplementaryAreaRegulations=False, includePointRegulations=False)
        elif featureType == "piste":
            regulations = self.getSpecificRegulations(includeAreaRegulations=False, includeSuplementaryAreaRegulations=False, includeLineRegulations=False)

        try:
            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                query = "SELECT id_kaavamaarays FROM yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys WHERE id_kaavaobjekti_{} = %s".format(featureType)
                cursor.execute(query, (featureID, ))
                rows = cursor.fetchall()

                for row in rows:
                    for regulation in regulations:
                        if regulation["id"] == row["id_kaavamaarays"]:
                            # QgsMessageLog.logMessage("getRegulationsForSpatialFeature - kaavamääräys lisätään palautettavaan listaan, jos kaavamaarays_otsikko ei null, feature['kaavamaarays_otsikko']: " + str(regulation['kaavamaarays_otsikko'].value()), 'Yleiskaava-työkalu', Qgis.Info)
                                if regulation["kaavamaarays_otsikko"] is not None:
                                    # QgsMessageLog.logMessage("getRegulationsForSpatialFeature - kaavamääräys lisätään palautettavaan listaan, regulation['kaavamaarays_otsikko']: " + str(regulation['kaavamaarays_otsikko'].value()), 'Yleiskaava-työkalu', Qgis.Info)
                                    regulationList.append(regulation)
                                break
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.getRegulationsForSpatialFeature(featureID, featureType, shouldRetry = False)

        return regulationList


    def getSpecificRegulations(self, onlyUsedRegulations=False, includeAreaRegulations=True, includeSuplementaryAreaRegulations=True, includeLineRegulations=True, includePointRegulations=True):

        regulationList = []

        if includeAreaRegulations:
            query = None
            if onlyUsedRegulations:
                query = "SELECT DISTINCT id_kaavamaarays FROM yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys WHERE id_kaavaobjekti_alue IS NOT NULL AND id_kaavaobjekti_alue in (SELECT id FROM yk_yleiskaava.kaavaobjekti_alue WHERE version_loppumispvm IS NULL)"
            else:
                query = "SELECT DISTINCT id_kaavamaarays FROM yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys WHERE id_kaavaobjekti_alue IS NOT NULL"

            regulationList.extend(self.getSpecificRegulationsForSubQuery(query))

        if includeSuplementaryAreaRegulations:
            query = None
            if onlyUsedRegulations:
                query = "SELECT DISTINCT id_kaavamaarays FROM yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys WHERE id_kaavaobjekti_alue_taydentava IS NOT NULL AND id_kaavaobjekti_alue_taydentava in (SELECT id FROM yk_yleiskaava.kaavaobjekti_alue_taydentava WHERE version_loppumispvm IS NULL)"
            else:
                query = "SELECT DISTINCT id_kaavamaarays FROM yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys WHERE id_kaavaobjekti_alue_taydentava IS NOT NULL"

            regulationList.extend(self.getSpecificRegulationsForSubQuery(query))
        
        if includeLineRegulations:
            query = None
            if onlyUsedRegulations:
                query = "SELECT DISTINCT id_kaavamaarays FROM yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys WHERE id_kaavaobjekti_viiva IS NOT NULL AND id_kaavaobjekti_viiva in (SELECT id FROM yk_yleiskaava.kaavaobjekti_viiva WHERE version_loppumispvm IS NULL)"
            else:
                query = "SELECT DISTINCT id_kaavamaarays FROM yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys WHERE id_kaavaobjekti_viiva IS NOT NULL"

            regulationList.extend(self.getSpecificRegulationsForSubQuery(query))

        if includePointRegulations:
            query = None
            if onlyUsedRegulations:
                query = "SELECT DISTINCT id_kaavamaarays FROM yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys WHERE id_kaavaobjekti_piste IS NOT NULL AND id_kaavaobjekti_piste in (SELECT id FROM yk_yleiskaava.kaavaobjekti_piste WHERE version_loppumispvm IS NULL)"
            else:
                query = "SELECT DISTINCT id_kaavamaarays FROM yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys WHERE id_kaavaobjekti_piste IS NOT NULL"

            regulationList.extend(self.getSpecificRegulationsForSubQuery(query))

        return regulationList


    def getSpecificRegulationsForSubQuery(self, subQuery, shouldRetry=True):
        regulationList = []
        try:
            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as regulationCursor:
                query = "SELECT id, kaavamaarays_otsikko, maaraysteksti, kuvaus_teksti FROM yk_yleiskaava.kaavamaarays WHERE kaavamaarays_otsikko IS NOT NULL and id in ({})".format(subQuery)
                regulationCursor.execute(query)
                regulationRows = regulationCursor.fetchall()
                for regulationRow in regulationRows:
                    regulationList.append({
                        "id": regulationRow['id'],
                        "alpha_sort_key": regulationRow['kaavamaarays_otsikko'],
                        "kaavamaarays_otsikko": QVariant(regulationRow['kaavamaarays_otsikko']),
                        "maaraysteksti": QVariant(regulationRow['maaraysteksti']),
                        "kuvaus_teksti": QVariant(regulationRow['kuvaus_teksti'])
                        })
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.getSpecificRegulationsForSubQuery(subQuery, shouldRetry = False)


        return regulationList


    def shouldAddRegulation(self, regulationID, onlyUsedRegulations=False, includeAreaRegulations=True, includeSuplementaryAreaRegulations=True, includeLineRegulations=True, includePointRegulations=True, shouldRetry=True):

        # Kaavamääräys on käytössä, jos liittyy johonkin kaavakohteeseen, jonka version_loppumispvm is None
        try:
            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as relationCursor:
                query = "SELECT id_kaavaobjekti_alue, id_kaavaobjekti_alue_taydentava, id_kaavaobjekti_viiva, id_kaavaobjekti_piste FROM yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys WHERE id_kaavamaarays = (%s)"
                relationCursor.execute(query, (regulationID, ))
                relationRows = relationCursor.fetchall()
                for relationFeature in relationRows:
                    if includeAreaRegulations and not QVariant(relationFeature["id_kaavaobjekti_alue"]).isNull():
                        if onlyUsedRegulations:
                            
                            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                                query = "SELECT id, version_loppumispvm FROM yk_yleiskaava.kaavaobjekti_alue WHERE id = (%s) AND version_loppumispvm IS NULL"
                                cursor.execute(query, (relationFeature["id_kaavaobjekti_alue"], ))
                                rows = relationCursor.fetchall()
                                if len(rows) > 0:
                                    return True
                        else:
                            return True
                    # else:
                    #     QgsMessageLog.logMessage('isRegulationInUse - relationFeature["id_kaavaobjekti_alue"]: ' + str(relationFeature["id_kaavaobjekti_alue"]) + ', QVariant(relationFeature["id_kaavaobjekti_alue"]).isNull(): ' + str(QVariant(relationFeature["id_kaavaobjekti_alue"]).isNull()), 'Yleiskaava-työkalu', Qgis.Info)
                    elif includeSuplementaryAreaRegulations and not QVariant(relationFeature["id_kaavaobjekti_alue_taydentava"]).isNull():
                        if onlyUsedRegulations:
                            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                                query = "SELECT id, version_loppumispvm FROM yk_yleiskaava.kaavaobjekti_alue_taydentava WHERE id = (%s) AND version_loppumispvm IS NULL"
                                cursor.execute(query, (relationFeature["id_kaavaobjekti_alue_taydentava"], ))
                                rows = relationCursor.fetchall()
                                if len(rows) > 0:
                                    return True
                        else:
                            return True
                    elif includeLineRegulations and not QVariant(relationFeature["id_kaavaobjekti_viiva"]).isNull():
                        if onlyUsedRegulations:
                            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                                query = "SELECT id, version_loppumispvm FROM yk_yleiskaava.kaavaobjekti_viiva WHERE id = (%s) AND version_loppumispvm IS NULL"
                                cursor.execute(query, (relationFeature["id_kaavaobjekti_viiva"], ))
                                rows = relationCursor.fetchall()
                                if len(rows) > 0:
                                    return True
                        else:
                            return True
                    elif includePointRegulations and not QVariant(relationFeature["id_kaavaobjekti_piste"]).isNull():
                        if onlyUsedRegulations:
                            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                                query = "SELECT id, version_loppumispvm FROM yk_yleiskaava.kaavaobjekti_piste WHERE id = (%s) AND version_loppumispvm IS NULL"
                                cursor.execute(query, (relationFeature["id_kaavaobjekti_piste"], ))
                                rows = relationCursor.fetchall()
                                if len(rows) > 0:
                                    return True
                        else:
                            return True
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.shouldAddRegulation(regulationID, onlyUsedRegulations, includeAreaRegulations, includeSuplementaryAreaRegulations, includeLineRegulations, includePointRegulations, shouldRetry = False)

        return False


    def updateRegulation(self, regulationID, regulationTitle, regulationText, regulationDescription):
        layer = self.getProjectLayer("yk_yleiskaava.kaavamaarays")

        featureRequest = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(["id", "kaavamaarays_otsikko", "maaraysteksti", "kuvaus_teksti"], layer.fields())
        for feature in layer.getFeatures(featureRequest):
            if feature["id"] == regulationID:
                fid = feature.id()
                indexTitle = layer.fields().indexFromName("kaavamaarays_otsikko")
                indexText = layer.fields().indexFromName("maaraysteksti")
                indexDescription = layer.fields().indexFromName("kuvaus_teksti")
                attrs = { indexTitle: regulationTitle, indexText: regulationText, indexDescription: indexDescription }
                success = layer.dataProvider().changeAttributeValues({ fid: attrs })
                if not success:
                    self.iface.messageBar().pushMessage('updateRegulation - commitChanges() failed', Qgis.Critical)
                    return False
                break

        return True


    def removeSpatialFeatureRegulationAndLandUseClassification(self, featureID, featureType, shouldUpdateOnlyRelation):
        self.removeRegulationRelationsFromSpatialFeature(featureID, featureType)

        layer = self.getProjectLayer("yk_yleiskaava.kaavaobjekti_" + featureType)
        feature = self.findSpatialFeatureFromFeatureLayerWithID(layer, featureID)

        if not shouldUpdateOnlyRelation:
            fid = feature.id()
            indexTitle = layer.fields().indexFromName("kaavamaaraysotsikko")
            indexLandUseClass = layer.fields().indexFromName("kayttotarkoitus_lyhenne")
            attrs = { indexTitle: None, indexLandUseClass: None }
            success = layer.dataProvider().changeAttributeValues({ fid: attrs })
            if not success:
                self.iface.messageBar().pushMessage('removeSpatialFeatureRegulationAndLandUseClassification - commitChanges() failed', Qgis.Critical)
                return False

        return True


    def removeSpatialFeatureThemes(self, featureID, featureType):
        self.removeThemeRelationsFromSpatialFeature(featureID, featureType)

        return True
        

    def updateSpatialFeatureRegulationAndLandUseClassification(self, featureID, featureType, regulationID, regulationTitle, shouldRemoveOldRegulationRelations, shouldUpdateOnlyRelation, shouldRetry=True):
        # remove old regulation relations if shouldRemoveOldRegulationRelations
        # lisää yhteys kaavaobjekti_kaavamaarays_yhteys-tauluun, jos yhteyttä ei vielä ole

        try:
            if shouldRemoveOldRegulationRelations:
                self.removeRegulationRelationsFromSpatialFeature(featureID, featureType)

            if not self.existsFeatureRegulationRelation(featureID, featureType, regulationID):
                self.createFeatureRegulationRelationWithRegulationID("yk_yleiskaava.kaavaobjekti_" + featureType, featureID, regulationID)

            # return True

            if not shouldUpdateOnlyRelation:
                landUseClassificationName = regulationTitle

                with self.dbConnection.cursor() as cursor:
                    query = "SELECT nro FROM yk_yleiskaava.yleiskaava WHERE id = (SELECT id_yleiskaava FROM yk_yleiskaava.kaavaobjekti_{} ko WHERE id = %s)".format(featureType)

                    # QgsMessageLog.logMessage("updateSpatialFeatureRegulationAndLandUseClassification - query: " + query, 'Yleiskaava-työkalu', Qgis.Info)

                    cursor.execute(query, (featureID, ))
                    row = cursor.fetchone()
                    if row is not None and row[0] is not None:
                        planNumber = row[0]
                        landUseClassificationName = self.yleiskaavaUtils.getLandUseClassificationNameForRegulation(planNumber, "yk_yleiskaava.kaavaobjekti_" + featureType, regulationTitle)

                    query = "UPDATE yk_yleiskaava.kaavaobjekti_{} SET kaavamaaraysotsikko = %s, kayttotarkoitus_lyhenne = %s WHERE id = %s".format(featureType)
                    cursor.execute(query, (regulationTitle, landUseClassificationName, featureID))
                    self.dbConnection.commit()

                # if not success:
                #     self.iface.messageBar().pushMessage('updateSpatialFeatureRegulationAndLandUseClassificationTexts - commitChanges() failed', Qgis.Critical)
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.updateSpatialFeatureRegulationAndLandUseClassification(featureID, featureType, regulationID, regulationTitle, shouldRemoveOldRegulationRelations, shouldUpdateOnlyRelation, shouldRetry = False)

        return True


    def existsFeatureRegulationRelation(self, featureID, featureType, regulationID, shouldRetry=True):
        try:
            with self.dbConnection.cursor() as cursor:
                query = "SELECT id FROM yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys WHERE id_kaavaobjekti_{} = %s AND id_kaavamaarays = %s".format(featureType)
                cursor.execute(query, (featureID, regulationID))
                if len(cursor.fetchall()) > 0:
                    return True
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.existsFeatureRegulationRelation(featureID, featureType, regulationID, shouldRetry = False)

        return False


    def removeRegulationRelationsFromSpatialFeature(self, featureID, featureType, shouldRetry=True):
        try:
            with self.dbConnection.cursor() as cursor:
                query = "DELETE FROM yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys WHERE id_kaavaobjekti_{} = %s".format(featureType)
                cursor.execute(query, (featureID, ))
                self.dbConnection.commit()
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    self.removeRegulationRelationsFromSpatialFeature(featureID, featureType, shouldRetry = False)


    def deleteSpatialFeature(self, featureID, featureType, shouldRetry=True):
        try:
            with self.dbConnection.cursor() as cursor:
                query = "DELETE FROM yk_yleiskaava.kaavaobjekti_{} WHERE id = %s".format(featureType)
                cursor.execute(query, (featureID, ))
                self.dbConnection.commit()
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    self.deleteSpatialFeature(featureID, featureType, shouldRetry = False)


    def createFeatureRegulationRelation(self, targetSchemaTableName, targetFeatureID, regulationTitle):
        regulationID = self.findRegulationID(regulationTitle)

        self.createFeatureRegulationRelationWithRegulationID(targetSchemaTableName, targetFeatureID, regulationID)


    def createFeatureRegulationRelationWithRegulationID(self, targetSchemaTableName, targetFeatureID, regulationID, shouldRetry=True):
        # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - targetSchemaTableName: " + targetSchemaTableName + ", targetFeatureID: " + str(targetFeatureID) + ", regulationID: " + str(regulationID), 'Yleiskaava-työkalu', Qgis.Info)

        try:
            schema, table_name = targetSchemaTableName.split('.')

            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                query = "INSERT INTO yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys (id, id_{}, id_kaavamaarays) VALUES (%s, %s, %s)".format(table_name)
                cursor.execute(query, (str(uuid.uuid4()), targetFeatureID, regulationID))
                self.dbConnection.commit()
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    self.createFeatureRegulationRelationWithRegulationID(targetSchemaTableName, targetFeatureID, regulationID, shouldRetry = False)


    def addRegulationRelationsToLayer(self, sourceFeatureID, targetFeatureID, featureType):
        # NOTE ilmeisesti toimii vain, jos targetFeatureID löytyy jo tallennettuna tietokannasta ko. kaavaobjekti-taulusta
        regulations = self.getRegulationsForSpatialFeature(sourceFeatureID, featureType)
        targetSchemaTableName = "yk_yleiskaava.kaavaobjekti_" + featureType
        for regulation in regulations:
            # QgsMessageLog.logMessage("addRegulationRelationsToLayer - regulation relation lisätään kaavakohteelle, fid: " + str(targetFeatureID), 'Yleiskaava-työkalu', Qgis.Info)
            self.createFeatureRegulationRelationWithRegulationID(targetSchemaTableName, targetFeatureID, regulation["id"])


    def getThemes(self):
        if self.themes is None:
            self.readThemes()
        return self.themes


    def readThemes(self, shouldRetry=True):
        try:
            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                query = "SELECT id, nimi, kuvaus, id_yleiskaava FROM yk_kuvaustekniikka.teema"
                cursor.execute(query)
                rows = cursor.fetchall()

                self.themes = []

                for row in rows:
                    if row["nimi"] is not None:
                        nimi = row["nimi"]
                        kuvaus = row['kuvaus']
                        id_yleiskaava = row['id_yleiskaava']

                        self.themes.append({
                            "id": row['id'],
                            "alpha_sort_key": nimi,
                            "nimi": nimi,
                            "kuvaus": kuvaus,
                            "id_yleiskaava": id_yleiskaava,
                            "yleiskaava_nimi": self.getPlanNameForPlanID(id_yleiskaava)
                            })
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    self.readThemes(shouldRetry = False)


    def getThemesForSpatialFeature(self, featureID, featureType, shouldRetry=True):
        themeList = []

        try:
            themes = self.getThemes()

            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                query = "SELECT id_teema, id_kaavaobjekti_{} FROM yk_kuvaustekniikka.kaavaobjekti_teema_yhteys".format(featureType)
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    if row["id_kaavaobjekti_" + featureType] == featureID:
                        # QgsMessageLog.logMessage("getRegulationsForSpatialFeature - kaavakohde löytyi yhteyksistä, id_kaavaobjekti_*: " + str(feature["id_kaavaobjekti_" + featureType]), 'Yleiskaava-työkalu', Qgis.Info)
                        for theme in themes:
                            if theme["id"] == row["id_teema"]:
                                # QgsMessageLog.logMessage("getRegulationsForSpatialFeature - kaavamääräys lisätään palautettavaan listaan, jos kaavamaarays_otsikko ei null, feature['kaavamaarays_otsikko']: " + str(regulation['kaavamaarays_otsikko'].value()), 'Yleiskaava-työkalu', Qgis.Info)
                                if theme["nimi"] is not None:
                                    # QgsMessageLog.logMessage("getRegulationsForSpatialFeature - kaavamääräys lisätään palautettavaan listaan, regulation['kaavamaarays_otsikko']: " + str(regulation['kaavamaarays_otsikko'].value()), 'Yleiskaava-työkalu', Qgis.Info)
                                    themeList.append(theme)
                                break
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.getThemesForSpatialFeature(featureID, featureType, shouldRetry = False)

        return themeList


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
        provider = regulationLayer.dataProvider()
        provider.addFeatures([regulationFeature])

        self.createFeatureRegulationRelationWithRegulationID(targetSchemaTableName, targetFeatureID, regulationID)


    def getCodeListValuesForPlanObjectField(self, targetFieldName):
        name = "yk_koodiluettelot." + targetFieldName[3:]

        if name not in self.codeTableCodes:
            self.readCodeTableCodesFromDatabase(name)
                        
        return self.codeTableCodes[name]


    def getCodeListValueForPlanObjectFieldUUID(self, targetFieldName, value):
        codeValue = None
        name = "yk_koodiluettelot." + targetFieldName[3:]

        if name not in self.codeTableCodes:
            self.readCodeTableCodesFromDatabase(name)

        for item in self.codeTableCodes[name]:
            if item['id'] == value:
                codeValue =  item['koodi']
                break

        return codeValue


    def getCodeListUUIDForPlanObjectFieldCodeValue(self, targetFieldName, value):
        uuid = None
        name = "yk_koodiluettelot." + targetFieldName[3:]

        if name not in self.codeTableCodes:
            self.readCodeTableCodesFromDatabase(name)
        
        # if table_name == "kansallinen_prosessin_vaihe" or table_name == "prosessin_vaihe" or table_name == "kaavoitusprosessin_tila" or table_name == "laillinen_sitovuus":
        for item in self.codeTableCodes[name]:
            if item['koodi'] == value:
                uuid =  item['id']
                break

        return uuid


    def readCodeTableCodesFromDatabase(self, name, shouldRetry=True):
        try:
            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                query = "SELECT id, koodi FROM {}".format(name)
                cursor.execute(query)
                rows = cursor.fetchall()
                self.codeTableCodes[name] = []
                for row in rows:
                    self.codeTableCodes[name].append({'id': row['id'], 'koodi': row['koodi']})
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    self.readCodeTableCodesFromDatabase(name, shouldRetry = False)


    def getSchemaTableFieldInfos(self, name):
        fieldInfos = []

        if name == "yk_yleiskaava.kaavaobjekti_alue":
           fieldInfos = self.fieldInfosSpatialFeature
        elif name == "yk_yleiskaava.kaavaobjekti_alue_taydentava":
           fieldInfos = self.fieldInfosSuplementarySpatialFeature
        elif name == "yk_yleiskaava.kaavaobjekti_viiva":
            fieldInfos = self.fieldInfosLineFeature
        elif name == "yk_yleiskaava.kaavaobjekti_piste":
            fieldInfos = self.fieldInfosPointFeature

        return fieldInfos


    def getFieldNamesAndTypes(self, featureType):
        fieldInfos = []

        name = "yk_yleiskaava.kaavaobjekti_" + featureType

        if name == "yk_yleiskaava.kaavaobjekti_alue":
           fieldInfos = self.fieldInfosSpatialFeature
        elif name == "yk_yleiskaava.kaavaobjekti_alue_taydentava":
           fieldInfos = self.fieldInfosSuplementarySpatialFeature
        elif name == "yk_yleiskaava.kaavaobjekti_viiva":
            fieldInfos = self.fieldInfosLineFeature
        elif name == "yk_yleiskaava.kaavaobjekti_piste":
            fieldInfos = self.fieldInfosPointFeature

        return fieldInfos


    # def getSchemaTableFields(self, name):
    #     layer = self.getProjectLayer(name)
    #     return layer.fields().toList()


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


    def getSelectedFeatures(self, featureType, subsetOfAttributes=None):
        layer = self.getTargetLayer(featureType)
        featureRequest = QgsFeatureRequest()
        if subsetOfAttributes is not None:
            featureRequest.setSubsetOfAttributes(subsetOfAttributes, layer.fields())
        # QgsMessageLog.logMessage("getSelectedFeatures - layer.selectedFeatureCount(): " + str(layer.selectedFeatureCount()), 'Yleiskaava-työkalu', Qgis.Info)

        return layer.getSelectedFeatures(featureRequest)


    def getTargetLayer(self, featureType):
        layer = None

        if featureType == "alue":
            layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE)[0]
        elif featureType == "alue_taydentava":
            layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA)[0]
        elif featureType == "viiva":
            layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA)[0]
        elif featureType == "piste":
            layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_PISTE)[0]

        return layer

    
    def updateSpatialFeaturesWithFieldValues(self, layer, featureIDsAndValues, fieldName, shouldRetry=True):
        try:
            with self.dbConnection.cursor() as cursor:
                schemaTableName = self.getTargetSchemaTableNameForUserFriendlyTableName(layer.name())

                for featureIDAndValue in featureIDsAndValues:
                    query = "UPDATE {} SET {} = %s WHERE id = %s".format(schemaTableName, fieldName)

                    QgsMessageLog.logMessage("updateSpatialFeaturesWithFieldValues - query: " + query, 'Yleiskaava-työkalu', Qgis.Info)

                    cursor.execute(query, (featureIDAndValue["value"], featureIDAndValue["id"]))

                self.dbConnection.commit()
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.updateSpatialFeaturesWithFieldValues(layer, featureIDsAndValues, fieldName, shouldRetry = False)


        return True


    def updateSelectedSpatialFeaturesWithFieldValues(self, featureType, updatedFieldData, shouldRetry=True):
        try:
            with self.dbConnection.cursor() as cursor:
                layer = self.getTargetLayer(featureType)
                fieldNames = [updatedFieldDataItem["fieldName"] for updatedFieldDataItem in updatedFieldData]
                fieldNames.append("id")
                featureRequest = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(fieldNames, layer.fields())
                features = layer.getSelectedFeatures(featureRequest)

                for feature in features:
                    attrTuple = tuple()

                    query = "UPDATE yk_yleiskaava.kaavaobjekti_{} SET ".format(featureType)

                    for updatedFieldDataItem in updatedFieldData:
                        query += updatedFieldDataItem["fieldName"] + " = %s, "
                        attrTuple += (updatedFieldDataItem["value"], )

                    if len(updatedFieldData) > 0:
                        query = query[:-2]
                    attrTuple += (feature["id"], )
                    query += " WHERE id = %s"

                    QgsMessageLog.logMessage("updateSelectedSpatialFeaturesWithFieldValues - query: " + query, 'Yleiskaava-työkalu', Qgis.Info)
                    # QgsMessageLog.logMessage("updateSelectedSpatialFeaturesWithFieldValues - attrTuple: " + ', '.join(str(item) for item in attrTuple), 'Yleiskaava-työkalu', Qgis.Info)

                    cursor.execute(query, attrTuple)
                    self.dbConnection.commit()
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.updateSelectedSpatialFeaturesWithFieldValues(featureType, updatedFieldData, shouldRetry = False)

        return True


    def updateTheme(self, themeID, themeName, themeDescription, shouldRetry=True):
        try:
            with self.dbConnection.cursor() as cursor:
                query = "UPDATE yk_kuvaustekniikka.teema SET nimi = %s, kuvaus = %s WHERE id = %s"
                cursor.execute(query, (themeName, themeDescription, themeID))
                self.dbConnection.commit()

            self.readThemes()
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.updateTheme(themeID, themeName, themeDescription, shouldRetry = False)
        
        return True

    
    def getThemeCountForSpatialFeature(self, featureID, featureType):
        count = 0

        relationLayer = QgsProject.instance().mapLayersByName("kaavaobjekti_teema_yhteys")[0]
        featureRequest = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(["id_kaavaobjekti_" + featureType], relationLayer.fields())
        for feature in relationLayer.getFeatures(featureRequest):
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


    def createFeatureThemeRelationWithThemeID(self, targetSchemaTableName, targetFeatureID, themeID, shouldRetry=True):
        # QgsMessageLog.logMessage("createFeatureRegulationRelationWithRegulationID - targetSchemaTableName: " + targetSchemaTableName + ", targetFeatureID: " + str(targetFeatureID) + ", regulationID: " + str(regulationID), 'Yleiskaava-työkalu', Qgis.Info)

        try:
            schema, table_name = targetSchemaTableName.split('.')

            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                query = "INSERT INTO yk_kuvaustekniikka.kaavaobjekti_teema_yhteys (id, id_{}, id_teema) VALUES (%s, %s, %s)".format(table_name)
                cursor.execute(query, (str(uuid.uuid4()), targetFeatureID, themeID))
                self.dbConnection.commit()
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    self.createFeatureThemeRelationWithThemeID(targetSchemaTableName, targetFeatureID, themeID, shouldRetry = False)


    def existsFeatureThemeRelation(self, featureID, featureType, themeID, shouldRetry=True):
        try:
            with self.dbConnection.cursor() as cursor:
                query = "SELECT id FROM yk_kuvaustekniikka.kaavaobjekti_teema_yhteys WHERE id_kaavaobjekti_{} = %s AND id_teema = %s".format(featureType)
                cursor.execute(query, (featureID, themeID))
                if len(cursor.fetchall()) > 0:
                    return True
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.existsFeatureThemeRelation(featureID, featureType, themeID, shouldRetry = False)

        return False


    def removeThemeRelationsFromSpatialFeature(self, featureID, featureType, shouldRetry=True):
        try:
            with self.dbConnection.cursor() as cursor:
                query = "DELETE FROM yk_kuvaustekniikka.kaavaobjekti_teema_yhteys WHERE id_kaavaobjekti_{} = %s".format(featureType)
                cursor.execute(query, (featureID, ))
                self.dbConnection.commit()
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    self.removeThemeRelationsFromSpatialFeature(featureID, featureType, shouldRetry = False)


    def getSourceDataFeatures(self, linkType, shouldRetry=True):
        features = []

        try:
            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                query = "SELECT id, nimi, lahde, kuvaus, linkitys_tyyppi, linkki_data FROM yk_prosessi.lahtoaineisto WHERE linkitys_tyyppi = %s"
                cursor.execute(query, (linkType, ))
                rows = cursor.fetchall()
                for row in rows:
                    features.append({
                        "id": row["id"],
                        "nimi": row["nimi"],
                        "lahde": row["lahde"],
                        "kuvaus": row["kuvaus"],
                        "linkitys_tyyppi": row["linkitys_tyyppi"],
                        "linkki_data": row["linkki_data"]
                    })
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.getSourceDataFeatures(linkType, shouldRetry = False)

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


    def getLinkedFeatureIDsForSourceDataFeature(self, spatialFeatureLayer, linkedSourceDataFeature, shouldRetry=True):
        linkedFeatureIDs = []

        try:
            targetSchemaTableName = self.getTargetSchemaTableNameForUserFriendlyTableName(spatialFeatureLayer.name())
            schema, table_name = targetSchemaTableName.split('.')

            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                query = "SELECT id_{} FROM yk_prosessi.lahtoaineisto_yleiskaava_yhteys WHERE id_lahtoaineisto = %s AND id_{} IS NOT NULL".format(table_name, table_name)
                cursor.execute(query, (linkedSourceDataFeature["id"], ))
                rows = cursor.fetchall()
                for row in rows:
                    linkedFeatureIDs.append(row["id_" + table_name])
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.getLinkedFeatureIDsForSourceDataFeature(spatialFeatureLayer, linkedSourceDataFeature, shouldRetry = False)

        return linkedFeatureIDs


    def createSourceDataFeature(self, sourceData, shouldRetry=True):
        try:
            sourceDataLayer = QgsProject.instance().mapLayersByName("lahtoaineisto")[0]

            sourceDataFeatureID = str(uuid.uuid4())

            with self.dbConnection.cursor() as cursor:
                query = "INSERT INTO yk_prosessi.lahtoaineisto (id"
                
                attrTuple = (sourceDataFeatureID, )

                for key in sourceData.keys():
                    attrTuple += (sourceData[key], )

                    query += ", {}".format(key)

                query += ") VALUES (%s"
                for key in sourceData.keys():
                    query += ", %s"
                query += ")"

                cursor.execute(query, attrTuple)
                self.dbConnection.commit()
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.createSourceDataFeature(sourceData, shouldRetry = False)

        return sourceDataFeatureID


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


    def createSourceDataRelationToSpatialFeature(self, linkedSourceDataFeatureID, spatialFeatureLayer, targetFeatureID, shouldRetry=True):
        try:
            targetSchemaTableName = self.getTargetSchemaTableNameForUserFriendlyTableName(spatialFeatureLayer.name())
            schema, table_name = targetSchemaTableName.split('.')

            relationFeatureID = str(uuid.uuid4())

            with self.dbConnection.cursor() as cursor:
                query = "INSERT INTO yk_prosessi.lahtoaineisto_yleiskaava_yhteys (id, id_lahtoaineisto, id_{}) VALUES (%s, %s, %s)".format(table_name)
                cursor.execute(query, (relationFeatureID, linkedSourceDataFeatureID, targetFeatureID))
                self.dbConnection.commit()
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.createSourceDataRelationToSpatialFeature(linkedSourceDataFeatureID, spatialFeatureLayer, targetFeatureID, shouldRetry = False)

        return relationFeatureID


    def setDatabaseConnection(self, databaseConnectionParams):
        self.databaseConnectionParams = databaseConnectionParams

        # for key in self.databaseConnectionParams.keys():
        #     QgsMessageLog.logMessage('{}: {}'.format(key, self.databaseConnectionParams[key]), 'Yleiskaava-työkalu', Qgis.Info)

        sucess = self.reconnectToDB()

        return sucess
            

    def getDatabaseConnectionParams(self):
        return self.databaseConnectionParams

    
    def databaseMatchesDataSourceUri(self, dataSourceUri):
        if self.databaseConnectionParams is None:
            return False
            
        parts = dataSourceUri.split(' ')
        for part in parts:
            # QgsMessageLog.logMessage('databaseMatchesDataSourceUri - part: {}'.format(part) , 'Yleiskaava-työkalu', Qgis.Info)
            if part == '(geom)':
                continue
            key, value = part.split('=')
            value = value.replace("'", "")
            if key == 'dbname' and value != self.databaseConnectionParams['dbname']:
                # QgsMessageLog.logMessage('databaseMatchesDataSourceUri - uri, dbname: {}; db, dbname: {}'.format(value, self.databaseConnectionParams['dbname']) , 'Yleiskaava-työkalu', Qgis.Info)
                return False
            elif key == 'host':
                if value != self.databaseConnectionParams['host']:
                    valueParts = value.split('.')
                    dbValueParts = self.databaseConnectionParams['host'].split('.')
                    valuePartsAllNumbers = True
                    dbValuePartsAllNumbers = True
                    for valuePart in valueParts:
                        if not valuePart.isdigit():
                            valuePartsAllNumbers = False
                            break
                    for valuePart in dbValueParts:
                        if not valuePart.isdigit():
                            dbValuePartsAllNumbers = False
                            break
                    
                    if valuePartsAllNumbers and dbValuePartsAllNumbers:
                        # QgsMessageLog.logMessage('databaseMatchesDataSourceUri - uri, host: {}; db, host: {}'.format(value, self.databaseConnectionParams['host']) , 'Yleiskaava-työkalu', Qgis.Info)
                        return False

                    ipAddrForURI = value
                    ipAddrForDB = self.databaseConnectionParams['host']

                    if not valuePartsAllNumbers:
                        ipAddrForURI = socket.gethostbyname(value)
                    
                    if not dbValuePartsAllNumbers:
                        ipAddrForDB = socket.gethostbyname(value)

                    if ipAddrForURI != ipAddrForDB:
                        # QgsMessageLog.logMessage('databaseMatchesDataSourceUri - uri, ipAddrForURI: {}; db, ipAddrForURI: {}'.format(ipAddrForURI, ipAddrForDB) , 'Yleiskaava-työkalu', Qgis.Info)
                        return False
        
        return True


    def reconnectToDB(self):
        if self.databaseConnectionParams is not None:
            try:
                self.dbConnection = psycopg2.connect(**self.databaseConnectionParams)
                # self.iface.messageBar().pushMessage('Tietokantaan yhdistäminen onnistui', Qgis.Info, duration=20)
            except psycopg2.Error as e:
                return False
        else:
            return False

        return True

    
    def monitorCachedLayerChanges(self):
        self.plans = None
        self.planLevelList = None
        self.themes = None

        layersPlans = QgsProject.instance().mapLayersByName("Yleiskaavan ulkorajaus (yleiskaava)")
        layersPlanLevelList = QgsProject.instance().mapLayersByName("kaavan_taso")
        layersThemes = QgsProject.instance().mapLayersByName("teemat")

        if len(layersPlans) == 1:
            if self.layerPlans is not None:
                try:
                    self.layerPlans.editingStopped.disconnect(self.handleLayerPlansChanges)
                except TypeError:
                    pass
                except RuntimeError:
                    pass
            self.layerPlans = layersPlans[0]
            self.layerPlans.editingStopped.connect(self.handleLayerPlansChanges)

        if len(layersPlanLevelList) == 1:
            if self.layerPlanLevelList is not None:
                try:
                    self.layerPlanLevelList.editingStopped.disconnect(self.handleLayerPlanLevelListChanges)
                except TypeError:
                    pass
                except RuntimeError:
                    pass
            self.layerPlanLevelList = layersPlanLevelList[0]
            self.layerPlanLevelList.editingStopped.connect(self.handleLayerPlanLevelListChanges)

        if len(layersThemes) == 1:
            if self.layerThemes is not None:
                try:
                    self.layerThemes.editingStopped.disconnect(self.handleLayerThemesChanges)
                except TypeError:
                    pass
                except RuntimeError:
                    pass
            self.layerThemes = layersThemes[0]
            self.layerThemes.editingStopped.connect(self.handleLayerThemesChanges)


    def handleLayerPlansChanges(self):
        QgsMessageLog.logMessage("handleLayerPlansChanges", 'Yleiskaava-työkalu', Qgis.Info)
        self.getSpatialPlans()

    def handleLayerPlanLevelListChanges(self):
        QgsMessageLog.logMessage("handleLayerPlanLevelListChanges", 'Yleiskaava-työkalu', Qgis.Info)
        self.getYleiskaavaPlanLevelList()

    def handleLayerThemesChanges(self):
        QgsMessageLog.logMessage("handleLayerThemesChanges", 'Yleiskaava-työkalu', Qgis.Info)
        self.getThemes()


    def createTargetFeature(self, targetSchemaTableName, targetLayerFeature, targetCRS, shouldRetry=True):
        success = True
        
        # QgsMessageLog.logMessage("createTargetFeature - targetCRS: " + targetCRS.authid(), 'Yleiskaava-työkalu', Qgis.Info)

        geom = targetLayerFeature.geometry()
        
        try:
            schema, table_name = targetSchemaTableName.split('.')

            with self.dbConnection.cursor(cursor_factory = psycopg2.extras.DictCursor) as cursor:
                query = ""
                attrTuple = None

                if not geom.isNull():
                    query = "INSERT INTO {} (id, geom".format(targetSchemaTableName)
                    attrTuple = (targetLayerFeature["id"], )
                else:
                    query = "INSERT INTO {} (id".format(targetSchemaTableName)
                    attrTuple = (targetLayerFeature["id"], )

                for field in targetLayerFeature.fields().toList():
                    if field.name() != "id":
                        value = targetLayerFeature[field.name()]

                        fieldTypeName = self.yleiskaavaUtils.getStringTypeForFeatureField(field)
                        if value is not None:
                            if (fieldTypeName == "Date" or fieldTypeName == "DateTime") and not QVariant(value).isNull():
                                value = QDateTime(QVariant(value).value()).toString("yyyy-MM-dd")

                        attrTuple += (value, )

                        query += ", {}".format(field.name())

                if not geom.isNull():
                    if geom.isMultipart():
                        query += ") VALUES (%s, ST_SetSRID(ST_Force3D(ST_GeomFromText('{}')), {})".format(geom.asWkt(), targetCRS.authid().split(':')[1])
                    else:
                        query += ") VALUES (%s, ST_Collect(ARRAY[ ST_SetSRID(ST_Force3D(ST_GeomFromText('{}')), {}) ])".format(geom.asWkt(), targetCRS.authid().split(':')[1])
                else:
                    query += ") VALUES (%s"

                for field in targetLayerFeature.fields().toList():
                     if field.name() != "id":
                        query += ", %s"
                query += ")"
                
                # QgsMessageLog.logMessage("createTargetFeature - query: " + query, 'Yleiskaava-työkalu', Qgis.Info)

                cursor.execute(query, attrTuple)
                self.dbConnection.commit()
        except psycopg2.Error as e:
            if shouldRetry:
                success = self.reconnectToDB()
                if success:
                    return self.createTargetFeature(targetSchemaTableName, targetLayerFeature, targetCRS, shouldRetry = False)

        return success