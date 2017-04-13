# REM SatEx Plugin
This is a QGIS plugin which streamlines a pixel-based classifiaction of Landsat imagery
using the OrfeoToolbox (OTB). 
Only required inputs are:
1. a directory containing the band raster files of one or more Landsat satellite image,
2. a region of interest as a polygon in a shapefile, and
3. a vector containing a polygon feature set with training/testing information

Optionally a trained SVM model for the libsvm implementation of OTB, as also created by the plugin
can be provided instead of (3).

The plugin requires QGIS (&gt;=2.8) and an installation of the
Orfeo Toolbox (OTB)

Installation
------------
The plugin can be installed via the QGIS Plugin Manager
or by cloning this repository and running
```bash 
make compile
make deploy
``` 
in a shell from within the repository.

Software Requirements
---------------------
The plugin requires an installation of the Orfeo Toolbox (OTB;
details: www.orfeo-toolbox.org). On Windows you can install it
via OSGeo4W on Linux you can install it from packages provided
by your distribution or build it from the source packages available
from its git repository.

Note: Some Linux distributions split OTB in different packages,
in order for this plugin to work make sure the python wrappers
are installed alongside with the otb library. You can check if OTB
and the wrappers are installed from within qgis by opening the 
Python Console and typing (without the >):

```bash
import otbApplication
otbApplication.Registry.GetAvailableApplications()
```

This should return you a list of otb functions if it's working.

In order to build the documentation the python library sphinx
is required.

Purpose of the Plugin
---------------------

Plugin that provides two algorithms for the processing of one or
multiple Landsat scenes within a region of interest towards a
Landuse/Landcoverage classification streamlining all required
processing steps to perform a libsvm/orfeo toolbox (OTB) pixel based
classification.

Structure of the Plugin
-----------------------
The Plugin is structured in two modules:
1. Preprocessing, and
2. Classification 

In the "Preprocessing" algorithm Landsat scenes located in
a directory as , e.g., the directory created by extracting from the
downloaded zip archive of a Landsat 8 scene as can be found on
EarthExplorer http://earthexplorer.usgs.gov/ is 
1) cropped to a region of interest provided as , e.g., a polygon feature in a vector
file and then 
2) the separate spectral Bands are stacked and
3) a virtual raster tile is created out of these, i.e., in case the
region of interest stretches over more than one Landsat scene. If present,
the panchromatic band 8 (Landsat 7 and 8) is excluded from the layers. The
"Classification" algorithm is performing a classification of a
raster file as, e.g., resulting from the "Preprocessing" algorithm
and either by using a provided trained Support Vector Model (SVM)
from OTB or training and testing a SVM on the fly using a provided
ground truth testing/training data set. In the case a on the fly
training/testing is performed the provided ground truth data is
randomly split in a testing (~20%) and a training part (~80%), the
latter is then used in the libsvm implementation of OTB to create a
SVM. This SVM (or the external SVM) are then used to classify the
image. The resulting raster file with class labels is then tested
with the testing dataset (all features of the provided vector layer
in case an external SVM model was provided) and a confusion matrix is
produced. Finally the resulting raster file is sieved (i.e., regions
consisting of view pixels are merged to the surrounding).

You can find further informations on the usage of the plugin in the 
enclosed plugin documentation by pressing the help button in one of the
dialogs or opening ($HOME/.qgis2/python/plugins/SatEx/help/build/html/index.html).

Testing data
------------

In the test/test_data you will find a directory 'satellite_scenes' 
containing a subset of 2 satellite scences, an example region of interest
roi.shp and an example training/testing vector 'train.shp'.
These can be used for testing the funtionality of the plugin.

Contact
-------

Michael Haas - mhaas(at)gfz-potsdam.de
Massimiliano Pittore - pittore(at)gfz-potsdam.de
GFZ German Research Centre for Geosciences - Centre for Early Warning Systems 

License
-------

Copyright (c) 2016, GFZ - Centre for Early Warning
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of REM_satex_plugin nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
