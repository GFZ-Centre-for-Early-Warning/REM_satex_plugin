# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SatExDialog
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

import os

import PyQt4.QtGui
import PyQt4.uic
import PyQt4.QtCore


class Worker(PyQt4.QtCore.QObject):
    '''
    Class providing a worker
    '''

    def __init__(self, *args, **kwargs):
        PyQt4.QtCore.QObject.__init__(self, *args, **kwargs)
        self.killed = False

    #Signals
    progress = PyQt4.QtCore.pyqtSignal(int)
    status = PyQt4.QtCore.pyqtSignal(str)
    error = PyQt4.QtCore.pyqtSignal(str)
    killed = PyQt4.QtCore.pyqtSignal()
    finished = PyQt4.QtCore.pyqtSignal(str)

    def calculate_progress(self):
        self.processed = self.processed + 1
        percentage_new = (self.processed * 100) / self.ntasks
        if percentage_new > self.percentage:
            self.percentage = percentage_new
            self.progress.emit(self.percentage)

    def kill(self):
        self.abort = True

class Preprocess(Worker):
    '''
    Class providing a worker for the preprocessing
    '''

    def __init__(self, ls_path,roi,out_fname, *args, **kwargs):
        super(Preprocess,self).__init__()
        self.ls_path = ls_path
        self.roi = roi
        self.out_fname = out_fname
        self.processed = 0
        self.percentage = 0
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

        #self.status.emit('Task started!')
        #find the number of different L8 scenes
        #by reading all TIFs splitting off '_Bxy.TIF' and getting unique strings
        try:
            try:
                #instantiate utilities function
                ut = utils.utils()
                #delete any old tmp files that might be in the directory from a killed task
                old=ut.delete_tmps(self.ls_path)
                if old > 0: qgis.core.QgsMessageLog.logMessage('Old *satexTMP* files were present. They were deleted.')
                scenes = set(['_'.join(s.split('_')[:-1]) for s in ut.findFiles(self.ls_path,'*.TIF')])
                #adjust number of tasks
                self.ntasks = self.ntasks*len(scenes)
                #self.status.emit('Found {} scenes.'.format(len(scenes)))
                qgis.core.QgsMessageLog.logMessage(str('Found {} Landsat 8 scene(s) in {}'.format(len(scenes),self.ls_path)))
            except Exception as e:
                e = str('Found no Landsat 8 scene in {}'.format(self.ls_path))
                raise Exception

            #check shapefile roi
            try:
                driver = ogr.GetDriverByName('ESRI Shapefile')
                dataSource = driver.Open(self.roi,0)
                layer = dataSource.GetLayer()
                #self.status.emit('Using {} as ROI'.format(self.roi))
                qgis.core.QgsMessageLog.logMessage(str('Using {} as ROI'.format(self.roi)))
            except Exception as e:
                e = str('Could not open {}'.format(self.roi))
                raise Exception

            #loop through all scenes
            for scene in scenes:
                #find all bands for scene exclude quality band BQA and B8
                try:
                    bands = [b for b in ut.findFiles(self.ls_path,scene+'*.TIF') if '_BQA' not in b]
                    bands = [b for b in bands if '_B8' not in b]
                    #check if there are 10 bands
                    #if len(bands)!=11:
                    if len(bands)!=10:
                        e = str('Found {} instead of 10 bands (excluding B8 and BQA) for scene {}'.format(len(bands),scene))
                        raise Exception
                    else:
                        #self.status.emit('Found all 11 bands for scene {}'.format(scene))
                        qgis.core.QgsMessageLog.logMessage(str('Found all 10 bands (excluding B8 and BQA) for scene {} '.format(scene)))
                except Exception as e:
                    e = str('Could not find all 10 bands (excluding B8 and BQA) for scene {}'.format(scene))
                    raise Exception

                #use gdalwarp to cut bands to roi
                try:
                    #go through bands
                    for band in bands:
                        #self.status.emit('Cropping band {} to ROI'.format(band))
                        qgis.core.QgsMessageLog.logMessage(str('Cropping band {} to ROI'.format(band)))
                        cmd = ['gdalwarp','-q','-cutline',self.roi,'-crop_to_cutline',self.ls_path+band,self.ls_path+band[:-4]+'_satexTMP_ROI.TIF']
                        subprocess.check_call(cmd)
                    self.calculate_progress()
                except Exception as e:
                    e = str('Could not execute gdalwarp cmd: {}'.format(' '.join(cmd)))
                    raise Exception

                # Layerstack
                try:
                    #respect order B1,B2,B3,B4,B5,B6,B7,B9,B10,B11
                    #in_files = [str(self.ls_path+b[:-4]+'_satexTMP_ROI.TIF') for b in bands if '_B8' not in b]
                    in_files = [str(self.ls_path+b[:-4]+'_satexTMP_ROI.TIF') for b in bands]
                    in_files.sort()
                    #B10,B11 considered smaller --> resort
                    in_files = in_files[2:] + in_files[0:2]
                    out_file = str(self.ls_path+scene+'_satexTMP_mul.TIF')
                    #call otb wrapper
                    #self.status.emit('Concatenating bands for pansharpening scene {}'.format(scene))
                    qgis.core.QgsMessageLog.logMessage(str('Concatenate bands for pansharpening scene {}'.format(scene)))
                    ut.otb_concatenate(in_files,out_file)
                    self.calculate_progress()
                except Exception as e:
                    e = str('Could not execute OTB ConcatenateImages for scene: {}\nin_files: {}\nout_file: {}'.format(scene,in_files,out_file))
                    raise Exception

               # #Resample from 30x30 to 15x15
               # try:
               #     in_file = out_file
               #     out_file = str(in_file[:-4]+'_15.TIF')
               #     #call otb wrapper
               #     #self.status.emit('Resampling layerstack for pansharpening scene {}'.format(scene))
               #     qgis.core.QgsMessageLog.logMessage(str('Resampling layerstack for pansharpening scene {}'.format(scene)))
               #     ut.otb_resample(in_file,out_file)
               #     self.calculate_progress()
               # except Exception as e:
               #     e = str('Could not execute OTB RigidTransformResample for scene: {}\nin_file: {}\nout_file: {}'.format(scene,in_file,out_file))
               #     raise Exception

               # #superimpose stack with B8 (make sure they are aligned)
               # try:
               #     in_file_ref = out_file
               #     in_file_inm = str(self.ls_path+scene+'_B8_satexTMP_ROI.TIF')
               #     out_file = str(self.ls_path+scene+'_B8_satexTMP_SI.TIF')
               #     #call otb wrapper
               #     #self.status.emit('Superimposing layerstack to B8 for pansharpening scene {}'.format(scene))
               #     qgis.core.QgsMessageLog.logMessage(str('Superimposing layerstack to B8 for pansharpening scene {}'.format(scene)))
               #     ut.otb_superimpose(in_file_ref,in_file_inm,out_file)
               #     self.calculate_progress()
               # except Exception as e:
               #     e = str('Could not execute OTB Superimpose for scene: {}\nin_file_ref: {}\nin_file_inm: {}\nout_file: {}'.format(scene,in_file_ref,in_file_inm,out_file))
               #     raise Exception

               # #Pansharpen scene
               # try:
               #     in_file_pan = out_file
               #     in_file_mul = in_file_ref
               #     out_file = str(self.ls_path+scene+'_satexTMP_pan.TIF')
               #     #call otb wrapper
               #     #self.status.emit('Pansharpening layerstack of scene {}'.format(scene))
               #     qgis.core.QgsMessageLog.logMessage(str('Pansharpening layerstack of scene {}'.format(scene)))
               #     ut.otb_pansharpen(in_file_pan,in_file_mul,out_file)
               #     self.calculate_progress()
               # except Exception as e:
               #     e = str('Could not execute OTB Pansharpening for scene: {}\nin_file_pan: {}\nin_file_mul: {}\nout_file: {}'.format(scene,in_file_pan,in_file_mul,out_file))
               #     raise Exception

               # #Split layerstack
               # try:
               #     in_file_mul = in_file_mul
               #     #pattern for output bands <pattern>_x.TIF
               #     out_file = str(self.ls_path+scene+'_satexTMP_pan.TIF')
               #     #call otb wrapper
               #     #self.status.emit('Splitting pansharpened layerstack of scene {}'.format(scene))
               #     qgis.core.QgsMessageLog.logMessage(str('Splitting pansharpened layerstack of scene {}'.format(scene)))
               #     ut.otb_split(in_file_mul,out_file)
               #     self.calculate_progress()
               # except Exception as e:
               #     e = str('Could not execute OTB SplitImage for scene: {}\nin_file_mul: {}\nout_file: {}'.format(scene,in_file_mul,out_file))
               #     raise Exception

               # #Restack layers with superimposed B8
               # try:
               #     #gather files
               #     in_files = [str(self.ls_path+f) for f in ut.findFiles(self.ls_path,scene+'_satexTMP_pan_*.TIF')]
               #     in_files.sort()
               #     #add superimposed B8
               #     in_files = in_files[:8]+[str(self.ls_path+scene+'_B8_satexTMP_SI.TIF')]+in_files[8:]
               #     out_file = str(self.ls_path+scene+'_satexTMP_mul_pan.TIF')
               #     #call otb wrapper
               #     ut.otb_concatenate(in_files,out_file)
               #     #self.status.emit('Concatenating pansharpened bands for scene {}'.format(scene))
               #     qgis.core.QgsMessageLog.logMessage(str('Concatenating pansharpened bands for scene {}'.format(scene)))
               #     self.calculate_progress()
               # except Exception as e:
               #     e = str('Could not execute OTB ConcatenateImages for scene: {}\nin_files: {}\nout_file: {}'.format(scene,in_files,out_file))
               #     raise Exception

            # after all scenes were processed combine them to a virtual raster tile
            try:
                #cmd = ["gdalbuildvrt","overwrite",self.out_fname]
                cmd = ["gdalbuildvrt","-srcnodata","0","-overwrite",self.out_fname]
                #files = [f for f in ut.findFiles(self.ls_path,'*satexTMP_mul_pan.TIF')]
                files = [f for f in ut.findFiles(self.ls_path,'*satexTMP_mul.TIF')]
                for f in files:
                    cmd.append(str(self.ls_path+f))
                subprocess.check_call(cmd)
                #self.status.emit('Merged {} different scenes to {}'.format(len(files),self.out_fname))
                qgis.core.QgsMessageLog.logMessage(str('Merged {} different L8 scenes to {}'.format(len(files),self.out_fname)))
                self.calculate_progress()
            except:
                e = str('Could not execute gdalbuildvrt cmd: {}'.format(' '.join(cmd)))
                raise Exception
        except:
            self.error.emit(e)
            #self.status.emit('**ERROR**: Task failed, see log for details')
            self.finished.emit('Failed')
            qgis.core.QgsMessageLog.logMessage(str('Deleting temporary files'))
            ut.delete_tmps(self.ls_path)
        else:
            #self.status.emit('Task successfuly completed, see log for details')
            self.finished.emit('Succeeded')
            qgis.core.QgsMessageLog.logMessage(str('Deleting temporary files'))
            #ut.delete_tmps(self.ls_path)

