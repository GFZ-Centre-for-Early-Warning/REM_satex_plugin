# Function in use for the plugin
import os
import fnmatch
import subprocess
import otbApplication

class utils(object):

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
        cmd = ['rm',path+'/*satexTMP*']

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
        # The following line execute the application
        ConcatenateImages.ExecuteAndWriteOutput()

    def otb_resample(self,in_file,out_file):
        '''
        Wrapper for OTB RigidTransformResample
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

        # The following line execute the application
        RigidTransformResample.ExecuteAndWriteOutput()
