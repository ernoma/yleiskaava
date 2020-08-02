# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Yleiskaava
                                 A QGIS plugin
 Tampereen yleiskaavoituksen tietokannan käyttöön
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-07-02
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Tampereen kaupunki
        email                : erno.makinen@tampere.fi
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QUrl
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.PyQt.QtWidgets import QAction, QWidget, QGridLayout, QLabel, QComboBox

from qgis.core import (
    Qgis, QgsProject)
from qgis.gui import QgsMessageBarItem

# Initialize Qt resources from file resources.py
from ..resources import *

# Import the code for the DockWidget
from .yleiskaava_dockwidget import YleiskaavaDockWidget
import os.path

from .yleiskaava_settings import YleiskaavaSettings
from .yleiskaava_database import YleiskaavaDatabase
from .yleiskaava_utils import YleiskaavaUtils
from .yleiskaava_data_copy_source_to_target import DataCopySourceToTarget
from .yleiskaava_update_regulation_of_group import UpdateRegulationOfGroup
from .yleiskaava_geometry_edit_settings import GeometryEditSettings
from .yleiskaava_change_field_values_of_group import ChangeFieldValuesOfGroup
from .yleiskaava_update_themes_of_group import UpdateThemesOfGroup
from .yleiskaava_update_indexing_of_features import UpdateIndexingOfFeatures
from .yleiskaava_add_source_data_links import AddSourceDataLinks

class Yleiskaava:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(os.path.dirname(__file__))

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Yleiskaava_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Yleiskaava')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'Yleiskaava')
        self.toolbar.setObjectName(u'Yleiskaava')

        #print "** INITIALIZING Yleiskaava"

        self.pluginIsActive = False
        self.dockwidget = None
        self.openProjectMessageBarItem = None

        self.yleiskaavaSettings = YleiskaavaSettings(self.iface, self.plugin_dir)
        self.yleiskaavaDatabase = YleiskaavaDatabase(self.iface, self.plugin_dir)
        self.yleiskaavaUtils = YleiskaavaUtils(self.plugin_dir, self.yleiskaavaDatabase)
        self.yleiskaavaDatabase.setYleiskaavaUtils(self.yleiskaavaUtils)

        self.dataCopySourceToTarget = DataCopySourceToTarget(self.iface, self.plugin_dir, self.yleiskaavaSettings, self.yleiskaavaDatabase, self.yleiskaavaUtils)
        self.updateRegulationOfGroup = UpdateRegulationOfGroup(self.iface, self.plugin_dir, self.yleiskaavaSettings, self.yleiskaavaDatabase, self.yleiskaavaUtils)
        self.geometryEditSettings = GeometryEditSettings(self.iface, self.plugin_dir, self.yleiskaavaSettings, self.yleiskaavaDatabase, self.yleiskaavaUtils)
        self.changeFieldValuesOfGroup = ChangeFieldValuesOfGroup(self.iface, self.plugin_dir, self.yleiskaavaSettings, self.yleiskaavaDatabase, self.yleiskaavaUtils)
        self.updateThemesOfGroup = UpdateThemesOfGroup(self.iface, self.plugin_dir, self.yleiskaavaSettings, self.yleiskaavaDatabase, self.yleiskaavaUtils)
        self.updateIndexingOfFeatures = UpdateIndexingOfFeatures(self.iface, self.plugin_dir, self.yleiskaavaSettings, self.yleiskaavaDatabase, self.yleiskaavaUtils)
        self.addSourceDataLinks = AddSourceDataLinks(self.iface, self.plugin_dir, self.yleiskaavaSettings, self.yleiskaavaDatabase, self.yleiskaavaUtils)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Yleiskaava', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/yleiskaava/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Avaa työkalut'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING Yleiskaava"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.geometryEditSettings.onClosePlugin()


        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD Yleiskaava"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Yleiskaava'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING Yleiskaava"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = YleiskaavaDockWidget()

                self.setupYleiskaavaDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

    def setupYleiskaavaDockWidget(self):

        if not self.canUse():
            self.iface.projectRead.connect(self.handleProjectRead)
            self.openProjectMessageBarItem = QgsMessageBarItem('Yleiskaavan QGIS-työtila pitää käynnistää ennen työkalujen käyttöä', Qgis.Warning, duration=10)
            self.iface.messageBar().pushItem(self.openProjectMessageBarItem)

        self.yleiskaavaSettings.setupDialog()
        self.dataCopySourceToTarget.setup()
        self.updateRegulationOfGroup.setup()
        self.geometryEditSettings.setup()
        self.changeFieldValuesOfGroup.setup()
        self.updateThemesOfGroup.setup()
        self.updateIndexingOfFeatures.setup()
        self.addSourceDataLinks.setup()

        self.dockwidget.pushButtonCopySourceDataToDatabase.clicked.connect(self.dataCopySourceToTarget.openDialogCopySourceDataToDatabase)
        self.dockwidget.pushButtonUpdateRegulationForGroup.clicked.connect(self.updateRegulationOfGroup.openDialogUpdateRegulationOfGroup)
        self.dockwidget.pushButtonOpenGeometryEditSettings.clicked.connect(self.geometryEditSettings.openDockWidgetGeometryEditSettings)
        self.dockwidget.pushButtonChangeFieldValuesForGroup.clicked.connect(self.changeFieldValuesOfGroup.openDialogChangeFieldValuesForGroup)
        self.dockwidget.pushButtonUpdateThemeForGroup.clicked.connect(self.updateThemesOfGroup.openDialogUpdateThemeForGroup)
        self.dockwidget.pushButtonUpdateIndexingForLayer.clicked.connect(self.updateIndexingOfFeatures.openDialogUpdateIndexingOfFeatures)
        self.dockwidget.pushButtonAddSourceDataLinks.clicked.connect(self.addSourceDataLinks.openDialogAddSourceDataLinks)

        self.dockwidget.pushButtonSettings.clicked.connect(self.yleiskaavaSettings.openDialogSettings)

        self.dockwidget.pushButtonHelp.clicked.connect(self.showHelp)


    def handleProjectRead(self):
        if self.canUse():
            self.iface.projectRead.disconnect(self.handleProjectRead)
            self.iface.messageBar().popWidget(self.openProjectMessageBarItem)
            self.openProjectMessageBarItem = None
            

    def canUse(self):
        if len(QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE)) != 1 or len(QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_ALUE_TAYDENTAVA)) != 1 or len(QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_VIIVA)) != 1 or len(QgsProject.instance().mapLayersByName(YleiskaavaDatabase.KAAVAOBJEKTI_PISTE)) != 1:
            return False
        
        return True


    def showHelp(self):
        """Display application help to the user."""
        help_file = 'file:///%s/help/index.html' % self.plugin_dir
        # For testing path:
        #QMessageBox.information(None, 'Help File', help_file)
        # noinspection PyCallByClass,PyTypeChecker
        QDesktopServices.openUrl(QUrl(help_file))