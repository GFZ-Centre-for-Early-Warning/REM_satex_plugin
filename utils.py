# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SatEx
                                 A QGIS plugin
Streamlined algorithms for pixel based classification of Landsat satellite
imagery using OTB.
                              -------------------
        begin                : 2015-12-14
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Michael Haas (GFZ)
        email                : mhaas@gfz-potsdam.de
 ***************************************************************************/

/****************************************************************************
 *                                                                          *
 *    This program is free software: you can redistribute it and/or modify  *
 *    it under the terms of the GNU General Public License as published by  *
 *    the Free Software Foundation, either version 3 of the License, or     *
 *    (at your option) any later version.                                   *
 *                                                                          *
 *    This program is distributed in the hope that it will be useful,       *
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *    GNU General Public License for more details.                          *
 *                                                                          *
 *    You should have received a copy of the GNU General Public License     *
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>. *
 *                                                                          *
 ****************************************************************************/
"""
# Functions in use for the plugin
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

    def findFiles(self,path,pattern):
        '''
        Function to find files with pattern within directory 'path'
        return list of files
        '''
        files=[]
        for root,dirs,files in os.walk(path):
            for f in fnmatch.filter(files,pattern):
                yield f

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
        error = 'Unspecified error in utils.vector_raster_overlap function'
        #explicitly import from osgeo since QGIS named their gdal processing gdal...
        try:
            from osgeo import ogr
            from osgeo import gdal
            from osgeo import osr
        except:
            error = 'Failed to load ogr,gdal and osr from osgeo'

        try:
            raster = gdal.Open(raster_file)
        except:
            error = 'Failed to load raster file {}'.format(raster_file)

        try:
            driver = ogr.GetDriverByName('ESRI Shapefile')
            vector = driver.Open(vector_file)
            layer = vector.GetLayer()
        except:
            error = 'Failed to load shapefile {}'.format(vector_file)

        try:
            #determine srs of raster and vector
            srs1 = osr.SpatialReference(raster.GetProjection())
            srs2 = layer.GetSpatialRef()
            #create transform
            coordTrans = osr.CoordinateTransformation(srs1, srs2)
        except:
            error = 'Failed to determined spatial refernence of {} and {}'.format(raster_file,vector_file)

        try:
	    # get raster geometry
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
        except:
            error='Geometry exctraction of raster {} failed'.format(raster_file)

        try:
            #reproject
            rasterGeometry.Transform(coordTrans)
        except:
            error='Reprojecting the raster geometry {} to the spatial reference system of {} failed'.format(raster_file,vector_file)

        try:
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
        except:
            error = 'Determining if {} and  {} intersect failed'.format(raster_file,vector_file)
        else:
            error = 'SUCCESS'

        return error,overlap

    def otb_concatenate(self,in_files,out_file):
        '''
        Wrapper for OTB ConcatenateImages
        input: - input files as list of strings
               - output file name
        '''
        error = 'Unspecified error'
        try:
            try:
                ConcatenateImages = otbApplication.Registry.CreateApplication("ConcatenateImages")
            except Exception as error:
                raise Exception
            # The following lines set all the application parameters:
            try:
                ConcatenateImages.SetParameterStringList("il", [str(s) for s in in_files])
            except Exception as error:
                raise Exception
            try:
                ConcatenateImages.SetParameterString("out", str(out_file))
            except Exception as error:
                raise Exception
            try:
                ConcatenateImages.SetParameterOutputImagePixelType("out", 2)
            except Exception as error:
                raise Exception

            # The following line executes the application
            try:
                ConcatenateImages.ExecuteAndWriteOutput()
            except Exception as error:
                raise Exception
        except:
            #Get's catched one level higher
            pass
        else:
            error = 'success'
        return error

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
        error = 'Unspecified error'
        try:
            try:
                # The following line creates an instance of the ComputeImagesStatistics application
                ComputeImagesStatistics = otbApplication.Registry.CreateApplication("ComputeImagesStatistics")
            except Exception as error:
                raise Exception
            
            # The following lines set all the application parameters:
            try:
                ComputeImagesStatistics.SetParameterStringList("il", [str(input_raster)])
            except Exception as error:
                raise Exception
            try:     
                ComputeImagesStatistics.SetParameterString("out", str(statistics_xml))
            except Exception as error:
                raise Exception
            try:
                # The following line execute the application
                ComputeImagesStatistics.ExecuteAndWriteOutput()
            except Exception as error:
                raise Exception
        except:
            #Get's catched one level higher
            pass
        else:
            error = 'success'
        return error


    def otb_train_classifier(self,input_raster, input_shape, statistics_xml, classification_type, training_label, output_svm, confusion_matrix_csv):
        '''
        Training the classifier
        '''
        error = 'Unspecified error'
        try:
            try:
                # The following line creates an instance of the TrainImagesClassifier application
                TrainImagesClassifier = otbApplication.Registry.CreateApplication("TrainImagesClassifier")
            except Exception as error:
                raise Exception
                # The following lines set all the application parameters:
            try:
                TrainImagesClassifier.SetParameterStringList("io.il", [str(input_raster)])
            except Exception as error:
                raise Exception
            try:
                TrainImagesClassifier.SetParameterStringList("io.vd", [str(input_shape)])
            except Exception as error:
                raise Exception
            try:
                TrainImagesClassifier.SetParameterString("io.imstat", str(statistics_xml))
            except Exception as error:
                raise Exception
            try:
                TrainImagesClassifier.SetParameterInt("sample.mv", 100)
            except Exception as error:
                raise Exception
            try:
                TrainImagesClassifier.SetParameterInt("sample.mt", 100)
            except Exception as error:
                raise Exception
            #try:
            #    TrainImagesClassifier.SetParameterFloat("sample.vtr", 0.1)
            #except Exception as error:
            #    raise Exception
            #try:
            #    TrainImagesClassifier.SetParameterString("sample.edg","1")
            #except Exception as error:
            #    raise Exception
            try:
                TrainImagesClassifier.UpdateParameters()
            except Exception as error:
                raise Exception
            try:
                TrainImagesClassifier.SetParameterStringList("sample.vfn", [str(training_label)])
            except Exception as error:
                raise Exception
            try:
                TrainImagesClassifier.SetParameterString("classifier", str(classification_type))
            except Exception as error:
                raise Exception
            try:
                TrainImagesClassifier.SetParameterString("classifier.libsvm.k","linear")
            except Exception as error:
                raise Exception
            try:
                TrainImagesClassifier.SetParameterFloat("classifier.libsvm.c", 1)
            except Exception as error:
                raise Exception
            try:
                TrainImagesClassifier.SetParameterString("classifier.libsvm.opt","1")
            except Exception as error:
                raise Exception
            try:
                TrainImagesClassifier.SetParameterString("io.out", str(output_svm))
            except Exception as error:
                raise Exception
            try:
                TrainImagesClassifier.SetParameterString("io.confmatout", str(confusion_matrix_csv))
            except Exception as error:
                raise Exception

                # The following line execute the application
            try:
                TrainImagesClassifier.ExecuteAndWriteOutput()
            except Exception as error:
                raise Exception

        except:
            #Get's catched one level higher
            pass
        else:
            error = 'success'
        return error

    def otb_classification(self,input_raster, statistics_xml, input_svm, output_raster):
        '''
        Classification using the trained classifier
        '''
        error = 'Unspecified error'
        try:
            try:
                ImageClassifier = otbApplication.Registry.CreateApplication("ImageClassifier")
            except Exception as error:
                raise Exception

                # The following lines set all the application parameters:
            try:
                ImageClassifier.SetParameterString("in", str(input_raster))
            except Exception as error:
                raise Exception
            try:
                ImageClassifier.SetParameterString("imstat", str(statistics_xml))
            except Exception as error:
                raise Exception
            try:
                ImageClassifier.SetParameterString("model", str(input_svm))
            except Exception as error:
                raise Exception
            try:
                ImageClassifier.SetParameterString("out", str(output_raster))
            except Exception as error:
                raise Exception

                # The following line execute the application
            try:
                ImageClassifier.ExecuteAndWriteOutput()
            except Exception as error:
                raise Exception
        except:
            #Get's catched one level higher
            pass
        else:
            error = 'success'
        return error


    def otb_confusion_matrix(self,class_raster,out_conf_mat,test_vector,label):
        '''
        Computing a confusion matrix using the test_vector and labeled raster
        '''
        error = 'Unspecified error'
        try:
            try:
                # The following line creates an instance of the ComputeConfusionMatrix application
                ComputeConfusionMatrix = otbApplication.Registry.CreateApplication("ComputeConfusionMatrix")
            except Exception as error:
                raise Exception
            try:
                # The following lines set all the application parameters:
                ComputeConfusionMatrix.SetParameterString("in", str(class_raster))
            except Exception as error:
                raise Exception
            try:
                ComputeConfusionMatrix.SetParameterString("out", str(out_conf_mat))
            except Exception as error:
                raise Exception
            try:
                ComputeConfusionMatrix.SetParameterString("ref","vector")
            except Exception as error:
                raise Exception
            try:
                ComputeConfusionMatrix.SetParameterString("ref.vector.in", str(test_vector))
            except Exception as error:
                raise Exception
            try:
                ComputeConfusionMatrix.UpdateParameters()
            except Exception as error:
                raise Exception
            try:
                ComputeConfusionMatrix.SetParameterString("ref.vector.field", str(label))
            except Exception as error:
                raise Exception
            try:
                ComputeConfusionMatrix.SetParameterInt("nodatalabel", 0)
            except Exception as error:
                raise Exception

                # The following line execute the application
            try:
                ComputeConfusionMatrix.ExecuteAndWriteOutput()
            except Exception as error:
                raise Exception
        except:
            #Get's catched one level higher
            pass
        else:
            error = 'success'
        return error

