# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SatExDialog
                                 A QGIS plugin
 L8 processing towards exposure
                             -------------------
        begin                : 2015-12-14
        git sha              : $Format:%H$
        copyright            : (C) 2015 by GFZ Michael Haas
        email                : mhaas@gfz-potsdam.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
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
