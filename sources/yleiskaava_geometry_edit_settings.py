
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QTextCursor


from qgis.core import (
    Qgis, QgsProject,
    QgsMessageLog, QgsFeatureRequest,
    QgsApplication)

import os.path

from .yleiskaava_database import YleiskaavaDatabase


class GeometryEditSettings:

    def __init__(self, iface, plugin_dir, yleiskaavaSettings, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaSettings = yleiskaavaSettings
        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = plugin_dir

        self.dockWidgetGeometryEditSettings = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dockwidget_geometry_edit_settings.ui'))

        self.activeLayer = None

        self.featureLayer = {
            'alue': None,
            'alue_taydentava': None,
            'viiva': None,
            'piste': None
        }

        self.featureLayerEditBuffer = {
            'alue': None,
            'alue_taydentava': None,
            'viiva': None,
            'piste': None
        }

        self.addedFeatureIDs = {
            'alue': [],
            'alue_taydentava': [],
            'viiva': [],
            'piste': []
        }

        self.changedFeatureIDs = {
            'alue': [],
            'alue_taydentava': [],
            'viiva': [],
            'piste': []
        }

        self.featuresCopiedToClipboardLayer = None
        self.featuresCopiedToClipboard = None


    def setup(self):
        self.dockWidgetGeometryEditSettings.checkBoxKeepFeatureRelationsOnCopy.stateChanged.connect(self.handleCheckBoxKeepFeatureRelationsOnCopyStateChanged)
        self.dockWidgetGeometryEditSettings.checkBoxKeepFeatureRelationsOnSplit.stateChanged.connect(self.handleCheckBoxKeepFeatureRelationsOnSplitStateChanged)
        self.dockWidgetGeometryEditSettings.checkBoxPreventFeaturesWithTinyGeometries.stateChanged.connect(self.handleCheckBoxPreventFeaturesWithTinyGeometriesStateChanged)

        self.dockWidgetGeometryEditSettings.closed.connect(self.disconnectAll)
        self.dockWidgetGeometryEditSettings.visibilityChanged.connect(self.visibilityChangedDockWidgetGeometryEditSettings)


    def onClosePlugin(self):
        self.disconnectAll()


    def visibilityChangedDockWidgetGeometryEditSettings(self, visible):
        QgsMessageLog.logMessage("visibilityChangedDockWidgetGeometryEditSettings, visible: " + str(visible), 'Yleiskaava-työkalu', Qgis.Info)
        if visible:
            self.dockWidgetGeometryEditSettings.show()
        else:
            self.disconnectAll()


    def openDockWidgetGeometryEditSettings(self):
        # QgsMessageLog.logMessage("openDockWidgetGeometryEditSettings", 'Yleiskaava-työkalu', Qgis.Info)
        self.featureLayer['alue'] = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE)[0]
        self.featureLayer['alue_taydentava'] = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA)[0]
        self.featureLayer['viiva'] = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA)[0]
        self.featureLayer['piste'] = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_PISTE)[0]

        self.disconnectAll()
        self.followEdits()

        self.updateEditableFeatureClassesCountUIInfo()

        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockWidgetGeometryEditSettings)
        self.dockWidgetGeometryEditSettings.show()


    def followEdits(self):
        QgsMessageLog.logMessage("followEdits", 'Yleiskaava-työkalu', Qgis.Info)
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

        if self.dockWidgetGeometryEditSettings.checkBoxKeepFeatureRelationsOnSplit.isChecked():
            if self.featureLayer['alue'] != None:
                self.featureLayer['alue'].subsetStringChanged.connect(self.updateEditableFeatureClassesCountUIInfo)

                self.featureLayer['alue'].editingStarted.connect(self.followFeatureLayerEditsArea)
                self.featureLayer['alue'].editingStopped.connect(self.stopFollowingFeatureLayerEditsArea)
                self.featureLayer['alue'].editCommandEnded.connect(self.updateFeatureAttributesAfterEditCommandEndedArea)
        
            if self.featureLayer['alue_taydentava'] != None:
                self.featureLayer['alue_taydentava'].subsetStringChanged.connect(self.updateEditableFeatureClassesCountUIInfo)

                self.featureLayer['alue_taydentava'].editingStarted.connect(self.followFeatureLayerEditsSuplementaryArea)
                self.featureLayer['alue_taydentava'].editingStopped.connect(self.stopFollowingFeatureLayerEditsSuplementaryArea)
                self.featureLayer['alue_taydentava'].editCommandEnded.connect(self.updateFeatureAttributesAfterEditCommandEndedSuplementaryArea)

            if self.featureLayer['viiva'] != None:
                self.featureLayer['viiva'].subsetStringChanged.connect(self.updateEditableFeatureClassesCountUIInfo)

                # receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
                # QgsMessageLog.logMessage("followEdits - before receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
                # QgsMessageLog.logMessage("followEdits - connect(self.followLineFeatureLayerEdits)", 'Yleiskaava-työkalu', Qgis.Info)
                self.featureLayer['viiva'].editingStarted.connect(self.followFeatureLayerEditsLine)
                # receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
                # QgsMessageLog.logMessage("followEdits - after receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
                self.featureLayer['viiva'].editingStopped.connect(self.stopFollowingFeatureLayerEditsLine)
                self.featureLayer['viiva'].editCommandEnded.connect(self.updateFeatureAttributesAfterEditCommandEndedLine)

            if self.featureLayer['piste'] != None:
                # self.featureLayer['piste'].subsetStringChanged.connect(self.updateEditableFeatureClassesCountUIInfo)

                self.featureLayer['piste'].editingStarted.connect(self.followFeatureLayerEditsPoint)
                self.featureLayer['piste'].editingStopped.connect(self.stopFollowingFeatureLayerEditsPoint)

            self.iface.actionSplitFeatures().triggered.connect(self.actionSplitFeaturesTriggered)

        if self.dockWidgetGeometryEditSettings.checkBoxKeepFeatureRelationsOnCopy.isChecked():
            self.iface.actionCopyFeatures().triggered.connect(self.actionCopyCutFeaturesTriggered)
            self.iface.actionCutFeatures().triggered.connect(self.actionCopyCutFeaturesTriggered)
            self.iface.actionPasteFeatures().triggered.connect(self.actionPasteFeaturesTriggered)

    def followFeatureLayerEditsArea(self):
        self.followFeatureLayerEdits('alue')

    def followFeatureLayerEditsSuplementaryArea(self):
        self.followFeatureLayerEdits('alue_taydentava')

    def followFeatureLayerEditsLine(self):
        self.followFeatureLayerEdits('viiva')

    def followFeatureLayerEditsPoint(self):
        self.followFeatureLayerEdits('piste')


    def stopFollowingFeatureLayerEditsArea(self):
        self.stopFollowingFeatureLayerEdits('alue')

    def stopFollowingFeatureLayerEditsSuplementaryArea(self):
        self.stopFollowingFeatureLayerEdits('alue_taydentava')
    
    def stopFollowingFeatureLayerEditsLine(self):
        self.stopFollowingFeatureLayerEdits('viiva')

    def stopFollowingFeatureLayerEditsPoint(self):
        self.stopFollowingFeatureLayerEdits('piste')


    def updateFeatureAttributesAfterEditCommandEndedArea(self):
        self.updateFeatureAttributesAfterEditCommandEnded('alue')

    def updateFeatureAttributesAfterEditCommandEndedSuplementaryArea(self):
        self.updateFeatureAttributesAfterEditCommandEnded('alue_taydentava')
    
    def updateFeatureAttributesAfterEditCommandEndedLine(self):
        self.updateFeatureAttributesAfterEditCommandEnded('viiva')

    def updateFeatureAttributesAfterEditCommandEndedPoint(self):
        self.updateFeatureAttributesAfterEditCommandEnded('piste')
    

    def disconnectAll(self):
        QgsMessageLog.logMessage("disconnectAll", 'Yleiskaava-työkalu', Qgis.Info)
        self.disconnectAllOnSplit()
        self.disconnectAllOnCopyCutPaste()


    def disconnectAllOnSplit(self):
        try:
            self.iface.currentLayerChanged.disconnect(self.updateEditableFeatureClassesCountUIInfo)
        except TypeError:
            pass
        except RuntimeError:
            pass

        if self.featureLayer['alue'] != None:
            try:
                self.featureLayer['alue'].subsetStringChanged.disconnect(self.updateEditableFeatureClassesCountUIInfo)
            except TypeError:
                pass
            except RuntimeError:
                pass
            try:
                self.featureLayer['alue'].editingStarted.disconnect(self.followFeatureLayerEditsArea)
            except TypeError:
                pass
            except RuntimeError:
                pass
                # receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
                # QgsMessageLog.logMessage("disconnectAll - receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
            try:
                self.featureLayer['alue'].editingStopped.disconnect(self.stopFollowingFeatureLayerEditsArea)
            except TypeError:
                pass
            except RuntimeError:
                pass
            try:
                self.featureLayer['alue'].editCommandEnded.disconnect(self.updateFeatureAttributesAfterEditCommandEndedArea)
            except TypeError:
                pass
            except RuntimeError:
                pass

        if self.featureLayer['alue_taydentava'] != None:
            try:
                self.featureLayer['alue_taydentava'].subsetStringChanged.disconnect(self.updateEditableFeatureClassesCountUIInfo)
            except TypeError:
                pass
            except RuntimeError:
                pass
            try:
                self.featureLayer['alue_taydentava'].editingStarted.disconnect(self.followFeatureLayerEditsSuplementaryArea)
            except TypeError:
                pass
            except RuntimeError:
                pass
                # receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
                # QgsMessageLog.logMessage("disconnectAll - receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
            try:
                self.featureLayer['alue_taydentava'].editingStopped.disconnect(self.stopFollowingFeatureLayerEditsSuplementaryArea)
            except TypeError:
                pass
            except RuntimeError:
                pass
            try:
                self.featureLayer['alue_taydentava'].editCommandEnded.disconnect(self.updateFeatureAttributesAfterEditCommandEndedSuplementaryArea)
            except TypeError:
                pass
            except RuntimeError:
                pass

        if self.featureLayer['viiva'] != None:
            try:
                self.featureLayer['viiva'].subsetStringChanged.disconnect(self.updateEditableFeatureClassesCountUIInfo)
            except TypeError:
                pass
            except RuntimeError:
                pass
            try:
                self.featureLayer['viiva'].editingStarted.disconnect(self.followFeatureLayerEditsLine)
            except TypeError:
                pass
            except RuntimeError:
                pass
                # receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
                # QgsMessageLog.logMessage("disconnectAll - receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
            try:
                self.featureLayer['viiva'].editingStopped.disconnect(self.stopFollowingFeatureLayerEditsLine)
            except TypeError:
                pass
            except RuntimeError:
                pass
            try:
                self.featureLayer['viiva'].editCommandEnded.disconnect(self.updateFeatureAttributesAfterEditCommandEndedLine)
            except TypeError:
                pass
            except RuntimeError:
                pass

        if self.featureLayer['piste'] != None:
            try:
                # self.featureLayer['piste'].subsetStringChanged.disconnect(self.updateEditableFeatureClassesCountUIInfo)
                self.featureLayer['piste'].editingStarted.disconnect(self.followFeatureLayerEditsPoint)
            except TypeError:
                pass
            except RuntimeError:
                pass
                # receiversCount = self.lineFeatureLayer.receivers(self.lineFeatureLayer.editingStarted)
                # QgsMessageLog.logMessage("disconnectAll - receiversCount: " + str(receiversCount), 'Yleiskaava-työkalu', Qgis.Info)
            try:
                self.featureLayer['piste'].editingStopped.disconnect(self.stopFollowingFeatureLayerEditsPoint)
            except TypeError:
                pass
            except RuntimeError:
                pass

        try:
            self.iface.actionSplitFeatures().triggered.disconnect(self.actionSplitFeaturesTriggered)
        except TypeError:
            pass
        except RuntimeError:
            pass

    def disconnectAllOnCopyCutPaste(self):
        try:
            self.iface.actionCopyFeatures().triggered.disconnect(self.actionCopyCutFeaturesTriggered)
            self.iface.actionCutFeatures().triggered.disconnect(self.actionCopyCutFeaturesTriggered)
            self.iface.actionPasteFeatures().triggered.disconnect(self.actionPasteFeaturesTriggered)
        except TypeError:
            pass
        except RuntimeError:
            pass


    def updateEditableFeatureClassesCountUIInfo(self):
        self.activeLayer = self.iface.activeLayer()
        if self.activeLayer is None or (self.activeLayer.name() != YleiskaavaDatabase.KAAVAOBJEKTI_ALUE and self.activeLayer.name() != YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA and self.activeLayer.name() != YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA):
            self.dockWidgetGeometryEditSettings.lineEditEditableFeatureClassesCount.setStyleSheet("background-color: rgb(255, 255, 255);")
            self.dockWidgetGeometryEditSettings.lineEditEditableFeatureClassesCount.setText('')
        elif self.activeLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_ALUE or self.activeLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA or self.activeLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA:
            featureClasses = {}
            featureRequest = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setSubsetOfAttributes(["kayttotarkoitus_lyhenne"], self.activeLayer.fields())
            for feature in self.activeLayer.getFeatures(featureRequest):
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
        QgsMessageLog.logMessage('updateFeatureAttributesAfterEditCommandEnded - featureType:' + featureType, 'Yleiskaava-työkalu', Qgis.Info)
        if self.iface.actionSplitFeatures().isChecked():
            self.addRegulationAndThemeRelationsToFeature(featureType)
            self.yleiskaavaUtils.refreshTargetLayersInProject()


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
            # QgsMessageLog.logMessage('followFeatureLayerEdits - featureType == "viiva"', 'Yleiskaava-työkalu', Qgis.Info)
            self.featureLayerEditBuffer[featureType].geometryChanged.connect(self.lineFeatureGeometryChanged)
            try:
                self.featureLayer[featureType].featureAdded.disconnect(self.lineFeatureAdded)
            except TypeError:
                pass
            self.featureLayer[featureType].featureAdded.connect(self.lineFeatureAdded)
        elif featureType == 'piste':
            # QgsMessageLog.logMessage('followFeatureLayerEdits - featureType == "piste"', 'Yleiskaava-työkalu', Qgis.Info)
            # self.featureLayerEditBuffer[featureType].geometryChanged.connect(self.lineFeatureGeometryChanged)
            try:
                self.featureLayer[featureType].featureAdded.disconnect(self.pointFeatureAdded)
            except TypeError:
                pass
            self.featureLayer[featureType].featureAdded.connect(self.pointFeatureAdded)


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
        if fid not in self.changedFeatureIDs['alue']:
            self.changedFeatureIDs['alue'].append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Aluevarauskohteen geometriassa muutos, käyttötarkoitus: " + str(self.featureLayer['alue'].getFeature(fid)["kayttotarkoitus_lyhenne"]) + ", muuttuneita aluevarauskohteita yhteensä: " + str(len(self.changedFeatureIDs['alue'])))
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)


    def suplementaryAreaFeatureGeometryChanged(self, fid, geometry):
        #QgsMessageLog.logMessage("suplementaryAreaFeatureGeometryChanged - fid: " + str(fid) + ", geometry.area(): " + str(geometry.area()), 'Yleiskaava-työkalu', Qgis.Info)
        # changedGeometries = self.suplementaryAreaFeatureLayerEditBuffer.changedGeometries()
        # for key in changedGeometries.keys():
        #     QgsMessageLog.logMessage("suplementaryAreaFeatureGeometryChanged - changedGeometries, key: " + str(key) + ", geometry.area(): " + str(geometry.area()), 'Yleiskaava-työkalu', Qgis.Info)
        if fid not in self.changedFeatureIDs['alue_taydentava']:
            self.changedFeatureIDs['alue_taydentava'].append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Täydentävän aluekohteen geometriassa muutos, käyttötarkoitus: " + str(self.featureLayer['alue_taydentava'].getFeature(fid)["kayttotarkoitus_lyhenne"]) + ", muuttuneita täydentäviä aluekohteita yhteensä: " + str(len(self.changedFeatureIDs['alue_taydentava'])))
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)


    def lineFeatureGeometryChanged(self, fid, geometry):
        # QgsMessageLog.logMessage("lineFeatureGeometryChanged - fid: " + str(fid) + ", geometry.length(): " + str(geometry.length()), 'Yleiskaava-työkalu', Qgis.Info)
        # QgsMessageLog.logMessage("lineFeatureGeometryChanged - self.lineFeatureLayer.getFeature(fid).geometry().length(): " + str(self.lineFeatureLayer.getFeature(fid).geometry().length()), 'Yleiskaava-työkalu', Qgis.Info)
        # for key in addedFeatures.keys():
        #     QgsMessageLog.logMessage("lineFeatureGeometryChanged - addedFeatures, key: " + str(key) + ", feature.geometry.length(): " + str( addedFeatures[key].geometry().length()), 'Yleiskaava-työkalu', Qgis.Info)
        if fid not in self.changedFeatureIDs['viiva']:
            self.changedFeatureIDs['viiva'].append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Viivamaisen kohteen geometriassa muutos, käyttötarkoitus: " + str(self.featureLayer['viiva'].getFeature(fid)["kayttotarkoitus_lyhenne"]) + ", muuttuneita viivamaisia kohteita yhteensä: " + str(len(self.changedFeatureIDs['viiva'])))
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)

        # if len(self.addedLineFeatureIDs) == 1:
        #     self.addRegulationAndThemeRelationsToLineFeature()
        # elif len(self.addedLineFeatureIDs) > 1:
        #     self.iface.messageBar().pushMessage('Uusia viivamaisia kohteita on useita, joten uuden kohteen kaavamääräystä ja teemaa ei aseteta', Qgis.Warning)


    def areaFeatureAdded(self, fid):
        # QgsMessageLog.logMessage("areaFeatureAdded - fid: " + str(fid), 'Yleiskaava-työkalu', Qgis.Info)
        # QgsMessageLog.logMessage("areaFeatureAdded - self.areaFeatureLayer.featureCount(): " + str(self.featureLayer['alue'].featureCount()), 'Yleiskaava-työkalu', Qgis.Info)
        self.addedFeatureIDs['alue'].append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Uusi aluevarauskohde, uusia yhteensä: " + str(len(self.addedFeatureIDs['alue'])))
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)
        if not self.iface.actionSplitFeatures().isChecked() and self.featuresCopiedToClipboardLayer is not None and self.featuresCopiedToClipboard is not None and self.featuresCopiedToClipboardLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_ALUE:
            self.handlePasteFeatures('alue')


    def suplementaryAreaFeatureAdded(self, fid):
        # QgsMessageLog.logMessage("suplementaryAreaFeatureAdded - fid: " + str(fid), 'Yleiskaava-työkalu', Qgis.Info)
        # QgsMessageLog.logMessage("suplementaryAreaFeatureAdded - self.suplementaryAreaFeatureLayer.featureCount(): " + str(self.featureLayer['alue_taydentava'].featureCount()), 'Yleiskaava-työkalu', Qgis.Info)
        self.addedFeatureIDs['alue_taydentava'].append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Uusi täydentävä aluekohde, uusia yhteensä: " + str(len(self.addedFeatureIDs['alue_taydentava'])))
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)
        if not self.iface.actionSplitFeatures().isChecked() and self.featuresCopiedToClipboardLayer is not None and self.featuresCopiedToClipboard is not None and self.featuresCopiedToClipboardLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA:
            self.handlePasteFeatures('alue_taydentava')

    def lineFeatureAdded(self, fid):
        # QgsMessageLog.logMessage("lineFeatureAdded - fid: " + str(fid), 'Yleiskaava-työkalu', Qgis.Info)
        # QgsMessageLog.logMessage("lineFeatureAdded - self.lineFeatureLayer.featureCount(): " + str(self.featureLayer['viiva'].featureCount()), 'Yleiskaava-työkalu', Qgis.Info)
        #self.addedFeatureIDs.append(fid)
        self.addedFeatureIDs['viiva'].append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Uusi viivamainen kohde, uusia yhteensä: " + str(len(self.addedFeatureIDs['viiva'])))
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)
        if not self.iface.actionSplitFeatures().isChecked() and self.featuresCopiedToClipboardLayer is not None and self.featuresCopiedToClipboard is not None and self.featuresCopiedToClipboardLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA:
            self.handlePasteFeatures('viiva')
        # if len(self.changedLineFeatureIDs) == 1:
        #     self.addRegulationAndThemeRelationsToLineFeature()
        # elif len(self.changedLineFeatureIDs) > 1:
        #     self.iface.messageBar().pushMessage('Geometrialtaan muuttuneita viivamaisia kohteita on useita, joten uuden viivamaisen kohteen kaavamääräystä ja teemaa ei aseteta', Qgis.Warning)


    def pointFeatureAdded(self, fid):
        # QgsMessageLog.logMessage("pointFeatureAdded - fid: " + str(fid), 'Yleiskaava-työkalu', Qgis.Info)
        # self.featuresCopiedToClipboardLayer = None
        # self.featuresCopiedToClipboard

        self.addedFeatureIDs['piste'].append(fid)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Uusi pistemäinen kohde, uusia yhteensä: " + str(len(self.addedFeatureIDs['piste'])))
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)
        if not self.iface.actionSplitFeatures().isChecked() and self.featuresCopiedToClipboardLayer is not None and self.featuresCopiedToClipboard is not None and self.featuresCopiedToClipboardLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_PISTE:
            self.handlePasteFeatures('piste')


    def handlePasteFeatures(self, featureType):
        if len(self.addedFeatureIDs[featureType]) == len(self.featuresCopiedToClipboard):
            if self.dockWidgetGeometryEditSettings.checkBoxKeepFeatureRelationsOnCopy.isChecked():
                if self.featuresCopiedToClipboardLayer.name() == self.iface.activeLayer().name():

                    shouldReturnToEditMode = self.featureLayer[featureType].isEditable()
                    self.featureLayer[featureType].commitChanges()

                    for addedFeatureID in self.addedFeatureIDs[featureType]:
                        QgsMessageLog.logMessage("handlePasteFeatures - haetaan liitetylle kohteelle täsmäystä, addedFeatureID: " + str(addedFeatureID), 'Yleiskaava-työkalu', Qgis.Info)
                        addedFeature = self.featureLayer[featureType].getFeature(addedFeatureID)

                        foundMatch = False
                        foundMatchMultiple = False
                        matchedSourceFeature = None

                        for clipboardFeature in self.featuresCopiedToClipboard:
                            featuresMatch = self.featuresMatch(clipboardFeature, addedFeature)
                            if featuresMatch == True and foundMatch == True:
                                foundMatchMultiple = True
                                break
                            elif featuresMatch == True:
                                foundMatch = True
                                matchedSourceFeature = clipboardFeature

                        if matchedSourceFeature is not None and addedFeature is not None:
                            self.addRegulationAndThemeRelationsToFeatureFromCopy(matchedSourceFeature, addedFeature, featureType)
                            # self.featuresCopiedToClipboard = [feature for feature in self.featuresCopiedToClipboard if feature['id'] != matchedSourceFeature['id']]
                        else:
                            QgsMessageLog.logMessage("handlePasteFeatures - bugi koodissa, matchedSourceFeature: " + str(matchedSourceFeature) + ", addedFeature: " + str(addedFeature), 'Yleiskaava-työkalu', Qgis.Critical)

                        if foundMatchMultiple:
                            self.iface.messageBar().pushMessage('Liitetyllä kohteella ' + addedFeature['id'] + ' on useita täsmääviä kohteita, joten sen kaavamääräys- ja teema-relaatiot eivät ehkä kopioituneet oikein. Myös muilla liitetyillä kohteilla, joilla on samat täsmäykset on sama ongelma.', Qgis.Warning)
                            self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText('Liitetyllä kohteella ' + addedFeature['id'] + ' on useita täsmääviä kohteita, joten sen kaavamääräys- ja teema-relaatiot eivät ehkä kopioituneet oikein. Myös muilla liitetyillä kohteilla, joilla on samat täsmäykset on sama ongelma.')
                            self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)

                    if shouldReturnToEditMode:
                        self.featureLayer[featureType].startEditing()

            self.changedFeatureIDs[featureType] = []
            self.addedFeatureIDs[featureType] = []
            self.featuresCopiedToClipboardLayer = None
            self.featuresCopiedToClipboard = None
            self.yleiskaavaUtils.refreshTargetLayersInProject()


    def featuresMatch(self, clipboardFeature, addedFeature):
        if addedFeature.hasGeometry() and clipboardFeature.hasGeometry():
            if not addedFeature.geometry().equals(clipboardFeature.geometry()):
                return False
        elif (addedFeature.hasGeometry() and not clipboardFeature.hasGeometry()) or (not addedFeature.hasGeometry() and clipboardFeature.hasGeometry()):
            return False

        fields = addedFeature.fields().toList()
        for field in fields:
            if field.name() != 'id' and field.name() != 'version_alkamispvm' and field.name() != 'muokkaaja' and field.name() != 'pinta_ala_ha' and field.name() != 'pituus_km':
                addedFeatureValue = addedFeature[field.name()]
                clipboardFeatureValue = clipboardFeature[field.name()]
                if addedFeatureValue != clipboardFeatureValue:
                    return False

        return True


    def addRegulationAndThemeRelationsToFeatureFromCopy(self, matchedSourceFeature, addedFeature, featureType):

        self.yleiskaavaDatabase.reconnectToDB()
        
        self.yleiskaavaDatabase.addRegulationRelationsToLayer(matchedSourceFeature["id"], addedFeature["id"], featureType)
        self.yleiskaavaDatabase.addThemeRelationsToLayer(matchedSourceFeature["id"], addedFeature["id"], featureType)
        self.iface.messageBar().pushMessage('Kaavamääräykset ja teemat lisätty liitetylle kohteelle', Qgis.Info, 5)
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.appendPlainText("Kaavamääräykset ja teemat lisätty liitetylle kohteelle")
        self.dockWidgetGeometryEditSettings.plainTextEditMessages.moveCursor(QTextCursor.End)


    def addRegulationAndThemeRelationsToFeature(self, featureType):

        shouldReturnToEditMode = self.featureLayer[featureType].isEditable()
        self.featureLayer[featureType].commitChanges()

        if len(self.changedFeatureIDs[featureType]) == len(self.addedFeatureIDs[featureType]):
            for index, sourceFeatureID in enumerate(self.changedFeatureIDs[featureType]):

                sourceFeatureID = self.changedFeatureIDs[featureType][index]
                targetFeatureID = self.addedFeatureIDs[featureType][index]
                sourceFeature = self.featureLayer[featureType].getFeature(sourceFeatureID)
                targetFeature = self.featureLayer[featureType].getFeature(targetFeatureID)
                sourceFeatureUUID = sourceFeature["id"]
                targetFeatureUUID = targetFeature["id"]
                
                # QgsMessageLog.logMessage("addRegulationAndThemeRelationsToFeature - sourceFeatureUUID: " + str(sourceFeatureUUID) + ", targetFeatureUUID: " + str(targetFeatureUUID), 'Yleiskaava-työkalu', Qgis.Info)

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

                    if self.dockWidgetGeometryEditSettings.checkBoxKeepFeatureRelationsOnSplit.isChecked():
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

            self.updateEditableFeatureClassesCountUIInfo()
            # self.featureLayer[featureType].startEditing()

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

        if shouldReturnToEditMode:
            self.featureLayer[featureType].startEditing()
            # self.featureLayer[featureType].startEditing()


    def handleCheckBoxKeepFeatureRelationsOnCopyStateChanged(self):
        self.featuresCopiedToClipboardLayer = None
        self.featuresCopiedToClipboard = None
        self.changedFeatureIDs['alue'] = []
        self.addedFeatureIDs['alue'] = []
        self.changedFeatureIDs['alue_taydentava'] = []
        self.addedFeatureIDs['alue_taydentava'] = []
        self.changedFeatureIDs['viiva'] = []
        self.addedFeatureIDs['viiva'] = []
        self.changedFeatureIDs['piste'] = []
        self.addedFeatureIDs['piste'] = []

        if self.dockWidgetGeometryEditSettings.checkBoxKeepFeatureRelationsOnCopy.isChecked():
            self.iface.actionCopyFeatures().triggered.connect(self.actionCopyCutFeaturesTriggered)
            self.iface.actionCutFeatures().triggered.connect(self.actionCopyCutFeaturesTriggered)
            self.iface.actionPasteFeatures().triggered.connect(self.actionPasteFeaturesTriggered)
        else:
            self.iface.actionCopyFeatures().triggered.disconnect(self.actionCopyCutFeaturesTriggered)
            self.iface.actionCutFeatures().triggered.disconnect(self.actionCopyCutFeaturesTriggered)
            self.iface.actionPasteFeatures().triggered.disconnect(self.actionPasteFeaturesTriggered)

    def handleCheckBoxKeepFeatureRelationsOnSplitStateChanged(self):
        self.featuresCopiedToClipboardLayer = None
        self.featuresCopiedToClipboard = None
        self.changedFeatureIDs['alue'] = []
        self.addedFeatureIDs['alue'] = []
        self.changedFeatureIDs['alue_taydentava'] = []
        self.addedFeatureIDs['alue_taydentava'] = []
        self.changedFeatureIDs['viiva'] = []
        self.addedFeatureIDs['viiva'] = []
        self.changedFeatureIDs['piste'] = []
        self.addedFeatureIDs['piste'] = []

        if self.dockWidgetGeometryEditSettings.checkBoxKeepFeatureRelationsOnSplit.isChecked():
            self.followEdits()
        else:
            self.disconnectAllOnSplit()


    def actionSplitFeaturesTriggered(self):
        QgsMessageLog.logMessage("actionSplitFeaturesTriggered", 'Yleiskaava-työkalu', Qgis.Info)
        self.featuresCopiedToClipboardLayer = None
        self.featuresCopiedToClipboard = None
        self.changedFeatureIDs['alue'] = []
        self.addedFeatureIDs['alue'] = []
        self.changedFeatureIDs['alue_taydentava'] = []
        self.addedFeatureIDs['alue_taydentava'] = []
        self.changedFeatureIDs['viiva'] = []
        self.addedFeatureIDs['viiva'] = []
        self.changedFeatureIDs['piste'] = []
        self.addedFeatureIDs['piste'] = []


    def actionCopyCutFeaturesTriggered(self):
        # 1. tarkista aktiivinen layer
        # 2. hae sieltä valitut kohteet
        # 3. ota niiden ominaisuudet jotenkin talteen
        # 4. pasten / featureAdded yhteydessä jotenkin selvitä mikä feature liittyy mihinkin copyn featureen
        #  - voiko kohteiden järjestyksen luottaa pysyvän samana? ei voine
        #  - jos tekee relaatioiden kopioinnin liitetylle kohteelle vain, jos kahdella (tai useammalla) kopioidulla kohteella ei ole täysin samoja ominaisuuksia <- toimii varmasti
        self.changedFeatureIDs['alue'] = []
        self.addedFeatureIDs['alue'] = []
        self.changedFeatureIDs['alue_taydentava'] = []
        self.addedFeatureIDs['alue_taydentava'] = []
        self.changedFeatureIDs['viiva'] = []
        self.addedFeatureIDs['viiva'] = []
        self.changedFeatureIDs['piste'] = []
        self.addedFeatureIDs['piste'] = []
        # text = QgsApplication.clipboard().text()
        # QgsMessageLog.logMessage("actionCopyFeaturesTriggered - text: " + str(text), 'Yleiskaava-työkalu', Qgis.Info)
        if self.activeLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_ALUE or self.activeLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA or self.activeLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA or self.activeLayer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_PISTE:
            self.featuresCopiedToClipboardLayer = self.iface.activeLayer()
            self.featuresCopiedToClipboard = list(self.featuresCopiedToClipboardLayer.getSelectedFeatures())
            # for selectedFeature in self.featuresCopiedToClipboard:
            #     QgsMessageLog.logMessage("actionCopyCutFeaturesTriggered - selectedFeature['luokittelu']: " + str(selectedFeature['luokittelu']), 'Yleiskaava-työkalu', Qgis.Info)
        else:
            self.featuresCopiedToClipboardLayer = None
            self.featuresCopiedToClipboard = None


    def actionPasteFeaturesTriggered(self):
        pass