class Classify(Worker):
    '''
    Class providing a worker for the classification
    '''
    import os

    def __init__(self, raster,in_train,out_fname, *args, **kwargs):
        super(Classify,self).__init__()

        if '.vrt' not in raster:
            if '.TIF' not in raster:
                raise IOError('Input raster should be .TIF or .vrt')
            else:
                self.raster = raster
        else:
            self.raster = raster

        if '.shp' not in in_train:
            raise IOError('Input train should be .shp')
        else:
            self.in_train = in_train

        self.out_fname = out_fname
        self.processed = 0
        self.percentage = 0
        self.abort = False
        #TODO:fix
        self.ntasks = 8
        self.path = os.path.dirname(self.raster)+'/'

    def run(self):
        '''
        Function running all classification steps
        '''
        import utils
        import traceback
        import qgis.core
        import ogr
        #import subprocess
        import os

        try:
            import otbApplication
        except:
            print 'Plugin requires installation of OrfeoToolbox'

        #self.status.emit('Task started!')
        try:
            ut = utils.utils()
            #generate image statistics
            try:
                stats = str(self.path+self.raster[:-4]+'_stats.xml')
                ut.otb_image_statistics(self.raster,stats)
                #self.status.emit('Calculated image statistics {} for {}'.format(stats,raster))
                #qgis.core.QgsMessageLog.logMessage(str('Calculated image statistics {} for {}'.format(stats,raster)))
                self.calculate_progress()
            except:
                e = str('Could not execute OTB Image Statistics on: {}'.format(raster))
                raise Exception
            #split training dataset in 80% train 20% testing
            try:
                error,train,test = ut.split_train(self.in_train)
                if error != '':
                    raise Exception
                #self.status.emit('Calculated image statistics {} for {}'.format(stats,raster))
                #qgis.core.QgsMessageLog.logMessage(str('Calculated image statistics {} for {}'.format(stats,raster)))
                #self.calculate_progress()
            except:
                e=error
                raise Exception
        except:
            self.error.emit(e)
            #self.status.emit('**ERROR**: Task failed, see log for details')
            self.finished.emit('Failed')
            qgis.core.QgsMessageLog.logMessage(str('Deleting temporary files'))
            ut.delete_tmps(self.ls_path)
        else:
            #self.status.emit('Task successfuly completed, see log for details')
            self.finished.emit('Succeeded')
            qgis.core.QgsMessageLog.logMessage(str('Processing completed'))
            qgis.core.QgsMessageLog.logMessage(str('Deleting temporary files'))
            ut.delete_tmps(self.ls_path)

