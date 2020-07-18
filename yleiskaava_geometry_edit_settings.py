
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt

from qgis.core import (
    Qgis, QgsProject, QgsFeature,
    QgsMessageLog, QgsMapLayer,
    QgsVectorLayer, QgsGeometry,
    QgsWkbTypes)

import os.path


class GeometryEditSettings:

    def __init__(self, iface, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = os.path.dirname(__file__)

        self.dockWidgetGeometryEditSettings = uic.loadUi(os.path.join(self.plugin_dir, 'yleiskaava_dockwidget_geometry_edit_settings.ui'))

        self.areaFeatureLayer = None
        self.suplementaryAreaFeatureLayer = None
        self.lineFeatureLayer = None


    def setup(self):
        # TODO selvitä pitääkö splitParts käsitellä eri tavalla kuin splitFeatures
        self.dockWidgetGeometryEditSettings.checkBoxKeepFeatureRelations.stateChanged.connect(self.handleCheckBoxKeepFeatureRelationsStateChanged)
        self.dockWidgetGeometryEditSettings.checkBoxPreventFeaturesWithTinyGeometries.stateChanged.connect(self.handleCheckBoxPreventFeaturesWithTinyGeometriesStateChanged)

        self.areaFeatureLayer = QgsProject.instance().mapLayersByName("Aluevaraukset")[0]
        self.suplementaryAreaFeatureLayer = QgsProject.instance().mapLayersByName("Täydentävät aluekohteet (osa-alueet)")[0]
        self.lineFeatureLayer = QgsProject.instance().mapLayersByName("Viivamaiset kaavakohteet")[0]

        self.setFollowGeometryChanges(True)
        

    def openDockWidgetGeometryEditSettings(self):
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockWidgetGeometryEditSettings)
        self.dockWidgetGeometryEditSettings.show()


    def handleCheckBoxKeepFeatureRelationsStateChanged(self):
        if self.dockWidgetGeometryEditSettings.checkBoxKeepFeatureRelations.isChecked():
            self.setFollowGeometryChanges(True)
        else:
            self.setFollowGeometryChanges(False)


    def handleCheckBoxPreventFeaturesWithTinyGeometriesStateChanged(self):
        if self.dockWidgetGeometryEditSettings.checkBoxPreventFeaturesWithTinyGeometries.isChecked():
            self.dockWidgetGeometryEditSettings.spinBoxPreventFeaturesWithTinyGeometries.setEnabled(True)
        else:
            self.dockWidgetGeometryEditSettings.spinBoxPreventFeaturesWithTinyGeometries.setEnabled(False)

    
    def setFollowGeometryChanges(self, shouldFollow):
        if shouldFollow:
            self.areaFeatureLayer.geometryChanged.connect(self.areaFeatureGeometryChanged)
            self.suplementaryAreaFeatureLayer.geometryChanged.connect(self.suplementaryAreaFeatureGeometryChanged)
            self.lineFeatureLayer.geometryChanged.connect(self.lineFeatureGeometryChanged)
        else:
            self.areaFeatureLayer.geometryChanged.disconnect(self.areaFeatureGeometryChanged)
            self.suplementaryAreaFeatureLayer.geometryChanged.disconnect(self.suplementaryAreaFeatureGeometryChanged)
            self.lineFeatureLayer.geometryChanged.disconnect(self.lineFeatureGeometryChanged)


    def areaFeatureGeometryChanged(self, fid, geometry):
        QgsMessageLog.logMessage("areaFeatureGeometryChanged - fid: " + str(fid) + ", geometry.area(): " + str(geometry.area()), 'Yleiskaava-työkalu', Qgis.Info)


    def suplementaryAreaFeatureGeometryChanged(self, fid, geometry):
        QgsMessageLog.logMessage("suplementaryAreaFeatureGeometryChanged - fid: " + str(fid) + ", geometry.area(): " + str(geometry.area()), 'Yleiskaava-työkalu', Qgis.Info)


    def lineFeatureGeometryChanged(self, fid, geometry):
        QgsMessageLog.logMessage("lineFeatureGeometryChanged - fid: " + str(fid) + ", geometry.length(): " + str(geometry.length()), 'Yleiskaava-työkalu', Qgis.Info)