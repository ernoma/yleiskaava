
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QTextCursor


from qgis.core import (
    Qgis, QgsProject,
    QgsMessageLog)

import os.path
from functools import partial

from .yleiskaava_database import YleiskaavaDatabase


class GeometryEditSettings:

    def __init__(self, iface, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = os.path.dirname(__file__)

        self.dockWidgetGeometryEditSettings = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dockwidget_geometry_edit_settings.ui'))

        self.activeLayer = None

        self.featureLayer = {
            'alue': None,
            'alue_taydentava': None,
            'viiva': None
        }

        self.featureLayerEditBuffer = {
            'alue': None,
            'alue_taydentava': None,
            'viiva': None
        }

        self.addedFeatureIDs = {
            'alue': [],
            'alue_taydentava': [],
            'viiva': []
        }

        self.changedFeatureIDs = {
            'alue': [],
            'alue_taydentava': [],
            'viiva': []
        }


    def setup(self):
        # self.dockWidgetGeometryEditSettings.checkBoxKeepFeatureRelations.stateChanged.connect(self.handleCheckBoxKeepFeatureRelationsStateChanged)
        self.dockWidgetGeometryEditSettings.checkBoxPreventFeaturesWithTinyGeometries.stateChanged.connect(self.handleCheckBoxPreventFeaturesWithTinyGeometriesStateChanged)

        self.dockWidgetGeometryEditSettings.closed.connect(self.disconnectAll)


    def onClosePlugin(self):
        self.disconnectAll()


    def openDockWidgetGeometryEditSettings(self):
        # QgsMessageLog.logMessage("openDockWidgetGeometryEditSettings", 'Yleiskaava-työkalu', Qgis.Info)
        self.featureLayer['alue'] = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE)[0]
        self.featureLayer['alue_taydentava'] = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA)[0]
        self.featureLayer['viiva'] = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_PISTE)[0]

        self.followEdits()

        self.updateEditableFeatureClassesCountUIInfo()

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

        self.iface.currentLayerChanged.connect(self.updateEditableFeatureClassesCountUIInfo)

        if self.featureLayer['alue'] != None:
            self.featureLayer['alue'].subsetStringChanged.connect(self.updateEditableFeatureClassesCountUIInfo)

            self.featureLayer['alue'].editingStarted.connect(partial(self.followFeatureLayerEdits, 'alue'))
            self.featureLayer['alue'].editingStopped.connect(partial(self.stopFollowingFeatureLayerEdits, 'alue'))
            self.featureLayer['alue'].editCommandEnded.connect(partial(self.updateFeatureAttributesAfterEditCommandEnded, 'alue'))
    
        if self.featureLayer['alue_taydentava'] != None:
            self.featureLayer['alue_taydentava'].subsetStringChanged.connect(self.updateEditableFeatureClassesCountUIInfo)

            self.featureLayer['alue_taydentava'].editingStarted.connect(partial(self.followFeatureLayerEdits, 'alue_taydentava'))
            self.featureLayer['alue_taydentava'].editingStopped.connect(partial(self.stopFollowingFeatureLayerEdits, 'alue_taydentava'))
            self.featureLayer['alue_taydentava'].editCommandEnded.connect(partial(self.updateFeatureAttributesAfterEditCommandEnded, 'alue_taydentava'))

        if self.featureLayer['viiva'] != None:
            self.featureLayer['viiva'].subsetStringChanged.connect(self.updateEditableFeatureClassesCountUIInfo)

            # receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
            # QgsMessageLog.logMessage("followEdits - before receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
            # QgsMessageLog.logMessage("followEdits - connect(self.followLineFeatureLayerEdits)", 'Yleiskaava-työkalu', Qgis.Info)
            self.featureLayer['viiva'].editingStarted.connect(partial(self.followFeatureLayerEdits, 'viiva'))
            # receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
            # QgsMessageLog.logMessage("followEdits - after receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
            self.featureLayer['viiva'].editingStopped.connect(partial(self.stopFollowingFeatureLayerEdits, 'viiva'))
            self.featureLayer['viiva'].editCommandEnded.connect(partial(self.updateFeatureAttributesAfterEditCommandEnded, 'viiva'))


    def disconnectAll(self):
        # QgsMessageLog.logMessage("disconnectAll", 'Yleiskaava-työkalu', Qgis.Info)

        try:
            self.iface.currentLayerChanged.disconnect(self.updateEditableFeatureClassesCountUIInfo)
        except TypeError:
            pass
        except RuntimeError:
            pass

        if self.featureLayer['alue'] != None:
            try:
                self.featureLayer['alue'].subsetStringChanged.disconnect(self.updateEditableFeatureClassesCountUIInfo)

                self.featureLayer['alue'].editingStarted.disconnect(partial(self.followFeatureLayerEdits, 'alue'))
                # receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
                # QgsMessageLog.logMessage("disconnectAll - receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
                self.featureLayer['alue'].editingStopped.disconnect(partial(self.stopFollowingFeatureLayerEdits, 'alue'))
                self.featureLayer['alue'].editCommandEnded.disconnect(partial(self.updateFeatureAttributesAfterEditCommandEnded, 'alue'))
            except TypeError:
                pass
            except RuntimeError:
                pass

        if self.featureLayer['alue_taydentava'] != None:
            try:
                self.featureLayer['alue_taydentava'].subsetStringChanged.disconnect(self.updateEditableFeatureClassesCountUIInfo)
                
                self.featureLayer['alue_taydentava'].editingStarted.disconnect(partial(self.followFeatureLayerEdits, 'alue_taydentava'))
                # receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
                # QgsMessageLog.logMessage("disconnectAll - receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
                self.featureLayer['alue_taydentava'].editingStopped.disconnect(partial(self.stopFollowingFeatureLayerEdits, 'alue_taydentava'))
                self.featureLayer['alue_taydentava'].editCommandEnded.disconnect(partial(self.updateFeatureAttributesAfterEditCommandEnded, 'alue_taydentava'))
            except TypeError:
                pass
            except RuntimeError:
                pass

        if self.featureLayer['viiva'] != None:
            try:
                self.featureLayer['viiva'].subsetStringChanged.disconnect(self.updateEditableFeatureClassesCountUIInfo)

                self.featureLayer['viiva'].editingStarted.disconnect(partial(self.followFeatureLayerEdits, 'viiva'))
                # receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
                # QgsMessageLog.logMessage("disconnectAll - receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
                self.featureLayer['viiva'].editingStopped.disconnect(partial(self.stopFollowingFeatureLayerEdits, 'viiva'))
                self.featureLayer['viiva'].editCommandEnded.disconnect(partial(self.updateFeatureAttributesAfterEditCommandEnded, 'viiva'))
            except TypeError:
                pass
            except RuntimeError:
                pass


    def updateEditableFeatureClassesCountUIInfo(self):
        self.activeLayer = self.iface.activeLayer()
        if self.activeLayer is None or (self.activeLayer.name() != YleiskaavaDatabase.KAAVAOBJEKTI_ALUE and self.activeLayer.name() != YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA and self.activeLayer.name() != YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA and self.activeLayer.name() != YleiskaavaDatabase.KAAVAOBJEKTI_PISTE):
            self.dockWidgetGeometryEditSettings.lineEditEditableFeatureClassesCount.setStyleSheet("background-color: rgb(255, 255, 255);")
            self.dockWidgetGeometryEditSettings.lineEditEditableFeatureClassesCount.setText('')
        elif self.activeLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_ALUE or self.activeLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA or self.activeLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA or self.activeLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_PISTE:
            featureClasses = {}
            for feature in self.activeLayer.getFeatures():
                featureClass = feature["kayttotarkoitus_lyhenne"]
                if featureClass not in featureClasses:
                    featureClasses[featureClass] = 1
                else:
                    featureClasses[featureClass] += 1
            if len(featureClasses) == 0:
                self.dockWidgetGeometryEditSettings.lineEditEditableFeatureClassesCount.setStyleSheet("background-color: rgb(255, 255, 255);")
                self.dockWidgetGeometryEditSettings.lineEditEditableFeatureClassesCount.setText('0')
            elif len(featureClasses) == 1:
                self.dockWidgetGeometryEditSettings.lineEditEditableFeatureClassesCount.setStyleSheet("background-color: rgb(52, 235, 210);")
                self.dockWidgetGeometryEditSettings.lineEditEditableFeatureClassesCount.setText('1')
            elif len(featureClasses) > 1:
                self.dockWidgetGeometryEditSettings.lineEditEditableFeatureClassesCount.setStyleSheet("background-color: rgb(235, 97, 52);")
                self.dockWidgetGeometryEditSettings.lineEditEditableFeatureClassesCount.setText(str(len(featureClasses)))

    def updateFeatureAttributesAfterEditCommandEnded(self, featureType):
        self.addRegulationAndThemeRelationsToFeature(featureType)


    def followFeatureLayerEdits(self, featureType):
        self.featureLayerEditBuffer[featureType] = self.featureLayer[featureType].editBuffer()
        #self.areaFeatureLayerEditBuffer.featureAdded.connect(self.areaFeatureGeometryChanged)
        if featureType == 'alue':
            self.featureLayerEditBuffer[featureType].geometryChanged.connect(self.areaFeatureGeometryChanged)
            try:
                self.featureLayer[featureType].featureAdded.disconnect(self.areaFeatureAdded)
            except TypeError:
                pass
            self.featureLayer[featureType].featureAdded.connect(self.areaFeatureAdded)
        elif featureType == 'alue_taydentava':
            self.featureLayerEditBuffer[featureType].geometryChanged.connect(self.suplementaryAreaFeatureGeometryChanged)
            try:
                self.featureLayer[featureType].featureAdded.disconnect(self.suplementaryAreaFeatureAdded)
            except TypeError:
                pass
            self.featureLayer[featureType].featureAdded.connect(self.suplementaryAreaFeatureAdded)
        elif featureType == 'viiva':
            self.featureLayerEditBuffer[featureType].geometryChanged.connect(self.lineFeatureGeometryChanged)
            try:
                self.featureLayer[featureType].featureAdded.disconnect(self.lineFeatureAdded)
            except TypeError:
                pass
            self.featureLayer[featureType].featureAdded.connect(self.lineFeatureAdded)


    def stopFollowingFeatureLayerEdits(self, featureType):
        self.featureLayerEditBuffer[featureType] = None
        # self.areaFeatureLayerEditBuffer.geometryChanged.disconnect(self.areaFeatureGeometryChanged)


    # def handleCheckBoxKeepFeatureRelationsStateChanged(self):
    #     self.shouldKeepFeatureRelations = self.dockWidgetGeometryEditSettings.checkBoxKeepFeatureRelations.isChecked()


    def handleCheckBoxPreventFeaturesWithTinyGeometriesStateChanged(self):
        if self.dockWidgetGeometryEditSettings.checkBoxPreventFeaturesWithTinyGeometries.isChecked():
            self.dockWidgetGeometryEditSettings.doubleSpinBoxPreventFeaturesWithTinyGeometries.setEnabled(True)
        else:
            self.dockWidgetGeometryEditSettings.doubleSpinBoxPreventFeaturesWithTinyGeometries.setEnabled(False)


    def areaFeatureGeometryChanged(self, fid, geometry):
        #QgsMessageLog.logMessage("areaFeatureGeometryChanged - fid: " + str(fid) + ", geometry.area(): " + str(geometry.area()), 'Yleiskaava-työkalu', Qgis.Info)
        # changedGeometries = self.areaFeatureLayerEditBuffer.changedGeometries()
        # for key in changedGeometries.keys():
        #     QgsMessageLog.logMessage("areaFeatureGeometryChanged - changedGeometries, key: " + str(key) + ", geometry.area(): " + str(geometry.area()), 'Yleiskaava-työkalu', Qgis.Info)
        self.changedFeatureIDs['alue'].append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Aluevarauskohteen geometriassa muutos, käyttötarkoitus: " + str(self.featureLayer['alue'].getFeature(fid)["kayttotarkoitus_lyhenne"]) + ", muuttuneita aluevarauskohteita yhteensä: " + str(len(self.changedFeatureIDs['alue'])))
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)


    def suplementaryAreaFeatureGeometryChanged(self, fid, geometry):
        #QgsMessageLog.logMessage("suplementaryAreaFeatureGeometryChanged - fid: " + str(fid) + ", geometry.area(): " + str(geometry.area()), 'Yleiskaava-työkalu', Qgis.Info)
        # changedGeometries = self.suplementaryAreaFeatureLayerEditBuffer.changedGeometries()
        # for key in changedGeometries.keys():
        #     QgsMessageLog.logMessage("suplementaryAreaFeatureGeometryChanged - changedGeometries, key: " + str(key) + ", geometry.area(): " + str(geometry.area()), 'Yleiskaava-työkalu', Qgis.Info)
        self.changedFeatureIDs['alue_taydentava'].append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Täydentävän aluekohteen geometriassa muutos, käyttötarkoitus: " + str(self.featureLayer['alue_taydentava'].getFeature(fid)["kayttotarkoitus_lyhenne"]) + ", muuttuneita täydentäviä aluekohteita yhteensä: " + str(len(self.changedFeatureIDs['alue_taydentava'])))
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)


    def lineFeatureGeometryChanged(self, fid, geometry):
        #QgsMessageLog.logMessage("lineFeatureGeometryChanged - fid: " + str(fid) + ", geometry.length(): " + str(geometry.length()), 'Yleiskaava-työkalu', Qgis.Info)
        # QgsMessageLog.logMessage("lineFeatureGeometryChanged - self.lineFeatureLayer.getFeature(fid).geometry().length(): " + str(self.lineFeatureLayer.getFeature(fid).geometry().length()), 'Yleiskaava-työkalu', Qgis.Info)
        #QgsMessageLog.logMessage("lineFeatureGeometryChanged - self.lineFeatureLayer.featureCount(): " + str(self.lineFeatureLayer.featureCount()), 'Yleiskaava-työkalu', Qgis.Info)
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
        self.changedFeatureIDs['viiva'].append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Viivamaisen kohteen geometriassa muutos, käyttötarkoitus: " + str(self.featureLayer['viiva'].getFeature(fid)["kayttotarkoitus_lyhenne"]) + ", muuttuneita viivamaisia kohteita yhteensä: " + str(len(self.changedFeatureIDs['viiva'])))
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)

        # if len(self.addedLineFeatureIDs) == 1:
        #     self.addRegulationAndThemeRelationsToLineFeature()
        # elif len(self.addedLineFeatureIDs) > 1:
        #     self.iface.messageBar().pushMessage('Uusia viivamaisia kohteita on useita, joten uuden kohteen kaavamääräystä ja teemaa ei aseteta', Qgis.Warning)


    def areaFeatureAdded(self, fid):
        QgsMessageLog.logMessage("areaFeatureAdded - fid: " + str(fid), 'Yleiskaava-työkalu', Qgis.Info)
        QgsMessageLog.logMessage("areaFeatureAdded - self.areaFeatureLayer.featureCount(): " + str(self.featureLayer['alue'].featureCount()), 'Yleiskaava-työkalu', Qgis.Info)
        self.addedFeatureIDs['alue'].append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Uusi aluevarauskohde, uusia yhteensä: " + str(len(self.addedFeatureIDs['alue'])))
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)

    def suplementaryAreaFeatureAdded(self, fid):
        QgsMessageLog.logMessage("suplementaryAreaFeatureAdded - fid: " + str(fid), 'Yleiskaava-työkalu', Qgis.Info)
        QgsMessageLog.logMessage("suplementaryAreaFeatureAdded - self.suplementaryAreaFeatureLayer.featureCount(): " + str(self.featureLayer['alue_taydentava'].featureCount()), 'Yleiskaava-työkalu', Qgis.Info)
        self.addedFeatureIDs['alue_taydentava'].append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Uusi täydentävä aluekohde, uusia yhteensä: " + str(len(self.addedFeatureIDs['alue_taydentava'])))
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)

    def lineFeatureAdded(self, fid):
        QgsMessageLog.logMessage("lineFeatureAdded - fid: " + str(fid), 'Yleiskaava-työkalu', Qgis.Info)
        QgsMessageLog.logMessage("lineFeatureAdded - self.lineFeatureLayer.featureCount(): " + str(self.featureLayer['viiva'].featureCount()), 'Yleiskaava-työkalu', Qgis.Info)
        #self.addedFeatureIDs.append(fid)
        self.addedFeatureIDs['viiva'].append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Uusi viivamainen kohde, uusia yhteensä: " + str(len(self.addedFeatureIDs['viiva'])))
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)

        # if len(self.changedLineFeatureIDs) == 1:
        #     self.addRegulationAndThemeRelationsToLineFeature()
        # elif len(self.changedLineFeatureIDs) > 1:
        #     self.iface.messageBar().pushMessage('Geometrialtaan muuttuneita viivamaisia kohteita on useita, joten uuden viivamaisen kohteen kaavamääräystä ja teemaa ei aseteta', Qgis.Warning)



    def addRegulationAndThemeRelationsToFeature(self, featureType):

        self.featureLayer[featureType].commitChanges()

        if len(self.changedFeatureIDs[featureType]) == len(self.addedFeatureIDs[featureType]):
            for index, sourceFeatureID in enumerate(self.changedFeatureIDs[featureType]):

                sourceFeatureID = self.changedFeatureIDs[featureType][index]
                targetFeatureID = self.addedFeatureIDs[featureType][index]
                sourceFeature = self.featureLayer[featureType].getFeature(sourceFeatureID)
                targetFeature = self.featureLayer[featureType].getFeature(targetFeatureID)
                sourceFeatureUUID = sourceFeature["id"]
                targetFeatureUUID = targetFeature["id"]
                
                QgsMessageLog.logMessage("addRegulationAndThemeRelationsToFeature - sourceFeatureUUID: " + str(sourceFeatureUUID) + ", targetFeatureUUID: " + str(targetFeatureUUID), 'Yleiskaava-työkalu', Qgis.Info)

                #self.lineFeatureLayer.beginEditCommand("Lisätään kaavamääräys")

                if not targetFeature.hasGeometry():
                    if self.dockWidgetGeometryEditSettings.checkBoxPreventNULLGeometries.isChecked():
                        # remove feature
                        self.yleiskaavaDatabase.deleteSpatialFeature(targetFeatureUUID, featureType)
                        self.iface.messageBar().pushMessage('Kohde, jolla ei ollut geometriaa, poistettiin', Qgis.Warning)
                        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Kohde, jolla ei ollut geometriaa, poistettiin")
                        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)
                else:
                    # ratio = targetFeature.geometry().length() / (sourceFeature.geometry().length() + targetFeature.geometry().length()) * 100
                    # QgsMessageLog.logMessage("addRegulationAndThemeRelationsToLineFeature - ratio: " + str(ratio), 'Yleiskaava-työkalu', Qgis.Info)

                    if self.dockWidgetGeometryEditSettings.checkBoxKeepFeatureRelations.isChecked():
                        self.yleiskaavaDatabase.addRegulationRelationsToLayer(sourceFeatureUUID, targetFeatureUUID, featureType)
                        self.yleiskaavaDatabase.addThemeRelationsToLayer(sourceFeatureUUID, targetFeatureUUID, featureType)
                        self.iface.messageBar().pushMessage('Kaavamääräykset ja teemat lisätty jaetulle kohteelle', Qgis.Info, 5)
                        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Kaavamääräykset ja teemat lisätty jaetulle kohteelle")
                        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)

                    if self.dockWidgetGeometryEditSettings.checkBoxPreventFeaturesWithTinyGeometries.isChecked():
                        if featureType == 'alue' or featureType == 'alue_taydentava':
                            if (targetFeature.geometry().area() / (targetFeature.geometry().area() + sourceFeature.geometry().area()) * 100) < self.dockWidgetGeometryEditSettings.doubleSpinBoxPreventFeaturesWithTinyGeometries.value():
                                # remove feature
                                self.yleiskaavaDatabase.deleteSpatialFeature(targetFeatureUUID, featureType)
                                ratio = targetFeature.geometry().area() / (targetFeature.geometry().area() + sourceFeature.geometry().area()) * 100
                                self.iface.messageBar().pushMessage('Kohteen pinta-ala verrattuna alkuperäiseen oli ' + str(round(ratio, 3)) + '%, joten se poistettiin', Qgis.Warning)
                                self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText('Kohteen pinta-ala verrattuna alkuperäiseen oli ' + str(round(ratio, 3)) + '%, joten se poistettiin')
                                self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)
                            elif (sourceFeature.geometry().area() / (targetFeature.geometry().area() + sourceFeature.geometry().area()) * 100) < self.dockWidgetGeometryEditSettings.doubleSpinBoxPreventFeaturesWithTinyGeometries.value():
                                # remove feature
                                self.yleiskaavaDatabase.deleteSpatialFeature(sourceFeatureUUID, featureType)
                                ratio = sourceFeature.geometry().area() / (targetFeature.geometry().area() + sourceFeature.geometry().area()) * 100
                                self.iface.messageBar().pushMessage('Kohteen pinta-ala verrattuna alkuperäiseen oli ' + str(round(ratio, 3)) + '%, joten se poistettiin', Qgis.Warning)
                                self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText('Kohteen pinta-ala verrattuna alkuperäiseen oli ' + str(round(ratio, 3)) + '%, joten se poistettiin')
                                self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)
                        elif featureType == 'viiva':
                            if (targetFeature.geometry().length() / (targetFeature.geometry().length() + sourceFeature.geometry().length()) * 100) < self.dockWidgetGeometryEditSettings.doubleSpinBoxPreventFeaturesWithTinyGeometries.value():
                                # remove feature
                                self.yleiskaavaDatabase.deleteSpatialFeature(targetFeatureUUID, featureType)
                                ratio = targetFeature.geometry().length() / (targetFeature.geometry().length() + sourceFeature.geometry().length()) * 100
                                self.iface.messageBar().pushMessage('Kohteen pituus verrattuna alkuperäiseen oli ' + str(round(ratio, 3)) + '%, joten se poistettiin', Qgis.Warning)
                                self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText('Kohteen pituus verrattuna alkuperäiseen oli ' + str(round(ratio, 3)) + '%, joten se poistettiin')
                                self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)
                            elif (sourceFeature.geometry().length() / (targetFeature.geometry().length() + sourceFeature.geometry().length()) * 100) < self.dockWidgetGeometryEditSettings.doubleSpinBoxPreventFeaturesWithTinyGeometries.value():
                                # remove feature
                                self.yleiskaavaDatabase.deleteSpatialFeature(sourceFeatureUUID, featureType)
                                ratio = sourceFeature.geometry().length() / (targetFeature.geometry().length() + sourceFeature.geometry().length()) * 100
                                self.iface.messageBar().pushMessage('Kohteen pituus verrattuna alkuperäiseen oli ' + str(round(ratio, 3)) + '%, joten se poistettiin', Qgis.Warning)
                                self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText('Kohteen pituus verrattuna alkuperäiseen oli ' + str(round(ratio, 3)) + '%, joten se poistettiin')
                                self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)

            self.changedFeatureIDs[featureType] = []
            self.addedFeatureIDs[featureType] = []

            self.updateEditableFeatureClassesCountUIInfo()
            self.featureLayer[featureType].startEditing()

            # self.dockWidgetGeometryEditSettings.plainTextEditMessages.clear()
        else:
            if featureType == 'alue':
                self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Uusien ja jaettujen kohteiden lukumäärät eivät ole samoja. Aluevarauskohteen kaavamääräystä ja teemaa ei aseteta")
            elif featureType == 'alue_taydentava':
                self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Uusien ja jaettujen kohteiden lukumäärät eivät ole samoja. Täydentävän aluekohteen kaavamääräystä ja teemaa ei aseteta")
            if featureType == 'viiva':
                self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Uusien ja jaettujen kohteiden lukumäärät eivät ole samoja. Viivamaisen kohteen kaavamääräystä ja teemaa ei aseteta")
            self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)
            #self.iface.messageBar().pushMessage('Uusien ja jaettujen kohteiden lukumäärät eivät ole samoja. Uuden viivamaisen kohteen kaavamääräystä ja teemaa ei aseteta', Qgis.Warning)

            self.changedFeatureIDs[featureType] = []
            self.addedFeatureIDs[featureType] = []

            self.featureLayer[featureType].startEditing()