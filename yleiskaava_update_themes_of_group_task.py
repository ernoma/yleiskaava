
from qgis.core import (
    Qgis, QgsFeature,
    QgsMessageLog,
    QgsTask, QgsFeatureRequest)

from .yleiskaava_database import YleiskaavaDatabase


class UpdateThemesOfGroupTask(QgsTask):

    def __init__(self, yleiskaavaDatabase, featureType, themeID, themeName, shouldRemoveOldThemeRelations):
        super().__init__('Päivitetään teemoja', QgsTask.CanCancel)
        self.exceptions = []

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.featureType = featureType
        self.themeID = themeID
        self.themeName = themeName
        self.shouldRemoveOldThemeRelations = shouldRemoveOldThemeRelations


    def run(self):
        targetLayer = None
        spatialFeatures = None
        featureCount = 0
        layers = self.dependentLayers()
        for layer in layers:
            if layer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_ALUE or layer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA or layer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA or layer.name() == YleiskaavaDatabase.KAAVAOBJEKTI_PISTE:
                targetLayer = layer
                featureRequest = QgsFeatureRequest().setSubsetOfAttributes(["id"], targetLayer.fields())
                spatialFeatures = targetLayer.getSelectedFeatures(featureRequest)
                featureCount = targetLayer.selectedFeatureCount()

        for index, feature in enumerate(spatialFeatures):
            success = self.yleiskaavaDatabase.updateSpatialFeatureTheme(feature["id"], self.featureType, self.themeID, self.themeName, self.shouldRemoveOldThemeRelations)
            if not success:
                break

            progress = (index / featureCount) * 100
            self.setProgress(progress)

        return success


    def finished(self, success):
        if not success:
            QgsMessageLog.logMessage('UpdateThemesOfGroupTask - poikkeuksia: ', 'Yleiskaava-työkalu', Qgis.Critical)
            for exception in self.exceptions:
                QgsMessageLog.logMessage(str(self.exception), 'Yleiskaava-työkalu', Qgis.Critical)
            # raise self.exception
            # self.cancel()


    def cancel(self):
        QgsMessageLog.logMessage(
            'UpdateThemesOfGroupTask "{name}" keskeytettiin'.format(
                name=self.description()),
            'Yleiskaava-työkalu', Qgis.Info)
        super().cancel()