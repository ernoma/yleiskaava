

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QVariant

from qgis.core import (Qgis, QgsProject, QgsMessageLog)

import os.path
import uuid
from operator import itemgetter

class UpdateRegulationOfGroup:


    def __init__(self, iface, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = os.path.dirname(__file__)

        self.dialogUpdateRegulationOfGroup = uic.loadUi(os.path.join(self.plugin_dir, 'yleiskaava_dialog_update_regulation_of_group.ui'))

        self.regulations = None
        self.regulationTitles = None

        self.currentRegulation = None

        self.hasUserSelectedPolgyonFeaturesForUpdate = False
        self.hasUserSelectedSuplementaryPolgyonFeaturesForUpdate = False
        self.hasUserSelectedLineFeaturesForUpdate = False
        self.hasUserSelectedPointFeaturesForUpdate = False

    def setup(self):
        self.setupDialogUpdateRegulationOfGroup()


    def setupDialogUpdateRegulationOfGroup(self):

        #self.setupRegulationsInDialog()

        self.dialogUpdateRegulationOfGroup.comboBoxRegulationTitles.currentIndexChanged.connect(self.handleComboBoxRegulationTitleChanged)

        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPolgyonFeatures.stateChanged.connect(self.checkBoxUpdateLandUseClassificationsForPolgyonFeaturesStateChanged)
        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeatures.stateChanged.connect(self.checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeaturesStateChanged)
        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForLineFeatures.stateChanged.connect(self.checkBoxUpdateLandUseClassificationsForLineFeaturesStateChanged)
        self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPointFeatures.stateChanged.connect(self.checkBoxUpdateLandUseClassificationsForPointFeaturesStateChanged)

        # Varoita käyttäjää, jos jo valmiiksi valittuja kohteita
        self.dialogUpdateRegulationOfGroup.pushButtonSelectPolgyonFeatures.clicked.connect(self.selectPolgyonFeatures)
        self.dialogUpdateRegulationOfGroup.pushButtonSelectSupplementaryPolygonFeatures.clicked.connect(self.selectSupplementaryPolygonFeatures)
        self.dialogUpdateRegulationOfGroup.pushButtonSelectLineFeatures.clicked.connect(self.selectLineFeatures)
        self.dialogUpdateRegulationOfGroup.pushButtonSelectPointFeatures.clicked.connect(self.selectPointFeatures)

        self.dialogUpdateRegulationOfGroup.pushButtonUpdateRegulationAndSpatialFeatures.clicked.connect(self.handleUpdateRegulation)

        self.dialogUpdateRegulationOfGroup.pushButtonCancel.clicked.connect(self.dialogUpdateRegulationOfGroup.hide)
    

    def selectPolgyonFeatures(self):
        layer = QgsProject.instance().mapLayersByName("Aluevaraukset")[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Aluevaraukset karttatasolla oli jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedPolgyonFeaturesForUpdate = True

    def selectSupplementaryPolygonFeatures(self):
        layer = QgsProject.instance().mapLayersByName("Täydentävät aluekohteet (osa-alueet)")[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Täydentävät aluekohteet  karttatasolla oli jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedSuplementaryPolgyonFeaturesForUpdate = True

    def selectLineFeatures(self):
        layer = QgsProject.instance().mapLayersByName("Viivamaiset kaavakohteet")[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Viivamaiset kaavakohteet karttatasolla oli jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedLineFeaturesForUpdate = True

    def selectPointFeatures(self):
        layer = QgsProject.instance().mapLayersByName("Pistemäiset kaavakohteet")[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Pistemäiset kaavakohteet karttatasolla oli jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedPointFeaturesForUpdate = True


    def checkBoxUpdateLandUseClassificationsForPolgyonFeaturesStateChanged(self):
        if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPolgyonFeatures.isChecked():
            self.dialogUpdateRegulationOfGroup.pushButtonSelectPolgyonFeatures.setEnabled(True)
        else:
            self.dialogUpdateRegulationOfGroup.pushButtonSelectPolgyonFeatures.setEnabled(False)

    def checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeaturesStateChanged(self):
        if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeatures.isChecked():
            self.dialogUpdateRegulationOfGroup.pushButtonSelectSupplementaryPolygonFeatures.setEnabled(True)
        else:
            self.dialogUpdateRegulationOfGroup.pushButtonSelectSupplementaryPolygonFeatures.setEnabled(False)

    def checkBoxUpdateLandUseClassificationsForLineFeaturesStateChanged(self):
        if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForLineFeatures.isChecked():
            self.dialogUpdateRegulationOfGroup.pushButtonSelectLineFeatures.setEnabled(True)
        else:
            self.dialogUpdateRegulationOfGroup.pushButtonSelectLineFeatures.setEnabled(False)

    def checkBoxUpdateLandUseClassificationsForPointFeaturesStateChanged(self):
        if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPointFeatures.isChecked():
            self.dialogUpdateRegulationOfGroup.pushButtonSelectPointFeatures.setEnabled(True)
        else:
            self.dialogUpdateRegulationOfGroup.pushButtonSelectPointFeatures.setEnabled(False)


    def openDialogUpdateRegulationOfGroup(self):
        self.reset()
        self.dialogUpdateRegulationOfGroup.show()


    def handleUpdateRegulation(self):
        # Päivitä kaavamääräys ja siihen liitetyt kaavakohteet ja huomio asetukset, sekä mahd. useat määräykset kohteella kayttotarkoitus_lyhenne-päivityksessä.
        # Tarkista, onko kaavamääräyksen lomaketiedoissa eroa ja jos ei, niin ilmoita käyttäjälle.
        # TODO kokonaan uusien kaavamääräysten tuki
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
            elif not self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPolgyonFeatures.isChecked() and not self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeatures.isChecked() and not self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForLineFeatures.isChecked() and not self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPointFeatures.isChecked():
                self.iface.messageBar().pushMessage('Kaavamääräykseen ei ole tehty muutoksia eikä päivitettäviä kaavakohteita ole valittu. Ei tehdä päivityksiä', Qgis.Info, 30)

            if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPolgyonFeatures.isChecked():
                if not self.hasUserSelectedPolgyonFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä aluevarauksia; aluevarauksia ei päivitetty', Qgis.Warning)
                else:
                    success = self.updateRegulationsAndLandUseClassificationsForSpatialFeatures("alue")
                    if success:
                        self.iface.messageBar().pushMessage('Aluvarausten käyttötarkoitukset päivitetty', Qgis.Info, 30)
            if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForSupplementaryPolygonFeatures.isChecked():
                if not self.hasUserSelectedSuplementaryPolgyonFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä täydentäviä aluekohteita; täydentäviä aluekohteita ei päivitetty', Qgis.Warning)
                else:
                    success = self.updateRegulationsAndLandUseClassificationsForSpatialFeatures("alue_taydentava")
                    if success:
                        self.iface.messageBar().pushMessage('Täydentävien aluekohteiden käyttötarkoitukset päivitetty', Qgis.Info, 30)
            if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForLineFeatures.isChecked():
                if not self.hasUserSelectedLineFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä viivamaisia kohteita; viivamaisia ei päivitetty', Qgis.Warning)
                else:
                    success = self.updateRegulationsAndLandUseClassificationsForSpatialFeatures("viiva")
                    if success:
                        self.iface.messageBar().pushMessage('Viivamaisten kohteiden käyttötarkoitukset päivitetty', Qgis.Info, 30)
            if self.dialogUpdateRegulationOfGroup.checkBoxUpdateLandUseClassificationsForPointFeatures.isChecked():
                if not self.hasUserSelectedPointFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä pistemäisiä kohteita; pistemäisiä kohteita ei päivitetty', Qgis.Warning)
                else:
                    success = self.updateRegulationsAndLandUseClassificationsForSpatialFeatures("piste")
                    if success:
                        self.iface.messageBar().pushMessage('Pistemäisten kohteiden käyttötarkoitukset päivitetty', Qgis.Info, 30)

            # else:
            #     self.iface.messageBar().pushMessage("Kaavakohteita ei päivitetty", Qgis.Critical)

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
        self.reset()

        self.yleiskaavaUtils.refreshTargetLayersInProject()

        self.dialogUpdateRegulationOfGroup.hide()


    def reset(self):
        self.setupRegulationsInDialog()

        self.hasUserSelectedPolgyonFeaturesForUpdate = False
        self.hasUserSelectedSuplementaryPolgyonFeaturesForUpdate = False
        self.hasUserSelectedLineFeaturesForUpdate = False
        self.hasUserSelectedPointFeaturesForUpdate = False


    def updateRegulationsAndLandUseClassificationsForSpatialFeatures(self, featureType):
        if self.currentRegulation != None:
            regulationID = self.currentRegulation["id"]

            spatialFeatures = self.getSelectedFeatures(featureType)
            # spatialFeatures = self.yleiskaavaDatabase.getSpatialFeaturesWithRegulationForType(regulationID, featureType)

            for feature in spatialFeatures:
                regulationCount = self.yleiskaavaDatabase.getRegulationCountForSpatialFeature(feature["id"], featureType)

                # QgsMessageLog.logMessage("updateRegulationsAndLandUseClassificationsForSpatialFeatures - feature['feature']['kaavammaraysotsikko']: " + feature['feature']['kaavammaraysotsikko'] + ", regulationCount for feature: " + str(regulationCount), 'Yleiskaava-työkalu', Qgis.Info)

                shouldRemoveOldRegulationRelations = self.dialogUpdateRegulationOfGroup.checkBoxRemoveOldRegulationsFromSpatialFeatures.isChecked()
                shouldUpdateOnlyRelation = False

                if regulationCount >= 1 and not self.dialogUpdateRegulationOfGroup.checkBoxUpdateRegulationTextsEvenIfSpatialFeatureHasMultipleRegulations.isChecked() and not shouldRemoveOldRegulationRelations:
                    shouldUpdateOnlyRelation = True
                
                success = self.yleiskaavaDatabase.updateSpatialFeatureRegulationAndLandUseClassification(feature["id"], featureType, regulationID, self.currentRegulation["kaavamaarays_otsikko"], shouldRemoveOldRegulationRelations, shouldUpdateOnlyRelation)

                if not success:
                    self.iface.messageBar().pushMessage("Kaavakohteelle, jonka id on " + str(feature["id"]) + " ei voitu päivittää kaavamääräystä, kaavamaaraysteksti- ja kayttotarkoitus_lyhenne-kenttien tekstejä", Qgis.Critical)

                    return False

        return True


    def getSelectedFeatures(self, featureType):
        layer = None

        if featureType == "alue":
            layer = QgsProject.instance().mapLayersByName("Aluevaraukset")[0]
        elif featureType == "alue_taydentava":
            layer = QgsProject.instance().mapLayersByName("Täydentävät aluekohteet (osa-alueet)")[0]
        elif featureType == "viiva":
            layer = QgsProject.instance().mapLayersByName("Viivamaiset kaavakohteet")[0]
        elif featureType == "piste":
            layer = QgsProject.instance().mapLayersByName("Pistemäiset kaavakohteet")[0]

        # QgsMessageLog.logMessage("getSelectedFeatures - layer.selectedFeatureCount(): " + str(layer.selectedFeatureCount()), 'Yleiskaava-työkalu', Qgis.Info)

        return layer.getSelectedFeatures()


    def setupRegulationsInDialog(self):
        self.regulations = sorted(self.yleiskaavaDatabase.getSpecificRegulations(), key=itemgetter('alpha_sort_key'))
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
        self.currentRegulation = self.regulations[currentIndex - 1]

        if currentIndex > 0:
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
