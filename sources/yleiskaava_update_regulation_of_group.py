

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtWidgets import QProgressDialog

from qgis.core import (Qgis, QgsProject, QgsMessageLog, QgsApplication)

import os.path
import uuid
from operator import itemgetter

from .yleiskaava_database import YleiskaavaDatabase
from .yleiskaava_update_regulation_of_group_task import UpdateRegulationOfGroupTask

class UpdateRegulationOfGroup:

    def __init__(self, iface, plugin_dir, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = plugin_dir

        self.dialogUpdateRegulationOfGroup = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_update_regulation_of_group.ui'))
        self.dialogUpdateRegulationOfGroup.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)

        self.regulations = None
        self.regulationTitles = None

        self.currentRegulation = None

        self.hasUserSelectedPolygonFeaturesForUpdate = False
        self.hasUserSelectedSuplementaryPolygonFeaturesForUpdate = False
        self.hasUserSelectedLineFeaturesForUpdate = False
        self.hasUserSelectedPointFeaturesForUpdate = False

        self.hasUserCanceledCopy = False
        self.progressDialog = None
        self.shouldHide = False

    def setup(self):
        self.setupDialogUpdateRegulationOfGroup()


    def setupDialogUpdateRegulationOfGroup(self):

        self.dialogUpdateRegulationOfGroup.comboBoxRegulationTitles.currentIndexChanged.connect(self.handleComboBoxRegulationTitleChanged)

        self.dialogUpdateRegulationOfGroup.checkBoxShowOnlyUsedRegulations.stateChanged.connect(self.checkBoxShowOnlyUsedRegulationsStateChanged)
        self.dialogUpdateRegulationOfGroup.checkBoxShowAreaRegulations.stateChanged.connect(self.checkBoxShowAreaRegulationsStateChanged)
        self.dialogUpdateRegulationOfGroup.checkBoxShowSuplementaryAreaRegulations.stateChanged.connect(self.checkBoxShowSuplementaryAreaRegulationsStateChanged)
        self.dialogUpdateRegulationOfGroup.checkBoxShowLineRegulations.stateChanged.connect(self.checkBoxShowLineRegulationsStateChanged)
        self.dialogUpdateRegulationOfGroup.checkBoxShowPointRegulations.stateChanged.connect(self.checkBoxShowPointRegulationsStateChanged)

        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPolygonFeatures.stateChanged.connect(self.checkBoxUpdateLandUseClassificationsForPolygonFeaturesStateChanged)
        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeatures.stateChanged.connect(self.checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeaturesStateChanged)
        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForLineFeatures.stateChanged.connect(self.checkBoxUpdateLandUseClassificationsForLineFeaturesStateChanged)
        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPointFeatures.stateChanged.connect(self.checkBoxUpdateLandUseClassificationsForPointFeaturesStateChanged)

        # Varoita käyttäjää, jos jo valmiiksi valittuja kohteita
        self.dialogUpdateRegulationOfGroup.pushButtonSelectPolygonFeatures.clicked.connect(self.selectPolygonFeatures)
        self.dialogUpdateRegulationOfGroup.pushButtonSelectSupplementaryPolygonFeatures.clicked.connect(self.selectSupplementaryPolygonFeatures)
        self.dialogUpdateRegulationOfGroup.pushButtonSelectLineFeatures.clicked.connect(self.selectLineFeatures)
        self.dialogUpdateRegulationOfGroup.pushButtonSelectPointFeatures.clicked.connect(self.selectPointFeatures)

        self.dialogUpdateRegulationOfGroup.pushButtonUpdate.clicked.connect(self.handleUpdateRegulation)
        self.dialogUpdateRegulationOfGroup.pushButtonUpdateAndClose.clicked.connect(self.handleUpdateRegulationAndClose)

        self.dialogUpdateRegulationOfGroup.pushButtonCancel.clicked.connect(self.dialogUpdateRegulationOfGroup.hide)
    

    def selectPolygonFeatures(self):
        layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE)[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Aluevaraukset karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedPolygonFeaturesForUpdate = True

        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPolygonFeatures.setChecked(True)


    def selectSupplementaryPolygonFeatures(self):
        layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA)[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Täydentävät aluekohteet karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedSuplementaryPolygonFeaturesForUpdate = True

        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeatures.setChecked(True)


    def selectLineFeatures(self):
        layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA)[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Viivamaiset kaavakohteet karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedLineFeaturesForUpdate = True

        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForLineFeatures.setChecked(True)


    def selectPointFeatures(self):
        layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_PISTE)[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Pistemäiset kaavakohteet karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedPointFeaturesForUpdate = True

        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPointFeatures.setChecked(True)


    def checkBoxUpdateLandUseClassificationsForPolygonFeaturesStateChanged(self):
        pass
        # if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPolygonFeatures.isChecked():
        #     self.dialogUpdateRegulationOfGroup.pushButtonSelectPolygonFeatures.setEnabled(True)
        # else:
        #     self.dialogUpdateRegulationOfGroup.pushButtonSelectPolygonFeatures.setEnabled(False)

    def checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeaturesStateChanged(self):
        pass
        # if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeatures.isChecked():
        #     self.dialogUpdateRegulationOfGroup.pushButtonSelectSupplementaryPolygonFeatures.setEnabled(True)
        # else:
        #     self.dialogUpdateRegulationOfGroup.pushButtonSelectSupplementaryPolygonFeatures.setEnabled(False)

    def checkBoxUpdateLandUseClassificationsForLineFeaturesStateChanged(self):
        pass
        # if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForLineFeatures.isChecked():
        #     self.dialogUpdateRegulationOfGroup.pushButtonSelectLineFeatures.setEnabled(True)
        # else:
        #     self.dialogUpdateRegulationOfGroup.pushButtonSelectLineFeatures.setEnabled(False)

    def checkBoxUpdateLandUseClassificationsForPointFeaturesStateChanged(self):
        pass
        # if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPointFeatures.isChecked():
        #     self.dialogUpdateRegulationOfGroup.pushButtonSelectPointFeatures.setEnabled(True)
        # else:
        #     self.dialogUpdateRegulationOfGroup.pushButtonSelectPointFeatures.setEnabled(False)


    def openDialogUpdateRegulationOfGroup(self):
        self.reset()
        self.dialogUpdateRegulationOfGroup.show()


    def handleUpdateRegulation(self):
        self.shouldHide = False
        self.updateRegulation()

    def handleUpdateRegulationAndClose(self):
        self.shouldHide = True
        self.updateRegulation()


    def updateRegulation(self):
        # Päivitä kaavamääräys ja siihen liitetyt kaavakohteet ja huomio asetukset, sekä mahd. useat määräykset kohteella kayttotarkoitus_lyhenne-päivityksessä.
        # Tarkista, onko kaavamääräyksen lomaketiedoissa eroa ja jos ei, niin ilmoita käyttäjälle.
        # Lisää kaavamääräys sellaisille kaavakohteille, joilla sitä ei vielä ole, mutta käyttäjä on ko. kaavakohteen valinnut / valitsee
        # Anna käyttäjän valita kaavakohteet, joille kaavamääräys päivitetään.
        # Varmista, että käyttäjä ei voi vahingossa päivittää jo aiemmin valitsemiaan kaavaobjekteja.
        # Varmista jotenkin, että käyttäjän valitsemat kohteet päivitetään vaikka niillä olisi eri kaavamääräys kuin muutettava kaavamääräys / rajoita valintamahdollisuus kohteisiin, joilla muutettavan kaavamääräyksen relaatio
        # Ilmoita käyttäjälle, että valitse kohteet, tms., jos ei ole valinnut.
        # Varmista, että self.currentRegulation != None jo vaikka käyttäjä ei ole valinnut dialogista kohteita / lisää ensimmäiseksi vaihtoehdoksi comboboxiin "Valitse kaavamääräys"
        # Huomioi, "Poista kaavakohteilta vanhat kaavamääräykset"-asetuksen pois päältä olo, kun käyttäjä vain päivittää kohteilla jo olevaa kaavamääräystä -> ei siis tehdä duplikaattirelaatiota
        # Kun "Päivitä käyttötarkoitus vaikka kohteella olisi useita kaavamääräyksiä"-asetus on pois päältä, niin lisää kuitenkin kaavamääräys
        if self.currentRegulation != None:
            regulationID = self.currentRegulation["id"]
            regulationTitle = self.dialogUpdateRegulationOfGroup.plainTextEditRegulationTitle.toPlainText()
            regulationText = self.dialogUpdateRegulationOfGroup.plainTextEditRegulationText.toPlainText()
            regulationDescription = self.dialogUpdateRegulationOfGroup.plainTextEditRegulationDescription.toPlainText()

            if not self.equalsRegulationAndFormTexts(regulationTitle, regulationText, regulationDescription):
                success = self.yleiskaavaDatabase.updateRegulation(regulationID, regulationTitle, regulationText, regulationDescription)

                if success:
                    self.currentRegulation["alpha_sort_key"] = regulationTitle
                    self.currentRegulation["kaavamaarays_otsikko"] = QVariant(regulationTitle)
                    self.currentRegulation["maaraysteksti"] = QVariant(regulationText)
                    self.currentRegulation["kuvaus_teksti"] = QVariant(regulationDescription)

                    self.iface.messageBar().pushMessage('Kaavamääräys päivitetty', Qgis.Info, 30)
            elif not self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPolygonFeatures.isChecked() and not self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeatures.isChecked() and not self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForLineFeatures.isChecked() and not self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPointFeatures.isChecked():
                self.iface.messageBar().pushMessage('Kaavamääräykseen ei ole tehty muutoksia eikä päivitettäviä kaavakohteita ole valittu. Ei tehdä päivityksiä', Qgis.Info, 30)

            if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPolygonFeatures.isChecked():
                if not self.hasUserSelectedPolygonFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä aluevarauksia; aluevarauksia ei päivitetty', Qgis.Warning)
                else:
                    self.progressDialog = QProgressDialog("Päivitetään aluevarausten kaavamääräyksiä...", "Keskeytä", 0, 100)
                    self.progressDialog.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowStaysOnTopHint)
                    self.updateRegulationsAndLandUseClassificationsForSpatialFeatures("alue")
            if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeatures.isChecked():
                if not self.hasUserSelectedSuplementaryPolygonFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä täydentäviä aluekohteita; täydentäviä aluekohteita ei päivitetty', Qgis.Warning)
                else:
                    self.progressDialog = QProgressDialog("Päivitetään täydentävien aluekohteiden kaavamääräyksiä...", "Keskeytä", 0, 100)
                    self.progressDialog.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowStaysOnTopHint)
                    self.updateRegulationsAndLandUseClassificationsForSpatialFeatures("alue_taydentava")
            if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForLineFeatures.isChecked():
                if not self.hasUserSelectedLineFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä viivamaisia kohteita; viivamaisia ei päivitetty', Qgis.Warning)
                else:
                    self.progressDialog = QProgressDialog("Päivitetään viimamaisten kohteiden kaavamääräyksiä...", "Keskeytä", 0, 100)
                    self.progressDialog.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowStaysOnTopHint)
                    self.updateRegulationsAndLandUseClassificationsForSpatialFeatures("viiva")
            if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPointFeatures.isChecked():
                if not self.hasUserSelectedPointFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä pistemäisiä kohteita; pistemäisiä kohteita ei päivitetty', Qgis.Warning)
                else:
                    self.progressDialog = QProgressDialog("Päivitetään pistemäisten kohteiden kaavamääräyksiä...", "Keskeytä", 0, 100)
                    self.progressDialog.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowStaysOnTopHint)
                    self.updateRegulationsAndLandUseClassificationsForSpatialFeatures("piste")
            # else:
            #     self.iface.messageBar().pushMessage("Kaavakohteita ei päivitetty", Qgis.Critical)
            if self.shouldHide:
                self.dialogUpdateRegulationOfGroup.hide()

        elif self.dialogUpdateRegulationOfGroup.checkBoxRemoveOldRegulationsFromSpatialFeatures.isChecked():
            shouldUpdateOnlyRelation = False

            if not self.dialogUpdateRegulationOfGroup.checkBoxUpdateRegulationTextsEvenIfSpatialFeatureHasMultipleRegulations.isChecked():
                shouldUpdateOnlyRelation = True

            # ainoastaan poistetaan vanha(t) kaavamääys/kaavamääräykset valituilta kohteilta
            if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPolygonFeatures.isChecked():
                if not self.hasUserSelectedPolygonFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä aluevarauksia; aluevarauksia ei päivitetty', Qgis.Warning)
                else:
                    success = self.removeRegulationsAndLandUseClassificationsFromSpatialFeatures("alue", shouldUpdateOnlyRelation)
                    if success:
                        if shouldUpdateOnlyRelation:
                            self.iface.messageBar().pushMessage('Aluvarausten kaavamääräykset poistettu', Qgis.Info, 30)
                        else:
                            self.iface.messageBar().pushMessage('Aluvarausten kaavamääräykset ja käyttötarkoitus poistettu', Qgis.Info, 30)
            if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeatures.isChecked():
                if not self.hasUserSelectedSuplementaryPolygonFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä täydentäviä aluekohteita; täydentäviä aluekohteita ei päivitetty', Qgis.Warning)
                else:
                    success = self.removeRegulationsAndLandUseClassificationsFromSpatialFeatures("alue_taydentava", shouldUpdateOnlyRelation)
                    if success:
                        if shouldUpdateOnlyRelation:
                            self.iface.messageBar().pushMessage('Täydentävien aluekohteiden kaavamääräykset poistettu', Qgis.Info, 30)
                        else:
                            self.iface.messageBar().pushMessage('Täydentävien aluekohteiden kaavamääräykset ja käyttötarkoitus poistettu', Qgis.Info, 30)
            if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForLineFeatures.isChecked():
                if not self.hasUserSelectedLineFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä viivamaisia kohteita; viivamaisia ei päivitetty', Qgis.Warning)
                else:
                    success = self.removeRegulationsAndLandUseClassificationsFromSpatialFeatures("viiva", shouldUpdateOnlyRelation)
                    if success:
                        if shouldUpdateOnlyRelation:
                            self.iface.messageBar().pushMessage('Viivamaisten kohteiden kaavamääräykset poistettu', Qgis.Info, 30)
                        else:
                            self.iface.messageBar().pushMessage('Viivamaisten kohteiden kaavamääräykset ja käyttötarkoitus poistettu', Qgis.Info, 30)
            if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPointFeatures.isChecked():
                if not self.hasUserSelectedPointFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä pistemäisiä kohteita; pistemäisiä kohteita ei päivitetty', Qgis.Warning)
                else:
                    success = self.removeRegulationsAndLandUseClassificationsFromSpatialFeatures("piste", shouldUpdateOnlyRelation)
                    if success:
                        if shouldUpdateOnlyRelation:
                            self.iface.messageBar().pushMessage('Pistemäisten kohteiden kaavamääräykset poistettu', Qgis.Info, 30)
                        else:
                            self.iface.messageBar().pushMessage('Pistemäisten kohteiden kaavamääräykset ja käyttötarkoitus poistettu', Qgis.Info, 30)

            if self.shouldHide:
                self.dialogUpdateRegulationOfGroup.hide()
            self.finishUpdate()
        else:
            self.iface.messageBar().pushMessage('Valitse kaavamääräys', Qgis.Info, 30)


    def equalsRegulationAndFormTexts(self, formRegulationTitle, formRegulationText, formRegulationDescription):
        regulationTitle = self.currentRegulation["kaavamaarays_otsikko"].value()
        regulationText = ""
        regulationDescription = ""
        if not self.currentRegulation["maaraysteksti"].isNull():
            regulationText = self.currentRegulation["maaraysteksti"].value()
        if not self.currentRegulation["kuvaus_teksti"].isNull():
            regulationDescription = self.currentRegulation["kuvaus_teksti"].value()

        if formRegulationTitle == regulationTitle and formRegulationText == regulationText and formRegulationDescription == regulationDescription:
            return True

        return False


    def finishUpdate(self):
        self.yleiskaavaUtils.refreshTargetLayersInProject()

    def reset(self):
        self.setupRegulationsInDialog()

        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPolygonFeatures.setChecked(False)
        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeatures.setChecked(False)
        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForLineFeatures.setChecked(False)
        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPointFeatures.setChecked(False)

        self.hasUserSelectedPolygonFeaturesForUpdate = False
        self.hasUserSelectedSuplementaryPolygonFeaturesForUpdate = False
        self.hasUserSelectedLineFeaturesForUpdate = False
        self.hasUserSelectedPointFeaturesForUpdate = False


    def updateRegulationsAndLandUseClassificationsForSpatialFeatures(self, featureType):
        if self.currentRegulation != None:
            regulationID = self.currentRegulation["id"]
            regulationTitle = self.currentRegulation["kaavamaarays_otsikko"]
            shouldRemoveOldRegulationRelations = self.dialogUpdateRegulationOfGroup.checkBoxRemoveOldRegulationsFromSpatialFeatures.isChecked()
            shouldUpdateOnlyRelation = False
            shouldUpdateRegulationTextsEvenIfSpatialFeatureHasMultipleRegulations = self.dialogUpdateRegulationOfGroup.checkBoxUpdateRegulationTextsEvenIfSpatialFeatureHasMultipleRegulations.isChecked()

            self.updateRegulationOfGroupTask = UpdateRegulationOfGroupTask(self.yleiskaavaDatabase, featureType, regulationID, regulationTitle, shouldRemoveOldRegulationRelations, shouldUpdateRegulationTextsEvenIfSpatialFeatureHasMultipleRegulations)

            targetLayer = self.yleiskaavaDatabase.getTargetLayer(featureType)
            regulationLayer = self.yleiskaavaDatabase.getProjectLayer("yk_yleiskaava.kaavamaarays")
            regulationRelationLayer = self.yleiskaavaDatabase.getProjectLayer("yk_yleiskaava.kaavaobjekti_kaavamaarays_yhteys")
            self.updateRegulationOfGroupTask.setDependentLayers([targetLayer, regulationLayer, regulationRelationLayer])

            self.progressDialog.canceled.connect(self.handleUpdateRegulationOfGroupTaskStopRequestedByUser)
            self.updateRegulationOfGroupTask.progressChanged.connect(self.handleUpdateRegulationOfGroupTaskProgressChanged)
            self.updateRegulationOfGroupTask.taskCompleted.connect(self.handleUpdateRegulationOfGroupTaskCompleted)
            self.updateRegulationOfGroupTask.taskTerminated.connect(self.handleUpdateRegulationOfGroupTaskTerminated)

            self.progressDialog.setValue(0)
            self.progressDialog.show()
            QgsApplication.taskManager().addTask(self.updateRegulationOfGroupTask)


    def handleUpdateRegulationOfGroupTaskStopRequestedByUser(self):
        self.hasUserCanceledCopy = True
        self.updateRegulationOfGroupTask.cancel()


    def handleUpdateRegulationOfGroupTaskProgressChanged(self, progress):
        self.progressDialog.setValue(int(progress))


    def handleUpdateRegulationOfGroupTaskCompleted(self):
        self.progressDialog.hide()
        self.finishUpdate()
        if not self.hasUserCanceledCopy:
            self.iface.messageBar().pushMessage('Valittujen kaavakohteiden kaavamääräykset päivitetty', Qgis.Info, duration=30)
        else:
            self.iface.messageBar().pushMessage('Valittujen kaavakohteiden kaavamääräyksiä ei päivitetty kokonaisuudessaan tietokantaan', Qgis.Info, duration=30)
        self.hasUserCanceledCopy = False
        #if success:
        #    self.iface.messageBar().pushMessage('Aluvarausten käyttötarkoitukset päivitetty', Qgis.Info, 30)
        #                         self.iface.messageBar().pushMessage('Täydentävien aluekohteiden käyttötarkoitukset päivitetty', Qgis.Info, 30)
        #                        self.iface.messageBar().pushMessage('Viivamaisten kohteiden käyttötarkoitukset päivitetty', Qgis.Info, 30)
        #                        self.iface.messageBar().pushMessage('Pistemäisten kohteiden käyttötarkoitukset päivitetty', Qgis.Info, 30)


    def handleUpdateRegulationOfGroupTaskTerminated(self):
        if not self.hasUserCanceledCopy:
           self.iface.messageBar().pushMessage("Kaavamääräyksen sekä kaavamaaraysteksti- ja kayttotarkoitus_lyhenne-kenttien tekstien päivityksessä tapahtui virhe", Qgis.Critical)
        else:
            self.hasUserCanceledCopy = False
        self.progressDialog.hide()
        self.finishUpdate()


    def removeRegulationsAndLandUseClassificationsFromSpatialFeatures(self, featureType, shouldUpdateOnlyRelation):
        spatialFeatures = self.yleiskaavaDatabase.getSelectedFeatures(featureType, ["id"])
        # spatialFeatures = self.yleiskaavaDatabase.getSpatialFeaturesWithRegulationForType(regulationID, featureType)

        for feature in spatialFeatures:
            success = self.yleiskaavaDatabase.removeSpatialFeatureRegulationAndLandUseClassification(feature["id"], featureType, shouldUpdateOnlyRelation)

            if not success:
                self.iface.messageBar().pushMessage("Kaavakohteelta, jonka tyyppi on " + self.yleiskaavaDatabase.getUserFriendlySpatialFeatureTypeName(featureType) + " ja id on " + str(feature["id"]) + " ei voitu poistaa kaavamääräystä eikä kaavamaaraysteksti- ja kayttotarkoitus_lyhenne-kenttien tekstejä", Qgis.Critical)

                return False

        return True


    def setupRegulationsInDialog(self):
        shouldShowOnlyUsedRegulations = False
        includeAreaRegulations = False
        includeSuplementaryAreaRegulations = False
        includeLineRegulations = False
        includePointRegulations = False
        if self.dialogUpdateRegulationOfGroup.checkBoxShowOnlyUsedRegulations.isChecked():
            shouldShowOnlyUsedRegulations = True
        if self.dialogUpdateRegulationOfGroup.checkBoxShowAreaRegulations.isChecked():
            includeAreaRegulations = True
        if self.dialogUpdateRegulationOfGroup.checkBoxShowSuplementaryAreaRegulations.isChecked():
            includeSuplementaryAreaRegulations = True
        if self.dialogUpdateRegulationOfGroup.checkBoxShowLineRegulations.isChecked():
            includeLineRegulations = True
        if self.dialogUpdateRegulationOfGroup.checkBoxShowPointRegulations.isChecked():
            includePointRegulations = True

        self.regulations = sorted(self.yleiskaavaDatabase.getSpecificRegulations(shouldShowOnlyUsedRegulations, includeAreaRegulations, includeSuplementaryAreaRegulations, includeLineRegulations, includePointRegulations), key=itemgetter('alpha_sort_key'))
        self.regulationTitles = []
        for index, regulation in enumerate(self.regulations):
            #QgsMessageLog.logMessage("setupRegulationsInDialog - index: " + str(index) + ", regulation['kaavamaarays_otsikko']: " + str(regulation['kaavamaarays_otsikko'].value()) + ", regulation['maaraysteksti']: " + str(regulation['maaraysteksti'].value()) + ", regulation['kuvaus_teksti']: " + str(regulation['kuvaus_teksti'].value()), 'Yleiskaava-työkalu', Qgis.Info)
            # QgsMessageLog.logMessage("setupRegulationsInDialog - index: " + str(index) + ", regulation['kaavamaarays_otsikko']: " + str(regulation['kaavamaarays_otsikko'].value()), 'Yleiskaava-työkalu', Qgis.Info)
            self.regulationTitles.append(regulation["kaavamaarays_otsikko"].value())
        self.dialogUpdateRegulationOfGroup.comboBoxRegulationTitles.clear()
        self.dialogUpdateRegulationOfGroup.comboBoxRegulationTitles.addItems(self.regulationTitles)

        self.dialogUpdateRegulationOfGroup.comboBoxRegulationTitles.insertItem(0, "Valitse kaavamääräys")
        self.dialogUpdateRegulationOfGroup.comboBoxRegulationTitles.setCurrentIndex(0)
        self.currentRegulation = None

    
    def handleComboBoxRegulationTitleChanged(self, currentIndex):
        # QgsMessageLog.logMessage("handleComboBoxRegulationTitleChanged - currentIndex: " + str(currentIndex) + ", len(self.regulations): " + str(len(self.regulations)), 'Yleiskaava-työkalu', Qgis.Info)
        if currentIndex > 0 and self.regulations is not None and len(self.regulations) >= (currentIndex - 1):
            self.currentRegulation = self.regulations[currentIndex - 1]

            self.dialogUpdateRegulationOfGroup.plainTextEditRegulationTitle.setPlainText(self.currentRegulation["kaavamaarays_otsikko"].value())
            if not self.currentRegulation["maaraysteksti"].isNull():
                self.dialogUpdateRegulationOfGroup.plainTextEditRegulationText.setPlainText(self.currentRegulation["maaraysteksti"].value())
            else:
                self.dialogUpdateRegulationOfGroup.plainTextEditRegulationText.setPlainText("")
            if not self.currentRegulation["kuvaus_teksti"].isNull():
                self.dialogUpdateRegulationOfGroup.plainTextEditRegulationDescription.setPlainText(self.currentRegulation["kuvaus_teksti"].value())
            else:
                self.dialogUpdateRegulationOfGroup.plainTextEditRegulationDescription.setPlainText("")
        else:
            self.currentRegulation = None
            self.dialogUpdateRegulationOfGroup.plainTextEditRegulationTitle.setPlainText("")
            self.dialogUpdateRegulationOfGroup.plainTextEditRegulationText.setPlainText("")
            self.dialogUpdateRegulationOfGroup.plainTextEditRegulationDescription.setPlainText("")


    def checkBoxShowOnlyUsedRegulationsStateChanged(self):
        self.setupRegulationsInDialog()

            
    def checkBoxShowAreaRegulationsStateChanged(self):
        self.setupRegulationsInDialog()

    def checkBoxShowSuplementaryAreaRegulationsStateChanged(self):
        self.setupRegulationsInDialog()
   
    def checkBoxShowLineRegulationsStateChanged(self):
        self.setupRegulationsInDialog()

    def checkBoxShowPointRegulationsStateChanged(self):
        self.setupRegulationsInDialog()
