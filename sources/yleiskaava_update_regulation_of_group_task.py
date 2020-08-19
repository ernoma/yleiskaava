
from qgis.core import (
    Qgis, QgsFeature,
    QgsMessageLog,
    QgsTask, QgsFeatureRequest)

from .yleiskaava_database import YleiskaavaDatabase


class UpdateRegulationOfGroupTask(QgsTask):

    def __init__(self, yleiskaavaDatabase, featureType, regulationID, regulationTitle, shouldRemoveOldRegulationRelations, shouldUpdateRegulationTextsEvenIfSpatialFeatureHasMultipleRegulations):
        super().__init__('Päivitetään kaavamääräyksiä', QgsTask.CanCancel)
        self.exceptions = []

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.featureType = featureType
        self.regulationID = regulationID
        self.regulationTitle = regulationTitle
        self.shouldRemoveOldRegulationRelations = shouldRemoveOldRegulationRelations
        self.shouldUpdateRegulationTextsEvenIfSpatialFeatureHasMultipleRegulations = shouldUpdateRegulationTextsEvenIfSpatialFeatureHasMultipleRegulations


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
            regulationCount = self.yleiskaavaDatabase.getRegulationCountForSpatialFeature(feature["id"], self.featureType)

            shouldUpdateOnlyRelation = False

            if regulationCount >= 1 and not self.shouldUpdateRegulationTextsEvenIfSpatialFeatureHasMultipleRegulations and not self.shouldRemoveOldRegulationRelations:
                shouldUpdateOnlyRelation = True

            # QgsMessageLog.logMessage("updateRegulationsAndLandUseClassificationsForSpatialFeatures - feature['feature']['kaavammaraysotsikko']: " + feature['feature']['kaavammaraysotsikko'] + ", regulationCount for feature: " + str(regulationCount), 'Yleiskaava-työkalu', Qgis.Info)

            success = True
            success = self.yleiskaavaDatabase.updateSpatialFeatureRegulationAndLandUseClassification(feature["id"], self.featureType, self.regulationID, self.regulationTitle, self.shouldRemoveOldRegulationRelations, shouldUpdateOnlyRelation)

            if not success:
                break

            progress = (index / featureCount) * 100
            self.setProgress(progress)

        return success


    def finished(self, success):
        if not success:
            QgsMessageLog.logMessage('UpdateRegulationOfGroupTask - poikkeuksia: ', 'Yleiskaava-työkalu', Qgis.Critical)
            for exception in self.exceptions:
                QgsMessageLog.logMessage(str(self.exception), 'Yleiskaava-työkalu', Qgis.Critical)
            # raise self.exception
            # self.cancel()


    def cancel(self):
        QgsMessageLog.logMessage(
            'UpdateRegulationOfGroupTask "{name}" keskeytettiin'.format(
                name=self.description()),
            'Yleiskaava-työkalu', Qgis.Info)
        super().cancel()