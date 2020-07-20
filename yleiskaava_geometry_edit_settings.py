
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

        self.areaFeatureLayerEditBuffer = None
        self.suplementaryAreaFeatureLayerEditBuffer = None
        self.lineFeatureLayerEditBuffer = None

        self.addedLineFeatureIDs = []
        self.changedLineFeatureIDs = []


    def setup(self):
        # TODO selvitä pitääkö splitParts käsitellä eri tavalla kuin splitFeatures
        self.dockWidgetGeometryEditSettings.checkBoxKeepFeatureRelations.stateChanged.connect(self.handleCheckBoxKeepFeatureRelationsStateChanged)
        self.dockWidgetGeometryEditSettings.checkBoxPreventFeaturesWithTinyGeometries.stateChanged.connect(self.handleCheckBoxPreventFeaturesWithTinyGeometriesStateChanged)

        self.dockWidgetGeometryEditSettings.closed.connect(self.disconnectAll)


    def onClosePlugin(self):
        self.disconnectAll()


    def openDockWidgetGeometryEditSettings(self):
        # QgsMessageLog.logMessage("openDockWidgetGeometryEditSettings", 'Yleiskaava-työkalu', Qgis.Info)
        self.areaFeatureLayer = QgsProject.instance().mapLayersByName("Aluevaraukset")[0]
        self.suplementaryAreaFeatureLayer = QgsProject.instance().mapLayersByName("Täydentävät aluekohteet (osa-alueet)")[0]
        self.lineFeatureLayer = QgsProject.instance().mapLayersByName("Viivamaiset kaavakohteet")[0]

        self.followEdits()

        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockWidgetGeometryEditSettings)
        self.dockWidgetGeometryEditSettings.show()


    def followEdits(self):
        # NOTE edit bufferin geometrychanged-signaalin parametrina on alkup. featuren id
        # NOTE layerin featureAdded-signaalin kautta pääsee käsiksi uutteen featureen
        # NOTE kaikki näkymättömätkin kohteet tasolla jaetaan, jos ei ole filteröity pois

        # if self.areaFeatureLayer.isEditable():
        #    self.followAreaFeatureLayerEdits()
        # if self.suplementaryAreaFeatureLayer.isEditable():
        #     self.followSuplementaryAreaFeatureLayerEdits()
        # if self.lineFeatureLayer.isEditable():
        #     self.followLineFeatureLayerEdits()

        if self.areaFeatureLayer != None:
            self.areaFeatureLayer.editingStarted.connect(self.followAreaFeatureLayerEdits)
            self.areaFeatureLayer.editingStopped.connect(self.stopFollowingAreaFeatureLayerEdits)
    
        if self.suplementaryAreaFeatureLayer != None:
            self.suplementaryAreaFeatureLayer.editingStarted.connect(self.followSuplementaryAreaFeatureLayerEdits)
            self.suplementaryAreaFeatureLayer.editingStopped.connect(self.stopFollowingSuplementaryAreaFeatureLayerEdits)

        if self.lineFeatureLayer != None:
            # receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
            # QgsMessageLog.logMessage("followEdits - before receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
            # QgsMessageLog.logMessage("followEdits - connect(self.followLineFeatureLayerEdits)", 'Yleiskaava-työkalu', Qgis.Info)
            self.lineFeatureLayer.editingStarted.connect(self.followLineFeatureLayerEdits)
            # receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
            # QgsMessageLog.logMessage("followEdits - after receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
            self.lineFeatureLayer.editingStopped.connect(self.stopFollowingLineFeatureLayerEdits)


            self.lineFeatureLayer.editCommandEnded.connect(self.updateAttributesAfterEditCommandEnded)


    def disconnectAll(self):
        # QgsMessageLog.logMessage("disconnectAll", 'Yleiskaava-työkalu', Qgis.Info)
        if self.areaFeatureLayer != None:
            try:
                self.areaFeatureLayer.editingStarted.disconnect(self.followAreaFeatureLayerEdits)
                self.areaFeatureLayer.editingStopped.disconnect(self.stopFollowingAreaFeatureLayerEdits)
            except TypeError:
                pass
            except RuntimeError:
                pass

        if self.suplementaryAreaFeatureLayer != None:
            try:
                self.suplementaryAreaFeatureLayer.editingStarted.disconnect(self.followSuplementaryAreaFeatureLayerEdits)
                self.suplementaryAreaFeatureLayer.editingStopped.disconnect(self.stopFollowingSuplementaryAreaFeatureLayerEdits)
            except TypeError:
                pass
            except RuntimeError:
                pass

        if self.lineFeatureLayer != None:
            try:
                self.lineFeatureLayer.editingStarted.disconnect(self.followLineFeatureLayerEdits)
                # receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
                # QgsMessageLog.logMessage("disconnectAll - receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
                self.lineFeatureLayer.editingStopped.disconnect(self.stopFollowingLineFeatureLayerEdits)

                self.lineFeatureLayer.editCommandEnded.disconnect(self.updateAttributesAfterEditCommandEnded)
            except TypeError:
                pass
            except RuntimeError:
                pass


    def updateAttributesAfterEditCommandEnded(self):
        self.addRegulationAndThemeRelationsToLineFeature()


    def followAreaFeatureLayerEdits(self):
        self.areaFeatureLayerEditBuffer = self.areaFeatureLayer.editBuffer()
        #self.areaFeatureLayerEditBuffer.featureAdded.connect(self.areaFeatureGeometryChanged)
        self.areaFeatureLayerEditBuffer.geometryChanged.connect(self.areaFeatureGeometryChanged)
        try:
            self.areaFeatureLayer.featureAdded.disconnect(self.areaFeatureAdded)
        except TypeError:
            pass
        self.areaFeatureLayer.featureAdded.connect(self.areaFeatureAdded)

    def followSuplementaryAreaFeatureLayerEdits(self):
        self.suplementaryAreaFeatureLayerEditBuffer = self.suplementaryAreaFeatureLayer.editBuffer()
        #self.areaFeatureLayerEditBuffer.featureAdded.connect(self.areaFeatureGeometryChanged)
        self.suplementaryAreaFeatureLayerEditBuffer.geometryChanged.connect(self.suplementaryAreaFeatureGeometryChanged)
        try:
            self.suplementaryAreaFeatureLayer.featureAdded.disconnect(self.suplementaryAreaFeatureAdded)
        except TypeError:
            pass
        self.suplementaryAreaFeatureLayer.featureAdded.connect(self.suplementaryAreaFeatureAdded)

    def followLineFeatureLayerEdits(self):
        receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
        # QgsMessageLog.logMessage("followLineFeatureLayerEdits - receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
        #self.lineFeatures = self.lineFeatureLayer.getFeatures()
        # QgsMessageLog.logMessage("followLineFeatureLayerEdits - self.lineFeatureLayer.featureCount(): " + str(self.lineFeatureLayer.featureCount()), 'Yleiskaava-työkalu', Qgis.Info)
        self.lineFeatureLayerEditBuffer = self.lineFeatureLayer.editBuffer()
        #self.areaFeatureLayerEditBuffer.featureAdded.connect(self.areaFeatureGeometryChanged)
        self.lineFeatureLayerEditBuffer.geometryChanged.connect(self.lineFeatureGeometryChanged)
        try:
            self.lineFeatureLayer.featureAdded.disconnect(self.lineFeatureAdded)
        except TypeError:
            pass
        self.lineFeatureLayer.featureAdded.connect(self.lineFeatureAdded)


    def stopFollowingAreaFeatureLayerEdits(self):
        self.areaFeatureLayerEditBuffer = None
        # self.areaFeatureLayerEditBuffer.geometryChanged.disconnect(self.areaFeatureGeometryChanged)

    def stopFollowingSuplementaryAreaFeatureLayerEdits(self):
        self.suplementaryAreaFeatureLayerEditBuffer = None
        # self.suplementaryAreaFeatureLayerEditBuffer.geometryChanged.disconnect(self.suplementaryAreaFeatureGeometryChanged)

    def stopFollowingLineFeatureLayerEdits(self):
        self.lineFeatureLayerEditBuffer = None
        # self.lineFeatureLayerEditBuffer.geometryChanged.disconnect(self.lineFeatureGeometryChanged)


    def handleCheckBoxKeepFeatureRelationsStateChanged(self):
        pass


    def handleCheckBoxPreventFeaturesWithTinyGeometriesStateChanged(self):
        if self.dockWidgetGeometryEditSettings.checkBoxPreventFeaturesWithTinyGeometries.isChecked():
            self.dockWidgetGeometryEditSettings.spinBoxPreventFeaturesWithTinyGeometries.setEnabled(True)
        else:
            self.dockWidgetGeometryEditSettings.spinBoxPreventFeaturesWithTinyGeometries.setEnabled(False)


    def areaFeatureGeometryChanged(self, fid, geometry):
        QgsMessageLog.logMessage("areaFeatureGeometryChanged - fid: " + str(fid) + ", geometry.area(): " + str(geometry.area()), 'Yleiskaava-työkalu', Qgis.Info)
        # changedGeometries = self.areaFeatureLayerEditBuffer.changedGeometries()
        # for key in changedGeometries.keys():
        #     QgsMessageLog.logMessage("areaFeatureGeometryChanged - changedGeometries, key: " + str(key) + ", geometry.area(): " + str(geometry.area()), 'Yleiskaava-työkalu', Qgis.Info)


    def suplementaryAreaFeatureGeometryChanged(self, fid, geometry):
        QgsMessageLog.logMessage("suplementaryAreaFeatureGeometryChanged - fid: " + str(fid) + ", geometry.area(): " + str(geometry.area()), 'Yleiskaava-työkalu', Qgis.Info)
        # changedGeometries = self.suplementaryAreaFeatureLayerEditBuffer.changedGeometries()
        # for key in changedGeometries.keys():
        #     QgsMessageLog.logMessage("suplementaryAreaFeatureGeometryChanged - changedGeometries, key: " + str(key) + ", geometry.area(): " + str(geometry.area()), 'Yleiskaava-työkalu', Qgis.Info)


    def lineFeatureGeometryChanged(self, fid, geometry):
        QgsMessageLog.logMessage("lineFeatureGeometryChanged - fid: " + str(fid) + ", geometry.length(): " + str(geometry.length()), 'Yleiskaava-työkalu', Qgis.Info)
        # QgsMessageLog.logMessage("lineFeatureGeometryChanged - self.lineFeatureLayer.getFeature(fid).geometry().length(): " + str(self.lineFeatureLayer.getFeature(fid).geometry().length()), 'Yleiskaava-työkalu', Qgis.Info)
        QgsMessageLog.logMessage("lineFeatureGeometryChanged - self.lineFeatureLayer.featureCount(): " + str(self.lineFeatureLayer.featureCount()), 'Yleiskaava-työkalu', Qgis.Info)
        #lineFeatures = self.lineFeatureLayer.getFeatures()
        #QgsMessageLog.logMessage("lineFeatureGeometryChanged - len(lineFeatures): " + str(len(lineFeatures)), 'Yleiskaava-työkalu', Qgis.Info)
        # QgsMessageLog.logMessage("lineFeatureGeometryChanged - feature['kayttotarkoitus_lyhenne']: " + str(self.lineFeatureLayer.getFeature(fid)['kayttotarkoitus_lyhenne']), 'Yleiskaava-työkalu', Qgis.Info)
        # self.lineFeatureLayerEditBuffer = self.lineFeatureLayer.editBuffer()
        # changedGeometries = self.lineFeatureLayerEditBuffer.changedGeometries()
        # for key in changedGeometries.keys():
        #     QgsMessageLog.logMessage("lineFeatureGeometryChanged - changedGeometries, key: " + str(key) + ", geometry.length(): " + str(geometry.length()), 'Yleiskaava-työkalu', Qgis.Info)
        # addedFeatures = self.lineFeatureLayerEditBuffer.addedFeatures()
        # for key in addedFeatures.keys():
        #     QgsMessageLog.logMessage("lineFeatureGeometryChanged - addedFeatures, key: " + str(key) + ", feature.geometry.length(): " + str( addedFeatures[key].geometry().length()), 'Yleiskaava-työkalu', Qgis.Info)
        self.changedLineFeatureIDs.append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Viivamaisen kohteen geometriassa muutos, käyttötarkoitus: " + str(self.lineFeatureLayer.getFeature(fid)["kayttotarkoitus_lyhenne"]) + ", muuttuneita viivamaisia kohteita yhteensä: " + str(len(self.changedLineFeatureIDs)))

        # if len(self.addedLineFeatureIDs) == 1:
        #     self.addRegulationAndThemeRelationsToLineFeature()
        # elif len(self.addedLineFeatureIDs) > 1:
        #     self.iface.messageBar().pushMessage('Uusia viivamaisia kohteita on useita, joten uuden kohteen kaavamääräystä ja teemaa ei aseteta', Qgis.Warning)


    def areaFeatureAdded(self, fid):
        QgsMessageLog.logMessage("areaFeatureAdded - fid: " + str(fid), 'Yleiskaava-työkalu', Qgis.Info)
        QgsMessageLog.logMessage("areaFeatureAdded - self.areaFeatureLayer.featureCount(): " + str(self.areaFeatureLayer.featureCount()), 'Yleiskaava-työkalu', Qgis.Info)

    def suplementaryAreaFeatureAdded(self, fid):
        QgsMessageLog.logMessage("suplementaryAreaFeatureAdded - fid: " + str(fid), 'Yleiskaava-työkalu', Qgis.Info)
        QgsMessageLog.logMessage("suplementaryAreaFeatureAdded - self.suplementaryAreaFeatureLayer.featureCount(): " + str(self.suplementaryAreaFeatureLayer.featureCount()), 'Yleiskaava-työkalu', Qgis.Info)

    def lineFeatureAdded(self, fid):
        QgsMessageLog.logMessage("lineFeatureAdded - fid: " + str(fid), 'Yleiskaava-työkalu', Qgis.Info)
        QgsMessageLog.logMessage("lineFeatureAdded - self.lineFeatureLayer.featureCount(): " + str(self.lineFeatureLayer.featureCount()), 'Yleiskaava-työkalu', Qgis.Info)
        #self.addedFeatureIDs.append(fid)
        self.addedLineFeatureIDs.append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Uusi viivamainen kohde, uusia yhteensä: " + str(len(self.addedLineFeatureIDs)))

        # if len(self.changedLineFeatureIDs) == 1:
        #     self.addRegulationAndThemeRelationsToLineFeature()
        # elif len(self.changedLineFeatureIDs) > 1:
        #     self.iface.messageBar().pushMessage('Geometrialtaan muuttuneita viivamaisia kohteita on useita, joten uuden viivamaisen kohteen kaavamääräystä ja teemaa ei aseteta', Qgis.Warning)


    def addRegulationAndThemeRelationsToLineFeature(self):
        # TODO ota undo huomioon

        self.lineFeatureLayer.commitChanges()

        if len(self.changedLineFeatureIDs) == len(self.addedLineFeatureIDs):
            for index, sourceLineFeatureID in enumerate(self.changedLineFeatureIDs):

                sourceFeatureID = self.changedLineFeatureIDs[index]
                targetFeatureID = self.addedLineFeatureIDs[index]
                sourceFeatureUUID = self.lineFeatureLayer.getFeature(sourceFeatureID)["id"]
                targetFeatureUUID = self.lineFeatureLayer.getFeature(targetFeatureID)["id"]
                
                QgsMessageLog.logMessage("addRegulationAndThemeRelationsToLineFeature - sourceFeatureUUID: " + str(sourceFeatureUUID) + ", targetFeatureUUID: " + str(targetFeatureUUID), 'Yleiskaava-työkalu', Qgis.Info)

                #self.lineFeatureLayer.beginEditCommand("Lisätään kaavamääräys")

                self.yleiskaavaDatabase.addRegulationRelationsToLayer(sourceFeatureUUID, targetFeatureUUID, "viiva")
                self.yleiskaavaDatabase.addThemeRelationsToLayer(sourceFeatureUUID, targetFeatureUUID, "viiva")

            #self.lineFeatureLayer.endEditCommand()

                # self.lineFeatureLayer.commitChanges()

            self.changedLineFeatureIDs = []
            self.addedLineFeatureIDs = []

            # self.dockWidgetGeometryEditSettings.plainTextEditMessages.clear()
        else:
            self.iface.messageBar().pushMessage('Uusien ja jaettujen kohteiden lukumäärät eivät ole samoja. Uuden viivamaisen kohteen kaavamääräystä ja teemaa ei aseteta', Qgis.Critical)