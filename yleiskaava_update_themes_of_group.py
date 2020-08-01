

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtWidgets import QProgressDialog

from qgis.core import (Qgis, QgsProject, QgsMessageLog, QgsApplication)

import os.path
import uuid
from operator import itemgetter

from .yleiskaava_database import YleiskaavaDatabase
from .yleiskaava_update_themes_of_group_task import UpdateThemesOfGroupTask


class UpdateThemesOfGroup:

    def __init__(self, iface, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = os.path.dirname(__file__)

        self.dialogUpdateThemeOfGroup = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_update_themes_of_group.ui'))
        self.dialogUpdateThemeOfGroup.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)

        self.themes = None
        self.themeNames = None

        self.currentTheme = None

        self.hasUserSelectedPolygonFeaturesForUpdate = False
        self.hasUserSelectedSuplementaryPolygonFeaturesForUpdate = False
        self.hasUserSelectedLineFeaturesForUpdate = False
        self.hasUserSelectedPointFeaturesForUpdate = False

        self.hasUserCanceledCopy = False
        self.progressDialog = None
        self.shouldHide = False

    def setup(self):
        self.setupDialogUpdateThemeOfGroup()


    def setupDialogUpdateThemeOfGroup(self):

        self.dialogUpdateThemeOfGroup.comboBoxThemeNames.currentIndexChanged.connect(self.handleComboBoxThemeNameChanged)

        self.dialogUpdateThemeOfGroup.checkBoxUpdatePolygonFeatures.stateChanged.connect(self.checkBoxUpdatePolygonFeaturesStateChanged)
        self.dialogUpdateThemeOfGroup.checkBoxUpdateSupplementaryPolygonFeatures.stateChanged.connect(self.checkBoxUpdateSupplementaryPolygonFeaturesStateChanged)
        self.dialogUpdateThemeOfGroup.checkBoxUpdateLineFeatures.stateChanged.connect(self.checkBoxUpdateLineFeaturesStateChanged)
        self.dialogUpdateThemeOfGroup.checkBoxUpdatePointFeatures.stateChanged.connect(self.checkBoxUpdatePointFeaturesStateChanged)

        # Varoita käyttäjää, jos jo valmiiksi valittuja kohteita
        self.dialogUpdateThemeOfGroup.pushButtonSelectPolygonFeatures.clicked.connect(self.selectPolygonFeatures)
        self.dialogUpdateThemeOfGroup.pushButtonSelectSupplementaryPolygonFeatures.clicked.connect(self.selectSupplementaryPolygonFeatures)
        self.dialogUpdateThemeOfGroup.pushButtonSelectLineFeatures.clicked.connect(self.selectLineFeatures)
        self.dialogUpdateThemeOfGroup.pushButtonSelectPointFeatures.clicked.connect(self.selectPointFeatures)

        self.dialogUpdateThemeOfGroup.pushButtonUpdate.clicked.connect(self.handleUpdateTheme)
        self.dialogUpdateThemeOfGroup.pushButtonUpdateAndClose.clicked.connect(self.handleUpdateThemeAndClose)

        self.dialogUpdateThemeOfGroup.pushButtonCancel.clicked.connect(self.dialogUpdateThemeOfGroup.hide)


    def selectPolygonFeatures(self):
        layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE)[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Aluevaraukset karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedPolygonFeaturesForUpdate = True

        self.dialogUpdateThemeOfGroup.checkBoxUpdatePolygonFeatures.setChecked(True)


    def selectSupplementaryPolygonFeatures(self):
        layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA)[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Täydentävät aluekohteet  karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedSuplementaryPolygonFeaturesForUpdate = True

        self.dialogUpdateThemeOfGroup.checkBoxUpdateSupplementaryPolygonFeatures.setChecked(True)


    def selectLineFeatures(self):
        layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA)[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Viivamaiset kaavakohteet karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedLineFeaturesForUpdate = True

        self.dialogUpdateThemeOfGroup.checkBoxUpdateLineFeatures.setChecked(True)


    def selectPointFeatures(self):
        layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_PISTE)[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Pistemäiset kaavakohteet karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedPointFeaturesForUpdate = True

        self.dialogUpdateThemeOfGroup.checkBoxUpdatePointFeatures.setChecked(True)


    def checkBoxUpdatePolygonFeaturesStateChanged(self):
        pass
        # if self.dialogUpdateThemeOfGroup.checkBoxUpdatePolygonFeatures.isChecked():
        #     self.dialogUpdateThemeOfGroup.pushButtonSelectPolygonFeatures.setEnabled(True)
        # else:
        #     self.dialogUpdateThemeOfGroup.pushButtonSelectPolygonFeatures.setEnabled(False)

    def checkBoxUpdateSupplementaryPolygonFeaturesStateChanged(self):
        pass
        # if self.dialogUpdateThemeOfGroup.checkBoxUpdateSupplementaryPolygonFeatures.isChecked():
        #     self.dialogUpdateThemeOfGroup.pushButtonSelectSupplementaryPolygonFeatures.setEnabled(True)
        # else:
        #     self.dialogUpdateThemeOfGroup.pushButtonSelectSupplementaryPolygonFeatures.setEnabled(False)

    def checkBoxUpdateLineFeaturesStateChanged(self):
        pass
        # if self.dialogUpdateThemeOfGroup.checkBoxUpdateLineFeatures.isChecked():
        #     self.dialogUpdateThemeOfGroup.pushButtonSelectLineFeatures.setEnabled(True)
        # else:
        #     self.dialogUpdateThemeOfGroup.pushButtonSelectLineFeatures.setEnabled(False)

    def checkBoxUpdatePointFeaturesStateChanged(self):
        pass
        # if self.dialogUpdateThemeOfGroup.checkBoxUpdatePointFeatures.isChecked():
        #     self.dialogUpdateThemeOfGroup.pushButtonSelectPointFeatures.setEnabled(True)
        # else:
        #     self.dialogUpdateThemeOfGroup.pushButtonSelectPointFeatures.setEnabled(False)


    def openDialogUpdateThemeForGroup(self):
        self.reset()
        self.dialogUpdateThemeOfGroup.show()


    def handleUpdateTheme(self):
        self.shouldHide = False
        self.updateTheme()

    def handleUpdateThemeAndClose(self):
        self.shouldHide = True
        self.updateTheme()
        
    
    def updateTheme(self):
        # Päivitä teema ja siihen liitetyt kaavakohteet ja huomio asetukset, sekä mahd. useat teemat kohteella
        # Tarkista, onko teeman lomaketiedoissa eroa ja jos ei, niin ilmoita käyttäjälle.
        # Lisää teema sellaisille kaavakohteille, joilla sitä ei vielä ole, mutta käyttäjä on ko. kaavakohteen valinnut / valitsee
        # Anna käyttäjän valita kaavakohteet, joille teema päivitetään.
        # Varmista, että käyttäjä ei voi vahingossa päivittää jo aiemmin valitsemiaan kaavaobjekteja.
        # Varmista jotenkin, että käyttäjän valitsemat kohteet päivitetään vaikka niillä olisi eri teema kuin muutettava teema / rajoita valintamahdollisuus kohteisiin, joilla muutettavan teeman relaatio
        # Ilmoita käyttäjälle, että valitse kohteet, tms., jos ei ole valinnut.
        # Varmista, että self.currentTheme != None jo vaikka käyttäjä ei ole valinnut dialogista kohteita / lisää ensimmäiseksi vaihtoehdoksi comboboxiin "Valitse teema"
        # Huomioi, "Poista kaavakohteilta vanhat teemat"-asetuksen pois päältä olo, kun käyttäjä vain päivittää kohteilla jo olevaa teemaa -> ei siis tehdä duplikaattirelaatiota
        # näytä käyttöliittymässä yleiskaavan id, nimi, nro
        if self.currentTheme != None:
            themeID = self.currentTheme["id"]
            themeName = self.dialogUpdateThemeOfGroup.lineEditThemeName.text()
            themeDescription = self.dialogUpdateThemeOfGroup.plainTextEditThemeDescription.toPlainText()

            if not self.equalsThemeAndFormTexts(themeName, themeDescription):
                success = self.yleiskaavaDatabase.updateTheme(themeID, themeName, themeDescription)

                if success:
                    self.currentTheme["alpha_sort_key"] = themeName
                    self.currentTheme["nimi"] = QVariant(themeName)
                    self.currentTheme["kuvaus"] = QVariant(themeDescription)
                    # self.currentTheme["id_yleiskaava"] = QVariant(themeDescription)

                    self.iface.messageBar().pushMessage('Teema päivitetty', Qgis.Info, 30)
            elif not self.dialogUpdateThemeOfGroup.checkBoxUpdatePolygonFeatures.isChecked() and not self.dialogUpdateThemeOfGroup.checkBoxUpdateSupplementaryPolygonFeatures.isChecked() and not self.dialogUpdateThemeOfGroup.checkBoxUpdateLineFeatures.isChecked() and not self.dialogUpdateThemeOfGroup.checkBoxUpdatePointFeatures.isChecked():
                self.iface.messageBar().pushMessage('Teemaan ei ole tehty muutoksia eikä päivitettäviä kaavakohteita ole valittu. Ei tehdä päivityksiä', Qgis.Info, 30)

            if self.dialogUpdateThemeOfGroup.checkBoxUpdatePolygonFeatures.isChecked():
                if not self.hasUserSelectedPolygonFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä aluevarauksia; aluevarauksia ei päivitetty', Qgis.Warning)
                else:
                    self.progressDialog = QProgressDialog("Päivitetään aluevarausten teemoja...", "Keskeytä", 0, 100)
                    self.progressDialog.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowStaysOnTopHint)
                    self.updateSpatialFeatures("alue")
            if self.dialogUpdateThemeOfGroup.checkBoxUpdateSupplementaryPolygonFeatures.isChecked():
                if not self.hasUserSelectedSuplementaryPolygonFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä täydentäviä aluekohteita; täydentäviä aluekohteita ei päivitetty', Qgis.Warning)
                else:
                    self.progressDialog = QProgressDialog("Päivitetään täydentävien aluekohteiden teemoja...", "Keskeytä", 0, 100)
                    self.progressDialog.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowStaysOnTopHint)
                    self.updateSpatialFeatures("alue_taydentava")
            if self.dialogUpdateThemeOfGroup.checkBoxUpdateLineFeatures.isChecked():
                if not self.hasUserSelectedLineFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä viivamaisia kohteita; viivamaisia ei päivitetty', Qgis.Warning)
                else:
                    self.progressDialog = QProgressDialog("Päivitetään viivamaisten kohteiden teemoja...", "Keskeytä", 0, 100)
                    self.progressDialog.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowStaysOnTopHint)
                    self.updateSpatialFeatures("viiva")
            if self.dialogUpdateThemeOfGroup.checkBoxUpdatePointFeatures.isChecked():
                if not self.hasUserSelectedPointFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä pistemäisiä kohteita; pistemäisiä kohteita ei päivitetty', Qgis.Warning)
                else:
                    self.progressDialog = QProgressDialog("Päivitetään pistemäisten kohteiden teemoja...", "Keskeytä", 0, 100)
                    self.progressDialog.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowStaysOnTopHint)
                    self.updateSpatialFeatures("piste")

            if self.shouldHide:
                self.dialogUpdateThemeOfGroup.hide()

            # else:
            #     self.iface.messageBar().pushMessage("Kaavakohteita ei päivitetty", Qgis.Critical)

            
        elif self.dialogUpdateThemeOfGroup.checkBoxRemoveOldThemesFromSpatialFeatures.isChecked():
            # ainoastaan poistetaan vanha(t) teema(t) valituilta kohteilta
            if self.dialogUpdateThemeOfGroup.checkBoxUpdatePolygonFeatures.isChecked():
                if not self.hasUserSelectedPolygonFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä aluevarauksia; aluevarauksia ei päivitetty', Qgis.Warning)
                else:
                    success = self.removeThemesFromSpatialFeatures("alue")
                    if success:
                        self.iface.messageBar().pushMessage('Aluvarausten teemat poistettu', Qgis.Info, 30)
            if self.dialogUpdateThemeOfGroup.checkBoxUpdateSupplementaryPolygonFeatures.isChecked():
                if not self.hasUserSelectedSuplementaryPolygonFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä täydentäviä aluekohteita; täydentäviä aluekohteita ei päivitetty', Qgis.Warning)
                else:
                    success = self.removeThemesFromSpatialFeatures("alue_taydentava")
                    if success:
                        self.iface.messageBar().pushMessage('Täydentävien aluekohteiden teemat poistettu', Qgis.Info, 30)
            if self.dialogUpdateThemeOfGroup.checkBoxUpdateLineFeatures.isChecked():
                if not self.hasUserSelectedLineFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä viivamaisia kohteita; viivamaisia ei päivitetty', Qgis.Warning)
                else:
                    success = self.removeThemesFromSpatialFeatures("viiva")
                    if success:
                        self.iface.messageBar().pushMessage('Viivamaisten kohteiden teemat poistettu', Qgis.Info, 30)
            if self.dialogUpdateThemeOfGroup.checkBoxUpdatePointFeatures.isChecked():
                if not self.hasUserSelectedPointFeaturesForUpdate:
                    self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä pistemäisiä kohteita; pistemäisiä kohteita ei päivitetty', Qgis.Warning)
                else:
                    success = self.removeThemesFromSpatialFeatures("piste")
                    if success:
                        self.iface.messageBar().pushMessage('Pistemäisten kohteiden teemat poistettu', Qgis.Info, 30)

            if self.shouldHide:
                self.dialogUpdateThemeOfGroup.hide()
            self.finishUpdate()
        else:
            self.iface.messageBar().pushMessage('Valitse teema', Qgis.Info, 30)


    def equalsThemeAndFormTexts(self, formThemeName, formThemeDescription):
        themeName = self.currentTheme["nimi"].value()
        themeDescription = ""
        if not self.currentTheme["kuvaus"].isNull():
            themeDescription = self.currentTheme["kuvaus"].value()

        if formThemeName == themeName and formThemeDescription == themeDescription:
            return True

        return False


    def finishUpdate(self):
        self.yleiskaavaUtils.refreshTargetLayersInProject()


    def reset(self):
        self.setupThemesInDialog()

        self.dialogUpdateThemeOfGroup.checkBoxUpdatePolygonFeatures.setChecked(False)
        self.dialogUpdateThemeOfGroup.checkBoxUpdateSupplementaryPolygonFeatures.setChecked(False)
        self.dialogUpdateThemeOfGroup.checkBoxUpdateLineFeatures.setChecked(False)
        self.dialogUpdateThemeOfGroup.checkBoxUpdatePointFeatures.setChecked(False)

        self.hasUserSelectedPolygonFeaturesForUpdate = False
        self.hasUserSelectedSuplementaryPolygonFeaturesForUpdate = False
        self.hasUserSelectedLineFeaturesForUpdate = False
        self.hasUserSelectedPointFeaturesForUpdate = False


    def updateSpatialFeatures(self, featureType):
        if self.currentTheme != None:
            themeID = self.currentTheme["id"]
            themeName = self.currentTheme["nimi"]
            shouldRemoveOldThemeRelations = self.dialogUpdateThemeOfGroup.checkBoxRemoveOldThemesFromSpatialFeatures.isChecked()

            self.updateThemesOfGroupTask = UpdateThemesOfGroupTask(self.yleiskaavaDatabase, featureType, themeID, themeName, shouldRemoveOldThemeRelations)

            targetLayer = self.yleiskaavaDatabase.getTargetLayer(featureType)
            themeLayer = self.yleiskaavaDatabase.getProjectLayer("yk_kuvaustekniikka.teema")
            themeRelationLayer = self.yleiskaavaDatabase.getProjectLayer("yk_kuvaustekniikka.kaavaobjekti_teema_yhteys")
            self.updateThemesOfGroupTask.setDependentLayers([targetLayer, themeLayer, themeRelationLayer])

            self.progressDialog.canceled.connect(self.handleUpdateThemesOfGroupTaskStopRequestedByUser)
            self.updateThemesOfGroupTask.progressChanged.connect(self.handleUpdateThemesOfGroupTaskProgressChanged)
            self.updateThemesOfGroupTask.taskCompleted.connect(self.handleUpdateThemesOfGroupTaskCompleted)
            self.updateThemesOfGroupTask.taskTerminated.connect(self.handleUpdateThemesOfGroupTaskTerminated)

            self.progressDialog.setValue(0)
            self.progressDialog.show()
            QgsApplication.taskManager().addTask(self.updateThemesOfGroupTask)


    def handleUpdateThemesOfGroupTaskStopRequestedByUser(self):
        self.hasUserCanceledCopy = True
        self.updateThemesOfGroupTask.cancel()


    def handleUpdateThemesOfGroupTaskProgressChanged(self, progress):
        self.progressDialog.setValue(int(progress))


    def handleUpdateThemesOfGroupTaskCompleted(self):
        self.progressDialog.hide()
        self.finishUpdate()
        if not self.hasUserCanceledCopy:
            self.iface.messageBar().pushMessage('Valittujen kaavakohteiden teemat päivitetty', Qgis.Info, duration=30)
        else:
            self.iface.messageBar().pushMessage('Valittujen kaavakohteiden teemoja ei päivitetty kokonaisuudessaan tietokantaan', Qgis.Info, duration=30)
        self.hasUserCanceledCopy = False


    def handleUpdateThemesOfGroupTaskTerminated(self):
        if not self.hasUserCanceledCopy:
           self.iface.messageBar().pushMessage("Teemojen päivityksessä tapahtui virhe", Qgis.Critical)
        else:
            self.hasUserCanceledCopy = False
        self.progressDialog.hide()
        self.finishUpdate()


    def removeThemesFromSpatialFeatures(self, featureType):
        spatialFeatures = self.yleiskaavaDatabase.getSelectedFeatures(featureType, ["id"])
        # spatialFeatures = self.yleiskaavaDatabase.getSpatialFeaturesWithRegulationForType(regulationID, featureType)

        for feature in spatialFeatures:
            success = self.yleiskaavaDatabase.removeSpatialFeatureThemes(feature["id"], featureType)

            if not success:
                self.iface.messageBar().pushMessage("Kaavakohteelta, jonka tyyppi on " + self.yleiskaavaDatabase.getUserFriendlySpatialFeatureTypeName(featureType) + " ja id on " + str(feature["id"]) + " ei voitu poistaa teemoja", Qgis.Critical)

                return False

        return True


    def setupThemesInDialog(self):
        self.themes = sorted(self.yleiskaavaDatabase.getThemes(), key=itemgetter('alpha_sort_key'))
        self.themeNames = []
        for index, theme in enumerate(self.themes):
            #QgsMessageLog.logMessage("setupThemesInDialog - index: " + str(index) + ", theme['kaavamaarays_otsikko']: " + str(theme['kaavamaarays_otsikko'].value()) + ", theme['maaraysteksti']: " + str(theme['maaraysteksti'].value()) + ", theme['kuvaus_teksti']: " + str(theme['kuvaus_teksti'].value()), 'Yleiskaava-työkalu', Qgis.Info)
            # QgsMessageLog.logMessage("setupThemesInDialog - index: " + str(index) + ", theme['kaavamaarays_otsikko']: " + str(theme['kaavamaarays_otsikko'].value()), 'Yleiskaava-työkalu', Qgis.Info)
            kuvaus = (theme["kuvaus"].value()[:25] + '..') if len(theme["kuvaus"].value()) > 25 else theme["kuvaus"].value()
            self.themeNames.append(theme["nimi"].value() + ' - ' + kuvaus)
        self.dialogUpdateThemeOfGroup.comboBoxThemeNames.clear()
        self.dialogUpdateThemeOfGroup.comboBoxThemeNames.addItems(self.themeNames)

        self.dialogUpdateThemeOfGroup.comboBoxThemeNames.insertItem(0, "Valitse teema")
        self.dialogUpdateThemeOfGroup.comboBoxThemeNames.setCurrentIndex(0)
        self.currentTheme = None


    def handleComboBoxThemeNameChanged(self, currentIndex):
        self.currentTheme = self.themes[currentIndex - 1]

        if currentIndex > 0:
            self.dialogUpdateThemeOfGroup.lineEditThemeName.setText(self.currentTheme["nimi"].value())
            if not self.currentTheme["kuvaus"].isNull():
                self.dialogUpdateThemeOfGroup.plainTextEditThemeDescription.setPlainText(self.currentTheme["kuvaus"].value())
            else:
                self.dialogUpdateThemeOfGroup.plainTextEditThemeDescription.setPlainText("")
            if not self.currentTheme["yleiskaava_nimi"].isNull():
                self.dialogUpdateThemeOfGroup.lineEditPlanName.setText(self.currentTheme["yleiskaava_nimi"].value())
            else:
                self.dialogUpdateThemeOfGroup.lineEditPlanName.setText("")
        else:
            self.currentTheme = None
            self.dialogUpdateThemeOfGroup.lineEditThemeName.setText("")
            self.dialogUpdateThemeOfGroup.plainTextEditThemeDescription.setPlainText("")
            self.dialogUpdateThemeOfGroup.lineEditPlanName.setText("")