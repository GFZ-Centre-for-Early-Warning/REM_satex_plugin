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
import ogr
#import qgis.core

class Worker(PyQt4.QtCore.QObject):

    def __init__(self, ls_path,roi,out_fname, *args, **kwargs):
        PyQt4.QtCore.QObject.__init__(self, *args, **kwargs)
        self.ls_path = ls_path
        self.roi = roi
        self.out_fname = out_fname
        self.processed = 0
        self.percentage = 0
        self.abort = False
        #TODO:fix
        self.ntasks = 8

    def run(self):
        '''
        Function running all preprocessing steps
        '''
        import utils
        import traceback
        import qgis.core
        import ogr
        import subprocess

        try:
            import otbApplication
        except:
            print 'Plugin requires installation of OrfeoToolbox'

        self.status.emit('Task started!')
        #find the number of different L8 scenes
        #by reading all TIFs splitting off '_Bxy.TIF' and getting unique strings
        try:
            #instantiate utilities function
            ut = utils.utils()
            scenes = set(['_'.join(s.split('_')[:-1]) for s in ut.findFiles(self.ls_path,'*.TIF')])
            #adjust number of tasks
            self.ntasks = self.ntasks*len(scenes)
            self.status.emit('Found {} scenes.'.format(len(scenes)))
            qgis.core.QgsMessageLog.logMessage(str('Found {} Landsat 8 scene(s) in {}'.format(len(scenes),self.ls_path)))
        except:
            self.error.emit(traceback.format_exc())
            self.status.emit('Task failed see log for details')
            qgis.core.QgsMessageLog.logMessage(str('Found no Landsat 8 scenes in {}'.format(self.ls_path)))
            self.finished.emit('Failed')

        #check shapefile roi
        try:
            driver = ogr.GetDriverByName('ESRI Shapefile')
            dataSource = driver.Open(self.roi,0)
            layer = dataSource.GetLayer()
            self.status.emit('Using {} as ROI'.format(self.roi))
            qgis.core.QgsMessageLog.logMessage(str('Using {} as ROI'.format(self.roi)))
        except:
            self.error.emit(traceback.format_exc())
            self.status.emit('Task failed see log for details')
            qgis.core.QgsMessageLog.logMessage(str('Could not open {}'.format(self.roi)))
            self.finished.emit('Failed')

        try:
            #loop through all scenes
            for scene in scenes:
                #find all bands for scene exclude quality band BQA
                try:
                    bands = [b for b in ut.findFiles(self.ls_path,scene+'*.TIF') if '_BQA' not in b]
                    #check if there are 11 bands
                    if len(bands)!=11:
                        self.status.emit('Found {} instead of 11 bands for scene {}'.format(len(bands),scene))
                        qgis.core.QgsMessageLog.logMessage(str('Found {} instead of 11 bands for scene {}'.format(len(bands),scene)))
                        raise Exception
                    else:
                        self.status.emit('Found all 11 bands for scene {}'.format(scene))
                        qgis.core.QgsMessageLog.logMessage(str('Found all 11 bands for scene {} '.format(scene)))
                except:
                    self.error.emit(traceback.format_exc())
                    self.status.emit('Task failed see log for details')
                    qgis.core.QgsMessageLog.logMessage(str('Could not find all 11 bands for scene {}'.format(scene)))
                    self.finished.emit('Failed')
                    raise Exception

                #use gdalwarp to cut bands to roi
                try:
                    #go through bands
                    for band in bands:
                        cmd = ['gdalwarp','-q','-cutline',self.roi,'-crop_to_cutline',self.ls_path+band,self.ls_path+band[:-4]+'_satexTMP_ROI.TIF']
                        subprocess.check_call(cmd)
                        self.status.emit('Cropped band {} to ROI'.format(band))
                        qgis.core.QgsMessageLog.logMessage(str('Cropped band {} to ROI'.format(band)))
                        self.calculate_progress()
                except:
                    self.error.emit(traceback.format_exc())
                    self.status.emit('Task failed see log for details')
                    qgis.core.QgsMessageLog.logMessage(str('Could not execute gdalwarp cmd: {}'.format(' '.join(cmd))))
                    self.finished.emit('Failed')
                    ut.delete_tmps(self.ls_path)
                    raise Exception

                # Layerstack
                try:
                    #respect order B1,B2,B3,B4,B5,B6,B7,B8,B9,B10,B11
                    in_files = [str(self.ls_path+b[:-4]+'_satexTMP_ROI.TIF') for b in bands if '_B8' not in b]
                    in_files.sort()
                    #B10,B11 considered smaller --> resort
                    in_files = in_files[2:] + in_files[0:2]
                    out_file = str(self.ls_path+scene+'_satexTMP_mul.TIF')
                    #call otb wrapper
                    ut.otb_concatenate(in_files,out_file)
                    self.status.emit('Concatenated bands for pansharpening scene {}'.format(scene))
                    qgis.core.QgsMessageLog.logMessage(str('Concatenated bands for pansharpening scene {}'.format(scene)))
                except:
                    self.error.emit(traceback.format_exc())
                    self.status.emit('Task failed see log for details')
                    qgis.core.QgsMessageLog.logMessage(str('Could not execute OTB ConcatenateImages for scene: {}\nin_files: {}\nout_file: {}'.format(scene,in_files,out_file)))
                    self.finished.emit('Failed')
                    ut.delete_tmps(self.ls_path)
                    raise Exception

                #Resample from 30x30 to 15x15
                try:
                    in_file = out_file
                    out_file = str(in_file[:-4]+'_15.TIF')
                    #call otb wrapper
                    ut.otb_resample(in_file,out_file)
                    self.status.emit('Resampled layerstack for pansharpening scene {}'.format(scene))
                    qgis.core.QgsMessageLog.logMessage(str('Resampled layerstack for pansharpening scene {}'.format(scene)))
                except:
                    self.error.emit(traceback.format_exc())
                    self.status.emit('Task failed see log for details')
                    qgis.core.QgsMessageLog.logMessage(str('Could not execute OTB RigidTransformResample for scene: {}\nin_file: {}\nout_file: {}'.format(scene,in_file,out_file)))
                    self.finished.emit('Failed')
                    ut.delete_tmps(self.ls_path)
                    raise Exception

                #superimpose stack with B8 (make sure they are aligned)
                try:
                    in_file_ref = out_file
                    in_file_inm = str(self.ls_path+scene+'_B8_satexTMP_ROI.TIF')
                    out_file = str(self.ls_path+scene+'_B8_satexTMP_SI.TIF')
                    #call otb wrapper
                    ut.otb_superimpose(in_file_ref,in_file_inm,out_file)
                    self.status.emit('Superimposed layerstack to B8 for pansharpening scene {}'.format(scene))
                    qgis.core.QgsMessageLog.logMessage(str('Superimposed layerstack to B8 for pansharpening scene {}'.format(scene)))
                except:
                    self.error.emit(traceback.format_exc())
                    self.status.emit('Task failed see log for details')
                    qgis.core.QgsMessageLog.logMessage(str('Could not execute OTB Superimpose for scene: {}\nin_file_ref: {}\nin_file_inm: {}\nout_file: {}'.format(scene,in_file_ref,in_file_inm,out_file)))
                    self.finished.emit('Failed')
                    ut.delete_tmps(self.ls_path)
                    raise Exception

                #Pansharpen scene
                try:
                    in_file_pan = out_file
                    in_file_mul = in_file_ref
                    out_file = str(self.ls_path+scene+'_satexTMP_pan.TIF')
                    #call otb wrapper
                    ut.otb_pansharpen(in_file_pan,in_file_mul,out_file)
                    self.status.emit('Pansharpened layerstack of scene {}'.format(scene))
                    qgis.core.QgsMessageLog.logMessage(str('Pansharpened layerstack of scene {}'.format(scene)))
                except:
                    self.error.emit(traceback.format_exc())
                    self.status.emit('Task failed see log for details')
                    qgis.core.QgsMessageLog.logMessage(str('Could not execute OTB Pansharpening for scene: {}\nin_file_pan: {}\nin_file_mul: {}\nout_file: {}'.format(scene,in_file_pan,in_file_mul,out_file)))
                    self.finished.emit('Failed')
                    ut.delete_tmps(self.ls_path)
                    raise Exception

                #Split layerstack
                try:
                    in_file_mul = in_file_mul
                    #pattern for output bands <pattern>_x.TIF
                    out_file = str(self.ls_path+scene+'_satexTMP_pan.TIF')
                    #call otb wrapper
                    ut.otb_split(in_file_mul,out_file)
                    self.status.emit('Splitted pansharpened layerstack of scene {}'.format(scene))
                    qgis.core.QgsMessageLog.logMessage(str('Splitted pansharpened layerstack of scene {}'.format(scene)))
                except:
                    self.error.emit(traceback.format_exc())
                    self.status.emit('Task failed see log for details')
                    qgis.core.QgsMessageLog.logMessage(str('Could not execute OTB SplitImage for scene: {}\nin_file_mul: {}\nout_file: {}'.format(scene,in_file_mul,out_file)))
                    self.finished.emit('Failed')
                    ut.delete_tmps(self.ls_path)
                    raise Exception

                #Restack layers with superimposed B8
                try:
                    #gather files
                    in_files = [str(self.ls_path+f) for f in ut.findFiles(self.ls_path,scene+'_satexTMP_pan_*.TIF')]
                    in_files.sort()
                    #add superimposed B8
                    in_files = in_files[:8]+[str(self.ls_path+scene+'_B8_satexTMP_SI.TIF')]+in_files[8:]
                    out_file = str(self.ls_path+scene+'_satexTMP_mul_pan.TIF')
                    #call otb wrapper
                    ut.otb_concatenate(in_files,out_file)
                    self.status.emit('Concatenated pansharpened bands for scene {}'.format(scene))
                    qgis.core.QgsMessageLog.logMessage(str('Concatenated pansharpened bands for scene {}'.format(scene)))
                except:
                    self.error.emit(traceback.format_exc())
                    self.status.emit('Task failed see log for details')
                    qgis.core.QgsMessageLog.logMessage(str('Could not execute OTB ConcatenateImages for scene: {}\nin_files: {}\nout_file: {}'.format(scene,in_files,out_file)))
                    self.finished.emit('Failed')
                    ut.delete_tmps(self.ls_path)
                    raise Exception
        except:
            self.error.emit(traceback.format_exc())
            self.status.emit('Task failed see log for details')
            self.finished.emit('Failed')
            ut.delete_tmps(self.ls_path)

        try:
            cmd = ["gdalbuildvrt",self.out_fname]
            files = [f for f in ut.findFiles(self.ls_path,'*satexTMP_mul_pan.TIF')]
            for f in files:
                cmd.append(str(self.ls_path+f))
            subprocess.check_call(cmd)
            self.status.emit('Merged {} different scenes {} to ROI'.format(len(scenes),self.out_fname))
            qgis.core.QgsMessageLog.logMessage(str('Merged {} different L8 scenes to {}'.format(len(scenes),self.out_fname)))
            self.calculate_progress()
            ut.delete_tmps(self.ls_path)
            self.finished.emit('Succeeded')
        except:
            self.error.emit(traceback.format_exc())
            self.status.emit('Task failed see log for details')
            qgis.core.QgsMessageLog.logMessage(str('Could not execute gdalbuildvrt cmd: {}'.format(' '.join(cmd))))
            self.finished.emit('Failed')
            ut.delete_tmps(self.ls_path)

    def calculate_progress(self):
        self.processed = self.processed + 1
        percentage_new = (self.processed * 100) / self.ntasks
        if percentage_new > self.percentage:
            self.percentage = percentage_new
            self.progress.emit(self.percentage)

    def kill(self):
        self.abort = True

    progress = PyQt4.QtCore.pyqtSignal(int)
    status = PyQt4.QtCore.pyqtSignal(str)
    error = PyQt4.QtCore.pyqtSignal(str)
    killed = PyQt4.QtCore.pyqtSignal()
    finished = PyQt4.QtCore.pyqtSignal(str)

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

        # Create the dialog (after translation) and keep reference
        self.dlg = SatExDialog()

        #interactions
        self.dlg.lineEdit.clear()
        self.dlg.pushButton.clicked.connect(self.select_input_raster)
        self.dlg.lineEdit_2.clear()
        self.dlg.pushButton_2.clicked.connect(self.select_roi)
        self.dlg.lineEdit_3.clear()
        self.dlg.pushButton_3.clicked.connect(self.select_output_name)
        self.dlg.progressBar.reset()

        #TODO:defaults for development
        self.dlg.lineEdit.setText('/home/mhaas/PhD/Routines/rst/plugin/data/LC81740382015287LGN00')
        self.dlg.lineEdit_2.setText('/home/mhaas/PhD/Routines/rst/kerak.shp')
        self.dlg.lineEdit_3.setText('/home/mhaas/PhD/Routines/rst/test.vrt')


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&GFZ SatEx')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SatEx')
        self.toolbar.setObjectName(u'SatEx')

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

    def select_input_raster(self):
        dirname = PyQt4.QtGui.QFileDialog.getExistingDirectory(self.dlg, "Select input directory ","",PyQt4.QtGui.QFileDialog.ShowDirsOnly)
        self.dlg.lineEdit.setText(dirname)

    def select_roi(self):
        filename = PyQt4.QtGui.QFileDialog.getOpenFileName(self.dlg, "Select region of interest ","","*.shp")
        self.dlg.lineEdit_2.setText(filename)

    def select_output_name(self):
        filename = PyQt4.QtGui.QFileDialog.getSaveFileName(self.dlg, "Select output file ","","*.vrt")
        self.dlg.lineEdit_3.setText(filename)

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        #get user edits
        ls_path = self.dlg.lineEdit.text()+'/'
        roi = self.dlg.lineEdit_2.text()
        out_fname = self.dlg.lineEdit_3.text()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        layer = roi
        if result:
            worker = self.worker = Worker(ls_path,roi,out_fname)
            thread = self.thread = PyQt4.QtCore.QThread()
            worker.moveToThread(thread)
            thread.started.connect(worker.run)
            worker.progress.connect(self.dlg.progressBar.setValue)
            worker.status.connect(self.iface.mainWindow().statusBar().showMessage)
            worker.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            worker.finished.connect(thread.quit)
            thread.start()
