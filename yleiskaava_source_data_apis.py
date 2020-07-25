
from qgis.core import (Qgis, QgsDataSourceUri, QgsVectorLayer, QgsMessageLog)

import os.path
import re
from urllib.request import urlopen
from xml.dom.minidom import parse
import xml.dom.minidom

class YleiskaavaSourceDataAPIs:

    def __init__(self, iface, yleiskaavaDatabase, yleiskaavaUtils):

        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = os.path.dirname(__file__)

        self.sourceDataAPIs = None
        self.sourceDataAPIs = self.yleiskaavaDatabase.getSourceDataAPIs()

        self.currentApiID = None
        self.currentLayerName = None
        self.currentLayer = None
        self.currentLayerInfo = None


    def getSourceDataAPIs(self):
        return self.sourceDataAPIs['sources']


    def getSourceDataAPINames(self):
        names = []
        for api in self.sourceDataAPIs['sources']:
            names.append(api['name'])
        return names


    def getSourceDataAPILayerNamesAndTitles(self, apiID):
        for api in self.sourceDataAPIs['sources']:
            if api['id'] == apiID:
                filteredNames = []
                filteredTitles = []
                names, titles = self.getWFSAPILayerNamesAndTitles(api['url_capabilities'])
                for index, name in enumerate(names):
                    for info in api["layers_info"]:
                        if info["ignore"] == False and info["layer_name"] == name:
                            filteredNames.append(name)
                            filteredTitles.append(info["user_friendly_title"])
                            break
                return filteredNames, filteredTitles


    def getWFSAPILayerNamesAndTitles(self, url):
        layerNames = []
        layerTitles = []

        with urlopen(url) as connection:
            # data = connection.read().decode('utf-8')
            dom = xml.dom.minidom.parse(connection)
            WFS_Capabilities = dom.documentElement
            featureTypeList = WFS_Capabilities.getElementsByTagName("FeatureTypeList")[0]
            featureTypes = featureTypeList.getElementsByTagName("FeatureType")
            for featureType in featureTypes:
                layerName = featureType.getElementsByTagName("Name")[0]
                layerTitle = featureType.getElementsByTagName("Title")[0]

                if layerName is not None:
                    layerNames.append(layerName.childNodes[0].data)
                    QgsMessageLog.logMessage("getWFSAPILayerNames - layerName: " + layerName.childNodes[0].data, 'Yleiskaava-työkalu', Qgis.Info)
                    layerTitles.append(layerTitle.childNodes[0].data)

        return layerNames, layerTitles 


    def getLayerAndLayerInfo(self, apiID, name):

        if self.currentApiID != apiID or self.currentLayerName != name:
            self.currentApiID = apiID
            self.currentLayerName = name
            self.currentLayer = self.createVectorLayer(self.currentApiID, self.currentLayerName)

        return self.currentLayer, self.currentLayerInfo


    def createVectorLayer(self, apiID, name):
        layer = None

        uri = QgsDataSourceUri()

        for api in self.sourceDataAPIs['sources']:
            if api['id'] == apiID:
                if api['service'] == 'WFS':
                    uri.setParam('service', 'WFS')
                    uri.setParam('version', api['version'])
                    uri.setParam('request', 'GetFeature')
                    uri.setParam('typename', name)
                    uri.setParam('srsName', api['srsName'])
                    uri.setParam('url', api['base_url'])

                    for layerInfo in api['layers_info']:
                        if layerInfo['layer_name'] == name:
                            self.currentLayerInfo = layerInfo
                            title = layerInfo['user_friendly_title']
                            layer = QgsVectorLayer(uri.uri(), title, 'WFS')
                            break

                    if layer is None:
                        layer = QgsVectorLayer(uri.uri(), name, 'WFS')
                    
                break
        
        if layer is not None and not layer.isValid():
            layer = None
            self.iface.messageBar().pushMessage('Lähdekarttason avaaminen ei onnistunut', Qgis.Critical)
        else:
            pass

        return layer


    def getLinkedDatabaseFeature(self, currentSourceLayerFeature):
        return None