
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QVariant, QSize
from qgis.PyQt.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox, QCheckBox, QSizePolicy

from qgis.core import (Qgis, QgsProject, QgsMessageLog)

import os.path
from functools import partial

from .yleiskaava_database import YleiskaavaDatabase


class ChangeFieldValuesOfGroup:

    FIELD_USER_FRIENDLY_NAME_INDEX = 0
    FIELD_NAME_INDEX = 1
    FIELD_TYPE_NAME_INDEX = 2
    FIELD_VALUE_INDEX = 3
    FIELD_SHOULD_UPDATE_CHOICE_INDEX = 4


    CHOOSE_AND_UPDATE_VALUES_DIALOG_MIN_WIDTH = 1358
    CHOOSE_AND_UPDATE_VALUES_MIN_HEIGHT = 1088


    def __init__(self, iface, plugin_dir, yleiskaavaSettings, yleiskaavaDatabase, yleiskaavaUtils):
        
        self.iface = iface

        self.yleiskaavaSettings = yleiskaavaSettings
        self.yleiskaavaDatabase = yleiskaavaDatabase
        self.yleiskaavaUtils = yleiskaavaUtils

        self.plugin_dir = plugin_dir

        self.dialogChangeFieldValuesOfGroup = uic.loadUi(os.path.join(self.plugin_dir, 'ui','yleiskaava_dialog_change_field_values_of_group.ui'))

        self.dialogChooseAndUpdateFieldValuesForFeatureType = uic.loadUi(os.path.join(self.plugin_dir, 'ui', 'yleiskaava_dialog_choose_and_update_field_values_for_feature_type.ui'))
        
        self.hasUserSelectedPolygonFeaturesForUpdate = False
        self.hasUserSelectedSuplementaryPolygonFeaturesForUpdate = False
        self.hasUserSelectedLineFeaturesForUpdate = False
        self.hasUserSelectedPointFeaturesForUpdate = False

        self.shownFieldNamesAndTypes = []

        self.currentFeatureType = None


    def setup(self):
        # Varoita käyttäjää, jos jo valmiiksi valittuja kohteita
        self.dialogChangeFieldValuesOfGroup.pushButtonSelectPolygonFeatures.clicked.connect(self.selectPolygonFeatures)
        self.dialogChangeFieldValuesOfGroup.pushButtonSelectSupplementaryPolygonFeatures.clicked.connect(self.selectSupplementaryPolygonFeatures)
        self.dialogChangeFieldValuesOfGroup.pushButtonSelectLineFeatures.clicked.connect(self.selectLineFeatures)
        self.dialogChangeFieldValuesOfGroup.pushButtonSelectPointFeatures.clicked.connect(self.selectPointFeatures)

        # käsittele kaikki neljä kohdetyyppiä
        self.dialogChangeFieldValuesOfGroup.pushButtonChooseUpdatedAttributesAndValuesForSpatialFeatures.clicked.connect(self.handleChooseUpdatedAttributesAndValuesForSpatialFeatures)
        self.dialogChangeFieldValuesOfGroup.pushButtonChooseUpdatedAttributesAndValuesForSuplementarySpatialFeatures.clicked.connect(self.handleChooseUpdatedAttributesAndValuesForSuplementarySpatialFeatures)
        self.dialogChangeFieldValuesOfGroup.pushButtonChooseUpdatedAttributesAndValuesForSpatialLineFeatures.clicked.connect(self.handleChooseUpdatedAttributesAndValuesForSpatialLineFeatures)
        self.dialogChangeFieldValuesOfGroup.pushButtonChooseUpdatedAttributesAndValuesForSpatialPointFeatures.clicked.connect(self.handleChooseUpdatedAttributesAndValuesForSpatialPointFeatures)

        self.dialogChangeFieldValuesOfGroup.pushButtonClose.clicked.connect(self.dialogChangeFieldValuesOfGroup.hide)

        self.dialogChooseAndUpdateFieldValuesForFeatureType.pushButtonUpdateAndClose.clicked.connect(self.updateFieldValuesForFeatureType)
        self.dialogChooseAndUpdateFieldValuesForFeatureType.pushButtonClose.clicked.connect(self.dialogChooseAndUpdateFieldValuesForFeatureType.hide)
        

    def setupDialogChooseAndUpdateFieldValuesForFeatureType(self):
        self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.clearContents()
        self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.setRowCount(0)
        self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.setColumnCount(5)
        self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.setHorizontalHeaderLabels([
                "Ominaisuustieto",
                "Tietokannan taulun kenttä",
                "Tietotyyppi",
                "Ominaisuuden uusi arvo",
                "Päivitä kohteille"
            ])

        self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.resizeColumnsToContents()


    def reset(self):
        self.setupDialogChooseAndUpdateFieldValuesForFeatureType()

        self.hasUserSelectedPolygonFeaturesForUpdate = False
        self.hasUserSelectedSuplementaryPolygonFeaturesForUpdate = False
        self.hasUserSelectedLineFeaturesForUpdate = False
        self.hasUserSelectedPointFeaturesForUpdate = False

        self.shownFieldNamesAndTypes = []

        self.currentFeatureType = None


    def openDialogChangeFieldValuesForGroup(self):
        self.reset()

        if self.yleiskaavaSettings.shouldKeepDialogsOnTop():
            self.dialogChangeFieldValuesOfGroup.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
            self.dialogChooseAndUpdateFieldValuesForFeatureType.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        else:
            self.dialogChangeFieldValuesOfGroup.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
            self.dialogChooseAndUpdateFieldValuesForFeatureType.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)

        self.dialogChangeFieldValuesOfGroup.show()


    def handleChooseUpdatedAttributesAndValuesForSpatialFeatures(self): 
        if not self.hasUserSelectedPolygonFeaturesForUpdate:
            self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä aluevarauksia', Qgis.Warning)
        else:
            self.currentFeatureType = "alue"
            self.chooseUpdatedAttributesAndValuesForSpatialFeatures("alue")

    def handleChooseUpdatedAttributesAndValuesForSuplementarySpatialFeatures(self):
        if not self.hasUserSelectedSuplementaryPolygonFeaturesForUpdate:
            self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä täydentäviä aluekohteita', Qgis.Warning)
        else:
            self.currentFeatureType = "alue_taydentava"
            self.chooseUpdatedAttributesAndValuesForSpatialFeatures("alue_taydentava")

    def handleChooseUpdatedAttributesAndValuesForSpatialLineFeatures(self):
        if not self.hasUserSelectedLineFeaturesForUpdate:
            self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä viivamaisia kohteita', Qgis.Warning)
        else:
            self.currentFeatureType = "viiva"
            self.chooseUpdatedAttributesAndValuesForSpatialFeatures("viiva")

    def handleChooseUpdatedAttributesAndValuesForSpatialPointFeatures(self):
        if not self.hasUserSelectedPointFeaturesForUpdate:
            self.iface.messageBar().pushMessage('Et ole valinnut päivitettäviä pistemäisiä kohteita', Qgis.Warning)
        else:
            self.currentFeatureType = "piste"
            self.chooseUpdatedAttributesAndValuesForSpatialFeatures("piste")


    def chooseUpdatedAttributesAndValuesForSpatialFeatures(self, featureType):

        fieldNamesAndTypes = self.yleiskaavaDatabase.getFieldNamesAndTypes(featureType)
        self.shownFieldNamesAndTypes = self.yleiskaavaUtils.getShownFieldNamesAndTypes(fieldNamesAndTypes)

        self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.setRowCount(len(fieldNamesAndTypes))


        for index, fieldNamesAndType in enumerate(self.shownFieldNamesAndTypes):
            fieldName = fieldNamesAndType["name"]
            fieldTypeName =  fieldNamesAndType["typeName"]
            userFriendlyFieldName = self.yleiskaavaDatabase.getUserFriendlytargetFieldName(fieldName)
            
            fieldNameLabel = QLabel(fieldName)
            fieldTypeNameLabel = QLabel(fieldTypeName)
            userFriendlyFieldNameLabel = QLabel(userFriendlyFieldName)

            self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.setCellWidget(index, ChangeFieldValuesOfGroup.FIELD_USER_FRIENDLY_NAME_INDEX, userFriendlyFieldNameLabel)
            self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.setCellWidget(index, ChangeFieldValuesOfGroup.FIELD_NAME_INDEX, fieldNameLabel)
            self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.setCellWidget(index, ChangeFieldValuesOfGroup.FIELD_TYPE_NAME_INDEX, fieldTypeNameLabel)

            widget = self.yleiskaavaUtils.getWidgetForSpatialFeatureFieldType(fieldTypeName, fieldName)

            if widget != None:
                self.yleiskaavaUtils.connectWidgetValueChangeHandler(widget, partial(self.widgetFieldValueChanged, index), fieldTypeName)
                self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.setCellWidget(index, ChangeFieldValuesOfGroup.FIELD_VALUE_INDEX, widget)
            else:
                self.iface.messageBar().pushMessage('Bugi koodissa: showFieldInSettingsDialogDefaults widget == None', Qgis.Warning)
                #QgsMessageLog.logMessage('showFieldInSettingsDialogDefaults widget == None', 'Yleiskaava-työkalu', Qgis.Critical)
                
            updateChoiceQCheckBoxCellWidget = self.yleiskaavaUtils.createCenteredCheckBoxCellWidgetForTableWidget()
            # updateChoiceQCheckBox.setContentsMargins(0,0,0,0)
            self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.setCellWidget(index, ChangeFieldValuesOfGroup.FIELD_SHOULD_UPDATE_CHOICE_INDEX, updateChoiceQCheckBoxCellWidget)


        self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.resizeColumnsToContents()
        self.dialogChooseAndUpdateFieldValuesForFeatureType.resize(QSize(ChangeFieldValuesOfGroup.CHOOSE_AND_UPDATE_VALUES_DIALOG_MIN_WIDTH, ChangeFieldValuesOfGroup.CHOOSE_AND_UPDATE_VALUES_MIN_HEIGHT))
        self.dialogChooseAndUpdateFieldValuesForFeatureType.show()


    def updateFieldValuesForFeatureType(self):
        featureType = self.currentFeatureType
        updatedFieldValues = []

        for index, shownFieldNamesAndType in enumerate(self.shownFieldNamesAndTypes):
            shouldUpdate = self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.cellWidget(index, ChangeFieldValuesOfGroup.FIELD_SHOULD_UPDATE_CHOICE_INDEX).findChildren(QCheckBox)[0].isChecked()
            if shouldUpdate:
                fieldName = self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.cellWidget(index, ChangeFieldValuesOfGroup.FIELD_NAME_INDEX).text()
                fieldTypeName = self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.cellWidget(index, ChangeFieldValuesOfGroup.FIELD_TYPE_NAME_INDEX).text()
                widget = self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.cellWidget(index, ChangeFieldValuesOfGroup.FIELD_VALUE_INDEX)
                value = self.yleiskaavaUtils.getValueOfWidgetForType(widget, fieldTypeName)
                compatibleValue = self.yleiskaavaUtils.getAttributeValueInCompatibleType(fieldName, fieldTypeName, fieldTypeName, value)

                # QgsMessageLog.logMessage('updateFieldValuesForFeatureType - shouldUpdate, fieldName: ' + fieldName + ', value: ' + str(value) + ', compatibleValue: ' + str(compatibleValue), 'Yleiskaava-työkalu', Qgis.Info)
                updatedFieldValues.append({
                    "fieldName": fieldName,
                    "fieldTypeName": fieldTypeName,
                    "value": compatibleValue
                })

        success = self.yleiskaavaDatabase.updateSelectedSpatialFeaturesWithFieldValues(featureType, updatedFieldValues)

        if success:
            self.yleiskaavaUtils.refreshTargetLayersInProject()
            self.iface.messageBar().pushMessage('Valitsemiesi kohteiden ominaisuustiedot päivitetty', Qgis.Info, 30)
        else:
            self.iface.messageBar().pushMessage('Valitsemiesi kohteiden ominaisuustietojen päivitys epäonnistui', Qgis.Critical)

        self.dialogChooseAndUpdateFieldValuesForFeatureType.hide()


    def selectPolygonFeatures(self):
        layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE)[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Aluevaraukset karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedPolygonFeaturesForUpdate = True

    def selectSupplementaryPolygonFeatures(self):
        layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA)[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Täydentävät aluekohteet karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedSuplementaryPolygonFeaturesForUpdate = True

    def selectLineFeatures(self):
        layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA)[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Viivamaiset kaavakohteet karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedLineFeaturesForUpdate = True

    def selectPointFeatures(self):
        layer = QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_PISTE)[0]
        if layer.selectedFeatureCount() > 0:
             self.iface.messageBar().pushMessage('Pistemäiset kaavakohteet karttatasolla on jo valmiiksi valittuja kohteita', Qgis.Info, 20)
        self.iface.showAttributeTable(layer)
        self.hasUserSelectedPointFeaturesForUpdate = True


    def widgetFieldValueChanged(self, rowIndex):
        # value = self.yleiskaavaUtils.getValueOfWidgetForType(widget, fieldTypeName)
        # compatibleValue = self.yleiskaavaUtils.getAttributeValueInCompatibleType(fieldName, fieldTypeName, fieldTypeName, value)
        shouldUpdate = self.dialogChooseAndUpdateFieldValuesForFeatureType.tableWidgetFeatureAttributesAndValues.cellWidget(rowIndex, ChangeFieldValuesOfGroup.FIELD_SHOULD_UPDATE_CHOICE_INDEX).findChildren(QCheckBox)[0].setChecked(True)