
from qgis.core import (Qgis, QgsVectorLayer, QgsMessageLog)

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


    def getSourceDataAPIs(self):
        return self.sourceDataAPIs['wfs']


    def getSourceDataAPINames(self):
        names = []
        for api in self.sourceDataAPIs['wfs']:
            names.append(api['name'])
        return names


    def getSourceDataAPILayerNamesAndTitles(self, apiID):
        for api in self.sourceDataAPIs['wfs']:
            if api['id'] == apiID:
                names, titles = self.getWFSAPILayerNamesAndTitles(api['url'])
                return names, titles


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