# Function in use for the plugin
import os
import fnmatch
import subprocess

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
        cmd = ['rm',path+'*satexTMP*']
