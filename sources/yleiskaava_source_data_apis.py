
from qgis.core import (Qgis, QgsDataSourceUri,
    QgsVectorLayer, QgsMessageLog,
    QgsWkbTypes, QgsTask)

import os.path
import re
from urllib.request import urlopen
from xml.dom.minidom import parse
import xml.dom.minidom
import json
import socket


class YleiskaavaSourceDataAPIs:

    SOURCE_DATA_API_SETTINGS_FILE_PATH = 'lahderajapinnat.json'


    def __init__(self, iface, plugin_dir, yleiskaavaDatabase, yleiskaavaUtils):

        self.iface = iface

        self.plugin_dir = plugin_dir

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.sourceDataAPIs = self.readSourceDataAPIs()

        self.currentAPIID = None
        self.currentAPIInfo = None
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
                    # QgsMessageLog.logMessage("getWFSAPILayerNames - layerName: " + layerName.childNodes[0].data, 'Yleiskaava-työkalu', Qgis.Info)
                    layerTitles.append(layerTitle.childNodes[0].data)

        return layerNames, layerTitles 


    def getLayerAndLayerInfo(self, apiID, name):

        # if self.currentAPIID != apiID or self.currentLayerName != name:
        self.currentAPIID = apiID
        self.currentLayerName = name
        self.currentLayer = self.createVectorLayer(self.currentAPIID, self.currentLayerName)

        return self.currentLayer, self.currentLayerInfo


    def createVectorLayer(self, apiID, name):
        layer = None

        uri = QgsDataSourceUri()

        for api in self.sourceDataAPIs['sources']:
            if api['id'] == apiID:
                self.currentAPIInfo = api
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
            self.iface.messageBar().pushMessage('Lähdekarttason avaaminen ei onnistunut', Qgis.Critical, duration=0)
        else:
            pass

        return layer


    def getLinkedDatabaseFeatureIDAndSourceDataFeature(self, spatialFeatureLayer, sourceLayerFeatureInfo):
        linkedFeatureID = None
        linkedSourceDataFeature = None
        if self.currentAPIInfo != None:
            # features = self.yleiskaavaDatabase.getSourceDataFeatures(self.currentAPIInfo["linkitys_tyyppi"])
            linkedFeatureID, linkedSourceDataFeature = self.yleiskaavaDatabase.getLinkedFeatureIDAndSourceDataFeature(spatialFeatureLayer, sourceLayerFeatureInfo, self.currentAPIInfo["linkitys_tyyppi"])
        return linkedFeatureID, linkedSourceDataFeature


    def readSourceDataAPIs(self):
        filePath = os.path.join(self.plugin_dir, YleiskaavaSourceDataAPIs.SOURCE_DATA_API_SETTINGS_FILE_PATH)

        if not os.path.exists(filePath):
            self.iface.messageBar().pushMessage('Virhe', 'Lähderajapintatiedostoa ei voitu lukea',\
                Qgis.Critical, duration=0)
            return

        apis = None

        with open(filePath) as f:
            apis = json.load(f)

        return apis


    def createMemoryLayer(self, layer, layerInfo, features):
        memoryLayer = None

        geomType = layer.geometryType()

        if geomType == QgsWkbTypes.PointGeometry:
            memoryLayer = QgsVectorLayer("MultiPoint?crs=" + layer.sourceCrs().authid(), layerInfo['user_friendly_title'], "memory")
        elif geomType == QgsWkbTypes.LineGeometry:
            memoryLayer = QgsVectorLayer("MultiLineString?crs=" + layer.sourceCrs().authid(), layerInfo['user_friendly_title'], "memory")
        elif geomType == QgsWkbTypes.PolygonGeometry:
            memoryLayer = QgsVectorLayer("MultiPolygon?crs=" + layer.sourceCrs().authid(), layerInfo['user_friendly_title'], "memory")
        
        if memoryLayer is not None:
            fields = layer.dataProvider().fields().toList()
            memoryLayer.startEditing()
            for field in fields:
                memoryLayer.addAttribute(field)
            memoryLayer.commitChanges()
            # memoryLayer.startEditing()
            if features is not None:
                memoryLayer.dataProvider().addFeatures(features)
            # memoryLayer.commitChanges()

        return memoryLayer


class FeatureRequestTask(QgsTask):
    def __init__(self, layer, featureRequest):
        super().__init__('Haetaan kohteita', QgsTask.CanCancel)
        self.exception = None
        self.layer = layer
        self.featureRequest = featureRequest
        self.features = None


    def run(self):
        if self.exception:
            return False

        self.features = self.layer.getFeatures(self.featureRequest)

        return True


    def finished(self, success):
        if not success:
            QgsMessageLog.logMessage('FeatureRequestTask - poikkeus: ' + str(self.exception), 'Yleiskaava-työkalu', Qgis.Critical)
            self.iface.messageBar().pushMessage('Virhe: FeatureRequestTask - poikkeus: ' + str(self.exception), Qgis.Critical, duration=0)
            # raise self.exception
            self.cancel()


    def cancel(self):
        QgsMessageLog.logMessage(
            'FeatureRequestTask "{name}" keskeytettiin'.format(
                name=self.description()),
            'Yleiskaava-työkalu', Qgis.Info)
        super().cancel()
    