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

import os

import PyQt4.QtGui
import PyQt4.uic
import PyQt4.QtCore

FORM_CLASS_PREPR, _ = PyQt4.uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'preprocessing.ui'))

FORM_CLASS_CLASS, _ = PyQt4.uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'classification.ui'))

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