FORM_CLASS_PREPR, _ = PyQt4.uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'uis/preprocessing.ui'))

FORM_CLASS_CLASS, _ = PyQt4.uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'uis/classification.ui'))

class PreprocessingDialog(PyQt4.QtGui.QDialog, FORM_CLASS_PREPR):

    def __init__(self, parent=None):
        """Constructor."""
        super(PreprocessingDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

    def startWorker(self, iface, ls_path, roi, out_fname):
        self.iface = iface
        self.ls_path = ls_path
        self.roi = roi
        self.out_fname = out_fname

        # create a new worker instance
        worker = Preprocess(self.ls_path,self.roi,self.out_fname)

        # configure the QgsMessageBar
        messageBar = self.iface.messageBar().createMessage('Doing something time consuming...', )
        progressBar = PyQt4.QtGui.QProgressBar()
        progressBar.setAlignment(PyQt4.QtCore.Qt.AlignLeft|PyQt4.QtCore.Qt.AlignVCenter)
        cancelButton = PyQt4.QtGui.QPushButton()
        cancelButton.setText('Cancel')
# TODO: implement
#        cancelButton.clicked.connect(worker.kill)
        messageBar.layout().addWidget(progressBar)
        messageBar.layout().addWidget(cancelButton)
        self.iface.messageBar().pushWidget(messageBar, self.iface.messageBar().INFO)
        self.messageBar = messageBar

        # start the worker in a new thread
        thread = PyQt4.QtCore.QThread(self)
        worker.moveToThread(thread)
        worker.finished.connect(self.workerFinished)
        worker.error.connect(self.workerError)
        worker.progress.connect(progressBar.setValue)
        #worker.status.connect(self.updateTextbox)
        thread.started.connect(worker.run)
        thread.start()
        self.thread = thread
        self.worker = worker

    def workerFinished(self, return_str):
        # clean up the worker and thread
        # disconnect the signals
        self.worker.finished.disconnect()
        self.worker.error.disconnect()
        self.worker.progress.disconnect()
        self.thread.started.disconnect()
        #delete worker and thread
        self.worker.deleteLater()

        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()
        # remove widget from message bar
        self.iface.messageBar().popWidget(self.messageBar)
        #if ret is not None:
        #    # report the result
        #    layer, total_area = ret
        #    self.iface.messageBar().pushMessage('The total area of {name} is {area}.'.format(name=layer.name(), area=total_area))
        #else:
        #    # notify the user that something went wrong
        #    self.iface.messageBar().pushMessage('Something went wrong! See the message log for more information.', level=QgsMessageBar.CRITICAL, duration=3)

    def workerError(self,exception_string):
        import qgis.core
        qgis.core.QgsMessageLog.logMessage(str('Error:'+exception_string),level=qgis.core.QgsMessageLog.CRITICAL)
        #self.iface.messageBar().pushMessage("GFZ Satex","Processing failed. See log for details.",level=qgis.core.QgsMessageBar.CRITICAL,duration=5)

class ClassificationDialog(PyQt4.QtGui.QDialog, FORM_CLASS_CLASS):

    def __init__(self, parent=None):
        """Constructor."""
        super(ClassificationDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        ##interactions
        #self.lineEdit.clear()
        #self.pushButton.clicked.connect(self.select_input_pan)
        #self.lineEdit_2.clear()
        #self.pushButton_2.clicked.connect(self.select_training)
        #self.lineEdit_3.clear()
        #self.pushButton_3.clicked.connect(self.select_output_name)
        #self.progressBar.reset()

        ##TODO:defaults for development
        #self.lineEdit.setText('/home/mhaas/PhD/Routines/rst/test.vrt')
        #self.lineEdit_2.setText('/home/mhaas/PhD/Routines/rst/kerak.shp')
        #self.lineEdit_3.setText()

    #def updateForm(self):
    #    #get user edits
    #    self.raster = self.lineEdit.text()+'/'
    #    self.train = self.lineEdit_2.text()
    #    self.out_fname = self.lineEdit_3.text()

    #def select_input_pan(self):
    #    filename = PyQt4.QtGui.QFileDialog.getOpenFileName(self, "Select input pansharpened scene ","","")
    #    self.lineEdit.setText(filename)

    #def select_training(self):
    #    filename = PyQt4.QtGui.QFileDialog.getOpenFileName(self, "Select training vector ","","*.shp")
    #    self.lineEdit_2.setText(filename)

    #def select_output_name(self):
    #    filename = PyQt4.QtGui.QFileDialog.getSaveFileName(self, "Select output file ","","*.vrt")
    #    self.lineEdit_3.setText(filename)

    ##def updateProgress(self,value):
    ##    self.progressBar.setValue(value)

    #def updateTextbox(self,msg):
    #    self.textBrowser.append(msg)

    #def workerError(self,error):
    #    import qgis.core
    #    qgis.core.QgsMessageLog.logMessage(str('Error:'+error))
    #    #self.iface.messageBar().pushMessage("GFZ Satex","Processing failed. See log for details.",level=qgis.core.QgsMessageBar.CRITICAL,duration=5)

    #@PyQt4.QtCore.pyqtSlot()
    #def accept(self):
    #    self.updateForm()
    #    self.worker = Classify(self.raster,self.train,self.out_fname)
    #    self.thread = PyQt4.QtCore.QThread()
    #    #worker = Preprocess(self.ls_path,self.roi,self.out_fname)
    #    #thread = PyQt4.QtCore.QThread(self)
    #    self.worker.moveToThread(self.thread)
    #    self.thread.started.connect(self.worker.run)
    #    self.worker.progress.connect(self.progressBar.setValue)
    #  #  worker.progress.connect(self.updateProgress)
    #  #  worker.status.connect(self.iface.mainWindow().statusBar().showMessage)
    #    self.worker.status.connect(self.updateTextbox)
    #    self.worker.error.connect(self.workerError)
    #    self.worker.finished.connect(self.worker.deleteLater)
    #    self.thread.finished.connect(self.thread.deleteLater)
    #    self.worker.finished.connect(self.thread.quit)
    #    self.thread.start()

    #@PyQt4.QtCore.pyqtSlot()
    #def reject(self):
    #    PyQt4.QtGui.QDialog.reject(self)
