from PyQt5 import uic
from PyQt5.QtCore import QSettings
from qgis.core import (Qgis, QgsDataSourceUri, QgsVectorLayer, QgsMessageLog)
from qgis.gui import QgsFileWidget

import os.path
#import psycopg2
from configparser import ConfigParser

class YleiskaavaDatabase:

    def __init__(self, iface):

        self.iface = iface

        self.plugin_dir = os.path.dirname(__file__)

        self.settingsDialog = uic.loadUi(os.path.join(self.plugin_dir, 'db_settings.ui'))

        self.connParams = None

        self.yleiskaava_target_tables = [
            {"name": "yk_yleiskaava.yleiskaava", "geomFieldName": "kaavan_ulkorajaus", "showInCopySourceToTargetUI": False},
            {"name": "yk_yleiskaava.kaavaobjekti_alue", "geomFieldName": "geom", "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.kaavaobjekti_alue_taydentava", "geomFieldName": "geom", "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.kaavaobjekti_viiva", "geomFieldName": "geom", "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.kaavaobjekti_piste", "geomFieldName": "geom", "showInCopySourceToTargetUI": True},
            {"name": "yk_yleiskaava.yleismaarays", "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_yleiskaava.kaavamaarays", "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_kuvaustekniikka.teema", "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_prosessi.lahtoaineisto", "geomFieldName": None, "showInCopySourceToTargetUI": False},
            {"name": "yk_prosessi.dokumentti", "geomFieldName": None, "showInCopySourceToTargetUI": False},
        ]

    def getTargetSchemaTableNamesShownInCopySourceToTargetUI(self):
        names = []
        for item in self.yleiskaava_target_tables:
            if item['showInCopySourceToTargetUI'] == True:
                names.append(item['name'])
        return names

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