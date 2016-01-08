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
    import ogr
    import random
    import math

    def split_train(self,vector,label):
        '''
        Splits a vector layer into training and testing layers
        whit 80%/20% splitting ratio
        '''
        seed = 42
        error,test_file,train_file = ''
        try:
            try:
                driver = ogr.GetDriverByName('ESRI Shapefile')
                src = driver.Open(self.roi,0)
                src_layer = src.GetLayer()
            except:
                error = 'Reading provided training layer {} failed'.format(vector)
                raise Exception

            try:
                #random sampling
                #determine number of features
                nr_features = src_layer.GetFeatureCount()
                nr_test = int(math.ceil(nr_features*0.2))

                #determine different labels
                idxs = list(range(nr_features))
                labels = []
                for i in idxs:
                    labels.append(src_layer.GetFeature(i).GetField(label))
            except:
                error = 'Could not find label {} in provided training layer {}'.format(label,vector)
                raise Exception

            try:
                #number of different labels
                label_set = set(labels)
                nr_labels = len(label_set)
                #number of samples per class
                nr_sample = int(math.ceil(nr_test/nr_labels))
                #determine if class sampling is possible (assuming equally sized classes)
                if math.floor(nr_features/nr_sample) < nr_labels:
                    error = 'Classes not populated enough in training set'
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

            try:
                #Create layers
                #Gather meta info
                srs = src_layer.GetSpatialRef()
                geom_type = src_layer.GetLayerDefn().GetGeomType()

                test_file = vector[:-4]+'_test.shp'
                train_file = vector[:-4]+'_train.shp'
                test = driver.CreateDataSource(test_file)
                train = driver.CreateDataSource(train_file)
                test_layer = test.CreateLayer('test',srs = srs,geom_type=geom_type)
                train_layer = train.CreateLayer('train',srs = srs,geom_type=geom_type)
                #populate
                for i in idx_test:
                    tmp = src_layer.GetFeature(i)
                    [test_layer.CreateField(tmp.GetFieldDefnRef(i)) for i in range(tmp.GetFieldCount())]
                for i in idx_train:
                    tmp = src_layer.GetFeature(i)
                    [train_layer.CreateField(tmp.GetFieldDefnRef(i)) for i in range(tmp.GetFieldCount())]
            except:
                error = 'Layer creation failed'
                raise Exception
        except:
            pass

        return error,test_file,train_file

    def otb_image_statistics(self,input_raster, statistics_xml):
        '''
        Compute image statistics and store as xml file
        '''
        # The following line creates an instance of the ComputeImagesStatistics application
        ComputeImagesStatistics = otbApplication.Registry.CreateApplication("ComputeImagesStatistics")

        # The following lines set all the application parameters:
        ComputeImagesStatistics.SetParameterStringList("il", [input_raster])
        ComputeImagesStatistics.SetParameterString("out", statistics_xml)

        # The following line execute the application
        ComputeImagesStatistics.ExecuteAndWriteOutput()


    def otb_train_classifier(self,input_raster, input_shape, statistics_xml, classification_type, training_label, output_svm, confusion_matrix_csv):
        '''
        Training the classifier
        '''
        # The following line creates an instance of the TrainImagesClassifier application
        TrainImagesClassifier = otbApplication.Registry.CreateApplication("TrainImagesClassifier")
        # The following lines set all the application parameters:
        TrainImagesClassifier.SetParameterStringList("io.il", [input_raster])
        TrainImagesClassifier.SetParameterStringList("io.vd", [input_shape])
        TrainImagesClassifier.SetParameterString("io.imstat", statistics_xml)
        TrainImagesClassifier.SetParameterInt("sample.mv", 100)
        TrainImagesClassifier.SetParameterInt("sample.mt", 100)
        TrainImagesClassifier.SetParameterFloat("sample.vtr", 0.5)
        TrainImagesClassifier.SetParameterString("sample.edg","1")
        TrainImagesClassifier.SetParameterString("sample.vfn", training_label)
        TrainImagesClassifier.SetParameterString("classifier", classification_type)
        TrainImagesClassifier.SetParameterString("classifier.libsvm.k","linear")
        TrainImagesClassifier.SetParameterFloat("classifier.libsvm.c", 1)
        TrainImagesClassifier.SetParameterString("classifier.libsvm.opt","1")
        TrainImagesClassifier.SetParameterString("io.out", output_svm)
        TrainImagesClassifier.SetParameterString("io.confmatout", confusion_matrix_csv)

        # The following line execute the application
        TrainImagesClassifier.ExecuteAndWriteOutput()

    def otb_classification(self,input_raster, statistics_xml, input_svm, output_raster):
        '''
        Classification using the trained classifier
        '''
        ImageClassifier = otbApplication.Registry.CreateApplication("ImageClassifier")

        # The following lines set all the application parameters:
        ImageClassifier.SetParameterString("in", input_raster)
        ImageClassifier.SetParameterString("imstat", statistics_xml)
        ImageClassifier.SetParameterString("model", input_svm)
        ImageClassifier.SetParameterString("out", output_raster)

        # The following line execute the application
        ImageClassifier.ExecuteAndWriteOutput()

