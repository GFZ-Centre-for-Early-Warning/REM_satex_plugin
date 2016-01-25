# Function in use for the plugin
import os
import fnmatch
import otbApplication

class utils(object):
    '''
    Providing functions for the plugin
    '''

    ###################################################
    # General functions
    ###################################################

    def findFiles(self,path,filter,search_dirs=False):
        '''
        Function to find files and directories (search_dirs=True) within directory 'path'
        return list of files
        '''
        for root,dirs,files in os.walk(path,filter):
            if search_dirs:
                for directory in fnmatch.filter(dirs,filter):
                    yield directory
            else:
                for file in fnmatch.filter(files,filter):
                    yield file

    def delete_tmps(self,path):
        '''
        Function to delete temporary files created during processing
        '''
        files = [str(f) for f in self.findFiles(path,'*satexTMP*')]
        if len(files) > 0:
            for f in files:
                os.remove(path+f)
        return len(files)

    ###################################################
    # Preprocessing functions
    ###################################################

    def vector_raster_overlap(self,vector_file,raster_file):
        '''
        Function to determine if the polygon(s) in a vector overlap with a raster
	return true if all overlap false otherwise
        '''
        import ogr
        import gdal
        import osr

	raster = gdal.Open(raster_file)
        driver = ogr.GetDriverByName('ESRI Shapefile')
	vector = driver.Open(vector_file)
	layer = vector.GetLayer()

        #determine srs of raster and vector
        srs1 = osr.SpatialReference(raster.GetProjection())
        srs2 = layer.GetSpatialRef()
        #create transform
        coordTrans = osr.CoordinateTransformation(srs1, srs2)

	# Get raster geometry
	transform = raster.GetGeoTransform()
	pixelWidth = transform[1]
        #if width defined negative set positive
        if pixelWidth < 0: pixelWidth=-pixelWidth
	pixelHeight = transform[5]
        #if height defined negative set positive
        if pixelHeight < 0: pixelHeight=-pixelHeight
	cols = raster.RasterXSize
	rows = raster.RasterYSize

	xLeft = transform[0]
	yTop = transform[3]
	xRight = xLeft+cols*pixelWidth
	yBottom = yTop-rows*pixelHeight

	ring = ogr.Geometry(ogr.wkbLinearRing)
	ring.AddPoint(xLeft, yTop)
	ring.AddPoint(xRight, yTop)
	ring.AddPoint(xRight, yBottom)
	ring.AddPoint(xLeft, yBottom)
	ring.AddPoint(xLeft, yTop)
	rasterGeometry = ogr.Geometry(ogr.wkbPolygon)
        rasterGeometry.AssignSpatialReference(srs1)
	rasterGeometry.AddGeometry(ring)

        #reproject
        rasterGeometry.Transform(coordTrans)

	# Get feature geometry
        overlap = True
        while True:
            try:
                feature = layer.GetNextFeature()
                #make sure a feature was returned and not None
                feature.GetFID()
                #check intersect
                overlap=rasterGeometry.Intersect(feature.GetGeometryRef())
            except:
                break

        return overlap

    def otb_concatenate(self,in_files,out_file):
        '''
        Wrapper for OTB ConcatenateImages
        input: - input files as list of strings
               - output file name
        '''
        ConcatenateImages = otbApplication.Registry.CreateApplication("ConcatenateImages")

        # The following lines set all the application parameters:
        ConcatenateImages.SetParameterStringList("il", in_files)
        ConcatenateImages.SetParameterString("out", out_file)
        ConcatenateImages.SetParameterOutputImagePixelType("out", 2)
        # The following line execute the application
        ConcatenateImages.ExecuteAndWriteOutput()

    def otb_resample(self,in_file,out_file):
        '''
        Wrapper for OTB RigidTransformResample doubles x,y resolution
        input: - input file name
               - output file name
        '''
        # The following line creates an instance of the RigidTransformResample application
        RigidTransformResample = otbApplication.Registry.CreateApplication("RigidTransformResample")

        # The following lines set all the application parameters:
        RigidTransformResample.SetParameterString("in", in_file)
        RigidTransformResample.SetParameterString("out", out_file)
        RigidTransformResample.SetParameterString("transform.type","id")
        RigidTransformResample.SetParameterFloat("transform.type.id.scalex", 2.)
        RigidTransformResample.SetParameterFloat("transform.type.id.scaley", 2.)
        RigidTransformResample.SetParameterOutputImagePixelType("out", 2)

        # The following line execute the application
        RigidTransformResample.ExecuteAndWriteOutput()

    def otb_superimpose(self,in_file_ref,in_file_inm,out_file):
        '''
        Wrapper for OTB Superimpose using bicubic interpolation
        input: - in_file_ref input file as reference
               - in_file_inm input file to superimpose
               - output file name
        '''
	# The following line creates an instance of the Superimpose application
        Superimpose = otbApplication.Registry.CreateApplication("Superimpose")
        # The following lines set all the application parameters:
        Superimpose.SetParameterString("inr", in_file_ref)
        Superimpose.SetParameterString("inm", in_file_inm)
        Superimpose.SetParameterString("out", out_file)
        Superimpose.SetParameterString("interpolator","bco")
        Superimpose.SetParameterString("interpolator.bco.radius","2")
        Superimpose.SetParameterOutputImagePixelType("out", 2)
        # The following line execute the application
        Superimpose.ExecuteAndWriteOutput()

    def otb_pansharpen(self,in_file_pan,in_file_mul,out_file):
        '''
        Wrapper for OTB Pansharpen
        input: - input panchromatic file
               - input multiband file
               - output file name
        '''
        # The following line creates an instance of the Pansharpening application
        Pansharpening = otbApplication.Registry.CreateApplication("Pansharpening")

        # The following lines set all the application parameters:
        Pansharpening.SetParameterString("inp", in_file_pan)
        Pansharpening.SetParameterString("inxs", in_file_mul)
        Pansharpening.SetParameterString("out", out_file)
        Pansharpening.SetParameterOutputImagePixelType("out", 2)
        # The following line execute the application
        Pansharpening.ExecuteAndWriteOutput()

    def otb_split(self,in_file_mul,out_file):
        '''
        Wrapper for OTB SplitImage
        input: - input multiband file
               - output file name
        '''
        # The following line creates an instance of the Pansharpening application
        SplitImage = otbApplication.Registry.CreateApplication("SplitImage")

        # The following lines set all the application parameters:
        SplitImage.SetParameterString("in", in_file_mul)
        SplitImage.SetParameterString("out", out_file)
        SplitImage.SetParameterOutputImagePixelType("out", 2)
        # The following line execute the application
        SplitImage.ExecuteAndWriteOutput()

    ###################################################
    # Classification functions
    ###################################################

    def split_train(self,vector,label,startupinfo):
        '''
        Splits a vector layer into training and testing layers
        with 80%/20% splitting ratio
        '''
        import ogr
        import random
        import math
        import subprocess

        seed = 42
        error,test_file,train_file = '','',''

        try:
            try:
                driver = ogr.GetDriverByName('ESRI Shapefile')
                src = driver.Open(vector,0)
                src_layer = src.GetLayer()
            except:
                error = 'Reading provided training layer {} failed'.format(vector)
                raise Exception

            try:
                #random sampling
                #idxs = list(range(nr_features))
                idxs = []
                labels = []
                while True:
                    try:
                        #determine fids
                        tmp=src_layer.GetNextFeature()
                        i = tmp.GetFID()
                        #store FID
                        idxs.append(i)
                        #store class label
                        labels.append(tmp.GetField(str(label)))
                    except:
                        break
                #make sure label was found
                tmp = 1/len(labels)
                #determine number of features
                nr_features = len(idxs)
                #nr_features = src_layer.GetFeatureCount()
                nr_test = math.ceil(nr_features*0.2)
            except:
                error = 'Could not find column labeled {} in provided training layer {}'.format(label,vector)
                raise Exception

            try:
                #number of unique class labels
                label_set = set(labels)
                nr_labels = len(label_set)
                #number of samples per class
                nr_sample = int(math.ceil(nr_test/nr_labels))
                #determine if class sampling is possible at all (assuming equally sized classes and at least 1 train and 1 test)
                if nr_features < 2*nr_labels:
                    error = 'Classes not populated enough in training set, at least 2 features per class required'
                    raise Exception
            except:
                raise Exception

            try:
                #sample each class
                classes = list(zip(idxs,labels))
                samples = []
                for l in label_set:
                    #all class tuples that are labeled as l
                    tmp = [tup for tup in classes if tup[1]==l]
                    #check that there are training elements left after sampling
                    if len(tmp) <= nr_sample:
                        error = 'Class with label {} not populated enough'.format(l)
                        raise Exception
                    #sample
                    seed = seed+1
                    random.seed(seed)
                    sample=random.sample(tmp,nr_sample)
                    for s in sample:
                        samples.append(s)
                #indexes for split
                idx_test = [tup[0] for tup in samples]
                idx_train = [i for i in idxs if i not in idx_test]
            except:
                raise Exception

            #Create layers
            try:
                #test
                test_file = vector[:-4]+'_test.shp'
                print 'test_file:',test_file
                query_str='('+','.join([str(i) for i in idx_test])+')'
                cmd = ['ogr2ogr','-overwrite','-where','fid in {}'.format(query_str),str(test_file),str(vector)]
                subprocess.check_call(cmd,startupinfo=startupinfo)
            except:
                error = 'Layer creation during splitting failed: {}'.format(' '.join(cmd))
                raise Exception
            try:
                #train
                train_file = vector[:-4]+'_train.shp'
                query_str='('+','.join([str(i) for i in idx_train])+')'
                cmd = ['ogr2ogr','-overwrite','-where','fid in {}'.format(query_str),str(train_file),str(vector)]
                subprocess.check_call(cmd,startupinfo=startupinfo)
            except:
                error = 'Layer creation during splitting failed: {}'.format(' '.join(cmd))
                raise Exception
        except:
            pass

        if error == '': error = 'success'

        return [error,test_file,train_file]

    def otb_image_statistics(self,input_raster, statistics_xml):
        '''
        Compute image statistics and store as xml file
        '''
        # The following line creates an instance of the ComputeImagesStatistics application
        ComputeImagesStatistics = otbApplication.Registry.CreateApplication("ComputeImagesStatistics")

        # The following lines set all the application parameters:
        ComputeImagesStatistics.SetParameterStringList("il", [str(input_raster)])
        ComputeImagesStatistics.SetParameterString("out", str(statistics_xml))

        # The following line execute the application
        ComputeImagesStatistics.ExecuteAndWriteOutput()


    def otb_train_classifier(self,input_raster, input_shape, statistics_xml, classification_type, training_label, output_svm, confusion_matrix_csv):
        '''
        Training the classifier
        '''
        # The following line creates an instance of the TrainImagesClassifier application
        TrainImagesClassifier = otbApplication.Registry.CreateApplication("TrainImagesClassifier")
        # The following lines set all the application parameters:
        TrainImagesClassifier.SetParameterStringList("io.il", [str(input_raster)])
        TrainImagesClassifier.SetParameterStringList("io.vd", [str(input_shape)])
        TrainImagesClassifier.SetParameterString("io.imstat", str(statistics_xml))
        TrainImagesClassifier.SetParameterInt("sample.mv", 100)
        TrainImagesClassifier.SetParameterInt("sample.mt", 100)
        TrainImagesClassifier.SetParameterFloat("sample.vtr", 0.0)
        TrainImagesClassifier.SetParameterString("sample.edg","1")
        TrainImagesClassifier.SetParameterString("sample.vfn", str(training_label))
        TrainImagesClassifier.SetParameterString("classifier", str(classification_type))
        TrainImagesClassifier.SetParameterString("classifier.libsvm.k","linear")
        TrainImagesClassifier.SetParameterFloat("classifier.libsvm.c", 1)
        TrainImagesClassifier.SetParameterString("classifier.libsvm.opt","1")
        TrainImagesClassifier.SetParameterString("io.out", str(output_svm))
        TrainImagesClassifier.SetParameterString("io.confmatout", str(confusion_matrix_csv))

        # The following line execute the application
        TrainImagesClassifier.ExecuteAndWriteOutput()


    def otb_classification(self,input_raster, statistics_xml, input_svm, output_raster):
        '''
        Classification using the trained classifier
        '''
        ImageClassifier = otbApplication.Registry.CreateApplication("ImageClassifier")

        # The following lines set all the application parameters:
        ImageClassifier.SetParameterString("in", str(input_raster))
        ImageClassifier.SetParameterString("imstat", str(statistics_xml))
        ImageClassifier.SetParameterString("model", str(input_svm))
        ImageClassifier.SetParameterString("out", str(output_raster))

        # The following line execute the application
        ImageClassifier.ExecuteAndWriteOutput()


    def otb_confusion_matrix(self,class_raster,out_conf_mat,test_vector,label):
        # The following line creates an instance of the ComputeConfusionMatrix application
        ComputeConfusionMatrix = otbApplication.Registry.CreateApplication("ComputeConfusionMatrix")
        # The following lines set all the application parameters:
        ComputeConfusionMatrix.SetParameterString("in", str(class_raster))
        ComputeConfusionMatrix.SetParameterString("out", str(out_conf_mat))
        ComputeConfusionMatrix.SetParameterString("ref","vector")
        ComputeConfusionMatrix.SetParameterString("ref.vector.in", str(test_vector))
        ComputeConfusionMatrix.SetParameterString("ref.vector.field", str(label))
        ComputeConfusionMatrix.SetParameterInt("nodatalabel", 0)

        # The following line execute the application
        ComputeConfusionMatrix.ExecuteAndWriteOutput()

