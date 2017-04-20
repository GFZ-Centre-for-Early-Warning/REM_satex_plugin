class SatEx:
    '''
    Class for running SatEx as script
    '''
	
    def __init__(self,config):
	import os

	self.config = config
        #setup subrpocess differently for windows
        self.startupinfo = None
        if os.name == 'nt':
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    def updatePForm(self):
        #get user edits
        self.ls_path = self.config['ls_path']+'/'
        self.roi = self.config['roi']
        self.out_fname = self.config['out_fname1']
        if (self.ls_path =='/' or self.roi == '' or self.out_fname == ''):
            return False
        else:
            return True
    
    def updateCForm(self):
        #get user edits
        self.raster = self.config['raster']
        self.in_train = self.config['in_train']
        self.out_fname = self.config['out_fname']
        self.label = self.config['label']
        self.sieve = self.config['sieve']
        self.external = self.config['external']
        #in case an external SVM is provided the testing is optional
        if self.external:
            if (self.raster =='' or self.out_fname == '' or self.sieve == ''):
                return False
            else:
                return True
        else:
            if (self.raster =='' or self.in_train == '' or self.out_fname == '' or self.label == '' or self.sieve == ''):
                return False
            else:
                return True

    def select_input_raster(self):
        dirname = PyQt4.QtGui.QFileDialog.getExistingDirectory(self.Pdlg, "Select input directory ","",PyQt4.QtGui.QFileDialog.ShowDirsOnly)


    def run_preprocessing(self):
        """Run method that performs all the real work"""
        
	valid_input=self.updatePForm()

	import utils
	import traceback
	#import qgis.core
	import ogr
	import os
        import subprocess
	
	try:
	    import otbApplication
	except:
	    print 'ERROR: Plugin requires installation of OrfeoToolbox'
	
	#find the number of different L8 scenes
	#by reading all TIFs splitting off '_Bxy.TIF' and getting unique strings
	e = 'Unspecified error'
	#instantiate utilities function
	ut = utils.utils()
	try:
	    try:
	        #check if input is not empty string
	        1/valid_input
	    except ZeroDivisionError:
	        e = str('Please fill all required input fields')
	        raise Exception
	
	    try:
	        #delete any old tmp files that might be in the directory from a killed task
	        old=ut.delete_tmps(self.ls_path)
	        #if old > 0: qgis.core.QgsMessageLog.logMessage('Old *satexTMP* files were present. They were deleted.')
	        if old > 0: print 'Old *satexTMP* files were present. They were deleted.'
	    except:
	        e = str('Could not delete old *satexTMP* files. Function utils.delete_tmps.')
	        raise Exception
	
	    try:
	        pattern = '*.TIF'
	        scenes = set(['_'.join(s.split('_')[:1]) for s in ut.findFiles(self.ls_path,pattern)])
	        if len(scenes)==0:
	            pattern = '*.tif'
	            scenes = set(['_'.join(s.split('_')[:1]) for s in ut.findFiles(self.ls_path,pattern)])
	        1/len(scenes)
	    except ZeroDivisionError:
	        e = str('Found no scene in {}'.format(self.ls_path))
	        raise Exception
	    else:
	        print str('Found {} scene(s) in {}'.format(len(scenes),self.ls_path))
	
	    #check shapefile roi
	    try:
	        driver = ogr.GetDriverByName('ESRI Shapefile')
	        dataSource = driver.Open(self.roi,0)
	        layer = dataSource.GetLayer()
	        print str('Using {} as ROI'.format(self.roi))
	    except AttributeError:
	        e = str('Could not open {}'.format(self.roi))
	        raise Exception
	
	    #loop through all scenes
	    out_files = []
	    for scene in scenes:
	
	        #find all bands for scene exclude quality band BQA and B8
	        try:
	            bands = [b for b in ut.findFiles(self.ls_path,scene+'*_B'+pattern) if '_BQA' not in b]
	            bands = [b for b in bands if '_B8' not in b]
	            #in case of multiple scenes (and not first scene is processed) check if nr of bands are equal
	            try:
	                #only if more than one scene and at least second scene
	                nr_bands
	            except:
	                if len(bands)==0:
	                    e = str('Found no bands for scene {}.'.format(scene))
	                    raise Exception
	                else:
	                    #store number of bands for potential additonal scenes
	                    nr_bands = len(bands)
	                    print str('Found {} bands (if present, excluding B8 and BQA) for scene {} '.format(nr_bands,scene))
	            else:
	                if len(bands)!=nr_bands:
	                    e = str('Found {} instead of {} bands (excluding B8 and BQA) for scene {}. If multiple scenes are provided in the input directory, ensure they have equal bands!'.format(len(bands),nr_bands,scene))
	                else:
	                    print str('Found {} bands (if present, excluding B8 and BQA) for scene {} '.format(len(bands),scene))
	        except:
	            raise Exception
	
	        #Check if ROI and scene overlap
	        try:
	            error,overlap = ut.vector_raster_overlap(self.roi,self.ls_path+bands[0])
	        except:
	            e = str('Unspecified error while trying to execute utils.vector_raster_overlap function with {} and {}'.format(self.roi,bands[0]))
	            raise Exception
	        if error!='SUCCESS':
	            e = error
	            raise Exception
	        else:
	            try:
	                1/overlap
	            except ZeroDivisionError:
	                e = str('The provided ROI {} does not overlap with scene {}'.format(self.roi,scene))
	                raise Exception
	
	        #use gdalwarp to cut bands to roi
	        try:
	            #go through bands
	            for band in bands:
	                cmd = ['gdalwarp','-overwrite','-q','-cutline',self.roi,'-crop_to_cutline',self.ls_path+band,self.ls_path+band[:-4]+'_satexTMP_ROI'+pattern[1:]]
	        	subprocess.check_call(cmd,startupinfo=self.startupinfo)
	                print str('Cropped band {} to ROI'.format(band))
	        except:
	            e = str('Could not execute gdalwarp cmd: {}.\nError is:{}'.format(' '.join(cmd),error))
	            raise Exception
	
	        # Layerstack
	        try:
	            #respect order B1,B2,B3,B4,B5,B6,B7,B9,B10,B11
	            in_files = [str(self.ls_path+b[:-4]+'_satexTMP_ROI'+pattern[1:]) for b in bands]
	            in_files.sort()
	            if nr_bands==10:
	                # For Landsat 8 B10,B11 considered smaller --> resort
	                in_files = in_files[2:] + in_files[0:2]
	            out_file = str(os.path.dirname(self.out_fname)+'/'+scene+'_satex_mul'+pattern[1:])
	            #call otb wrapper
	            error = ut.otb_concatenate(in_files,out_file)
	            if error!='success': raise ZeroDivisionError
	            #append file to list
	            out_files.append(out_file)
	            #qgis.core.QgsMessageLog.logMessage(str('Concatenated bands for scene {}'.format(scene)))
	            print str('Concatenated bands for scene {}'.format(scene))
	        except ZeroDivisionError:
	            e = str('Could not execute OTB ConcatenateImages for scene: {}\nin_files: {}\nout_file: {}. \nError is: {}'.format(scene,in_files,out_file,error))
	            raise Exception
	
	    # after all scenes were processed combine them to a virtual raster tile
	    try:
	        cmd = ["gdalbuildvrt","-q","-srcnodata","0","-overwrite",self.out_fname]
	        for f in out_files:
	            cmd.append(f)
	        subprocess.check_call(cmd,startupinfo=self.startupinfo)
	        print str('Merged {} different scenes to {}'.format(len(out_files),self.out_fname))
	    except subprocess.CalledProcessError:
	        e = str('Could not execute gdalbuildvrt cmd: {}'.format(' '.join(cmd)))
	        raise Exception
	
	    ##add to map canvas if checked
	    #if self.Pdlg.checkBox.isChecked():
	    #    try:
	    #        self.iface.addRasterLayer(str(self.out_fname), "SatEx_vrt")
	    #    except:
	    #        e = str('Could not add {} to the layer canvas'.format(self.out_fname))
	    #        raise Exception
	
	except:
	    #self.errorMsg(e)
	    #qgis.core.QgsMessageLog.logMessage(str('Exception: {}'.format(e)))
	    print str('Exception: {}'.format(e))
	    #qgis.core.QgsMessageLog.logMessage(str('Exception occurred...deleting temporary files'))
	    print str('Exception occurred...deleting temporary files')
	    ut.delete_tmps(self.ls_path)
	else:
	    #qgis.core.QgsMessageLog.logMessage(str('Processing sucessfully completed'))
	    #qgis.core.QgsMessageLog.logMessage(str('Deleting temporary files'))
	    print str('Processing sucessfully completed')
	    print str('Deleting temporary files')
	    #self.iface.messageBar().pushMessage('Processing successfully completed, see log for details',self.iface.messageBar().SUCCESS,duration=3)
	    print 'Processing successfully completed, see log for details'
	    ut.delete_tmps(self.ls_path)

    def run_classification(self):
        """Run method that performs all the real work"""
	import utils
	
        import traceback
        #import qgis.core
        import ogr
	import os
        import subprocess

        #Get user edits
        valid_input=self.updateCForm()
        #TODO:fix
        self.classification_type='libsvm'
        self.svmModel = self.in_train[:-4]+'_svmModel.svm'
        self.ConfMatrix = self.in_train[:-4]+'_CM.csv'

        try:
            import otbApplication
        except:
            print 'ERROR: Plugin requires installation of OrfeoToolbox'

        e = 'Unspecified error'
        try:
            #instantiate utilities functions
            ut = utils.utils()
	    
	    #FIX:overwrite utils function train
	    print "FIX:overwriting utils function otb_train_cls due to bug in otb"
            #def new_train_classifier(raster, train, stats, classification_type, label, svmModel, ConfMatrix):
	    #    cmd = "~/OTB-5.10.1-Linux64/bin/otbcli_TrainImagesClassifier -io.il {} -io.vd {} -io.imstat {} -sample.mv 100 -sample.vfn {} -classifier {} -classifier.libsvm.k linear -classifier.libsvm.c 1 -classifier.libsvm.opt false -io.out {} -io.confmatout {}".format(raster,train,stats,label,classification_type,svmModel,ConfMatrix)
	    #    os.system(cmd)
	    #    return "success"

            #ut.otb_train_classifier=new_train_classifier

            try:
                #check if input is not empty string
                1/valid_input
            except ZeroDivisionError:
                e = str('Please fill all required input fields')
                raise Exception

            #check if training fields overlap with raster
            if not self.external:
                try:
                    error,overlap = ut.vector_raster_overlap(self.in_train,self.raster)
                except:
                    e = str('Unspecified error while trying to execute utils.vector_raster_overlap function')
                    raise Exception

                if error!='SUCCESS':
                    e = error
                    raise Exception
                else:
                    try:
                        1/overlap
                    except ZeroDivisionError:
                        e = str('At least one feature in {} does not overlap with {}'.format(self.in_train,self.raster))
                        raise Exception

            #generate image statistics
            try:
                self.stats = str(self.raster[:-4]+'_stats.xml')
                error=ut.otb_image_statistics(str(self.raster),str(self.stats))
                if error!='success':raise ZeroDivisionError
                #qgis.core.QgsMessageLog.logMessage(str('Calculated image statistics {} for {}'.format(self.stats,self.raster)))
                print str('Calculated image statistics {} for {}'.format(self.stats,self.raster))
            except ZeroDivisionError:
                e = str('Could not execute OTB Image Statistics on: {}. \nError is:{}'.format(self.raster,error))
                raise Exception

            #differntiate two cases case 1) external SVM provided an case 2) on the fly SVM training
            if self.external:
                if self.in_train!='':
                    #use full training set for testing
                    self.test = self.in_train
                #get SVM filename
                self.svmModel = self.Cdlg.lineEdit_4.text()
            else:
                #split training dataset in 80% train 20% testing
                [self.error,self.test,self.train] = ut.split_train(self.in_train,self.label,self.startupinfo)
                if self.error != 'success':
                    e=self.error
                    raise Exception
                else:
                    #qgis.core.QgsMessageLog.logMessage(str('Splitted ground truth data set in {} (~80%) and {} (~20%)'.format(self.train,self.test)))
                    print str('Splitted ground truth data set in {} (~80%) and {} (~20%)'.format(self.train,self.test))

                #train classifier
                #on the fly (wrong) confusion matrix gets overwritten later
                try:
                    error=ut.otb_train_classifier(self.raster, self.train, self.stats, self.classification_type, self.label, self.svmModel, self.ConfMatrix)
                    if error!='success': raise ZeroDivisionError
                    #qgis.core.QgsMessageLog.logMessage(str('Trained image classifier using {} and {}'.format(self.raster,self.train)))
                    print str('Trained image classifier using {} and {}'.format(self.raster,self.train))
                except ZeroDivisionError:
                    e = 'Could not execute OTB TrainClassifiers with {} {} {} {} {} {} {}. \nError is:{}'.format(self.raster, self.train, self.stats, self.classification_type, self.label, self.svmModel, self.ConfMatrix,error)
                    raise Exception

            #classify image
            try:
                error=ut.otb_classification(self.raster, self.stats, self.svmModel, self.out_fname)
                if error!='success': raise ZeroDivisionError
                print str('Image {} classified as {}'.format(self.raster,self.out_fname))
            except ZeroDivisionError:
                e = 'Could not execute OTB Classifier with {}, {}, {}, {}. \n Error is: {}'.format(self.raster, self.stats, self.svmModel, self.out_fname,error)
                raise Exception

	    #confusion matrix
            try:
                #testing is optional in case of externally provided SVM
                if self.in_train!='':
		    print self.out_fname,self.ConfMatrix,self.test,self.label
                    error=ut.otb_confusion_matrix(self.out_fname,self.ConfMatrix,self.test,self.label)
                    if error!='success':raise ZeroDivisionError
                    print str('Confusion matrix calculated on classified image {} with test set {} saved as {}'.format(self.out_fname,self.test,self.ConfMatrix))
            except ZeroDivisionError:
                e = 'Could not execute OTB Confusion Matrix with {}, {}, {}, {}. \nError is: {}'.format(self.out_fname, self.ConfMatrix, self.test, self.label)
                raise Exception

            #if sieving is asked perform sieving
            #if self.Cdlg.checkBox_3.isChecked():
	    if (self.config['sieve']!=''):
                try:
                    if os.name=='nt':
                        cmd = ['gdal_sieve.bat','-q','-st',str(self.sieve),'-8',str(self.out_fname)]
                    else:
                        cmd = ['gdal_sieve.py','-q','-st',str(self.sieve),'-8',str(self.out_fname)]
                    subprocess.check_call(cmd,startupinfo=self.startupinfo)
                except subprocess.CalledProcessError:
                    e = 'Could not execute {}'.format(cmd)
                    raise Exception

            #add to map canvas if checked
            #if self.Cdlg.checkBox_2.isChecked():
            #    try:
            #        self.iface.addRasterLayer(str(self.out_fname), "SatEx_classified_scene")
            #    except:
            #        e = str('Could not add {} to the layer canvas'.format(self.out_fname))
            #        raise Exception

        except:
            #self.errorMsg(e)
            #qgis.core.QgsMessageLog.logMessage(e)
            print e
        else:
            print str('Processing completed')
            print 'Processing successfully completed, see log for details'

def main():
    import ConfigParser
    
    #read config    
    Config = ConfigParser.ConfigParser()
    Config.read("config.ini")
    #store as dictionary
    config = {}
    #preprocessing
    parameters = ['ls_path','roi','out_fname']  
    for par in parameters:
    	try:
	    config[par] = Config.get("preprocessing",par)  
    	except:
	    config[par] = ''  
    #save before overriden
    config['out_fname1']= config['out_fname']

    #classification
    parameters = ['raster','in_train','out_fname','label','sieve','external']
    for par in parameters:
    	try:
	    config[par] = Config.get("classification",par)  
    	except:
	    config[par] = ''  
    
    #satex instance		
    satex = SatEx(config)

    #workflow
    if (config['ls_path']!=''):
        satex.run_preprocessing()	
    else:
	print 'No valid preprocessing configuration found. Skipping..'
    
    if (config['raster']!=''):
        satex.run_classification()	
    else:
	print 'No valid classification configuration found. Skipping..'
    
if __name__ == "__main__":
    main()
