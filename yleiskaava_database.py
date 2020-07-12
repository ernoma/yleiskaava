from PyQt5 import uic
from PyQt5.QtCore import QSettings
from qgis.core import (Qgis, QgsDataSourceUri, QgsVectorLayer, QgsWkbTypes, QgsMessageLog)
from qgis.gui import QgsFileWidget

import os.path
#import psycopg2
from configparser import ConfigParser
import uuid

class YleiskaavaDatabase:

    def __init__(self, iface):

        self.iface = iface

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


    def getUserFriendlyTargetSchemaTableNames(self):
        return [item["userFriendlyName"] for item in self.yleiskaava_target_tables]

        
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


    def getSpecificRegulations(self, upperCase):
        uri = self.createDbURI("yk_yleiskaava", "kaavamaarays", None)
        targetLayer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")

        features = targetLayer.getFeatures()
        regulationList = []
        for index, feature in enumerate(features):
            kaavamaarays_otsikko = feature['kaavamaarays_otsikko']
            maaraysteksti = feature['maaraysteksti']

            if upperCase:
                kaavamaarays_otsikko = kaavamaarays_otsikko.toupper()
                maaraysteksti = maaraysteksti.toupper()

            regulationList.append({
                "id": feature['id'],
                "kaavamaarays_otsikko": kaavamaarays_otsikko,
                "maaraysteksti": maaraysteksti})

        return regulationList


    def createFeatureRegulationRelation(self, targetSchemaTableName, targetFeatureID, regulationName):
        schema, table_name = targetSchemaTableName.split('.')

        regulationID = self.findRegulationID(regulationName)

        self.createFeatureRegulationRelationWithRegulationID(targetSchemaTableName, targetFeatureID, regulationID)


    def createFeatureRegulationRelationWithRegulationID(self, targetSchemaTableName, targetFeatureID, regulationID):
        uri = self.createDbURI("yk_yleiskaava", "kaavaobjekti_kaavamaarays_yhteys", None)
        relationLayer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")

        relationLayerFeature = QgsFeature()
        relationLayerFeature.setAttribute("id", str(uuid.uuid4()))
        relationLayerFeature.setAttribute("id_" + table_name, targetFeatureID)
        relationLayerFeature.setAttribute("id_kaavamaarays", regulationID)

        relationLayer.startEditing()
        provider = relationLayer.dataProvider()
        provider.addFeature(relationLayerFeature)
        relationLayer.commitChanges()


    def findRegulationID(self, regulationName):
        regulationList = self.getSpecificRegulations(upperCase=True)

        regulationID = None
        for regulation in regulationList:
            if regulation["kaavamaarays_otsikko"] == regulationName.toupper():
                regulationID = regulation["id"]
                break

        return regulationID


    def createSpecificRegulationAndFeatureRegulationRelation(self, targetSchemaTableName, targetFeatureID, regulationName):
        uri = self.createDbURI("yk_yleiskaava", "kaavamaarays", None)
        regulationLayer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")

        regulationID = str(uuid.uuid4())

        regulationFeature = QgsFeature()
        regulationFeature.setAttribute("id", regulationID)
        regulationFeature.setAttribute("kaavamaarays_otsikko", regulationName)
        regulationLayer.startEditing()
        provider = regulationLayer.dataProvider()
        provider.addFeature(relationLayerFeature)
        regulationLayer.commitChanges()

        self.createFeatureRegulationRelationWithRegulationID(targetSchemaTableName, targetFeatureID, regulationID)


    def getCodeListValuesForSchemaTable(self, id_name):
        if id_name == 'id_kansallinen_prosessin_vaihe':
            schema, table_name = "yk_koodiluettelot.kansallinen_prosessin_vaihe".split('.')
        elif id_name == 'id_laillinen_sitovuus':
            schema, table_name = "yk_koodiluettelot.laillinen_sitovuus".split('.')
        elif id_name == 'id_prosessin_vaihe':
            schema, table_name = "yk_koodiluettelot.prosessin_vaihe".split('.')
        elif id_name == 'id_kaavoitusprosessin_tila':
            schema, table_name = "yk_koodiluettelot.kaavoitusprosessin_tila".split('.')
        uri = self.createDbURI(schema, table_name, None)
        targetLayer = QgsVectorLayer(uri.uri(False), "temp layer", "postgres")
        features = targetLayer.getFeatures()
        values = None
        if table_name == "kansallinen_prosessin_vaihe" or table_name == "prosessin_vaihe" or table_name == "kaavoitusprosessin_tila" or table_name == "laillinen_sitovuus":
            values = [feature['koodi'] for feature in features]

        return values


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

