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
        input: - input panchromatic file
               - input multiband file
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

