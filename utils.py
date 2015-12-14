# Function in use for the plugin

class utils(object):

    def findFiles(path,filter,search_dirs=False):
        '''
        Function to find files and directories (type='d') within directory 'path'
        return list of files
        '''
        for root,dirs,files in os.walk(path,filter):
            if search_dirs:
                for directory in fnmatch.filter(dirs,filter):
                    yield directory
            else:
                for file in fnmatch.filter(files,filter):
                    yield file


