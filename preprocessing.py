# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SatEx
                                 A QGIS plugin
 L8 processing towards exposure
                              -------------------
        begin                : 2015-12-14
        git sha              : $Format:%H$
        copyright            : (C) 2015 by GFZ Michael Haas
        email                : mhaas@gfz-potsdam.de
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
import PyQt4.QtCore
import PyQt4.QtGui
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from preprocessing_dialog import SatExDialog
import os.path

class SatEx:
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
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = PyQt4.QtCore.QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SatEx_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = PyQt4.QtCore.QTranslator()
            self.translator.load(locale_path)

            if PyQt4.QtCore.qVersion() > '4.3.3':
                PyQt4.QtCore.QCoreApplication.installTranslator(self.translator)

       # # Create the dialog (after translation) and keep reference
       # self.dlg = SatExDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&GFZ SatEx')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SatEx')
        self.toolbar.setObjectName(u'SatEx')
        self.windowOpen = False

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
        return PyQt4.QtCore.QCoreApplication.translate('SatEx', message)


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

        icon = PyQt4.QtGui.QIcon(icon_path)
        action = PyQt4.QtGui.QAction(icon, text, parent)
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

        icon_path = ':/plugins/SatEx/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'SatEx'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&GFZ SatEx'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        if not self.windowOpen:
            dlg = SatExDialog(self.iface)
            dlg.show()
            self.windowOpen = True
            dlg.exec_()
            self.windowOpen = False
       # # show the dialog
       # self.dlg.show()
       # #get user edits
       # ls_path = self.dlg.lineEdit.text()+'/'
       # roi = self.dlg.lineEdit_2.text()
       # out_fname = self.dlg.lineEdit_3.text()
       # # Run the dialog event loop
       # result = self.dlg.exec_()
       # # See if OK was pressed
       # if result:
       #     worker = self.worker = Worker(ls_path,roi,out_fname)
       #     thread = self.thread = PyQt4.QtCore.QThread()
       #     worker.moveToThread(thread)
       #     thread.started.connect(worker.run)
       #     worker.progress.connect(self.dlg.progressBar.setValue)
       #     worker.status.connect(self.iface.mainWindow().statusBar().showMessage)
       #     worker.finished.connect(worker.deleteLater)
       #     thread.finished.connect(thread.deleteLater)
       #     worker.finished.connect(thread.quit)
       #     thread.start()
