# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'yleiskaava_dialog_copy_source_data_to_database.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DialogCopySourceDataToDatabase(object):
    def setupUi(self, DialogCopySourceDataToDatabase):
        DialogCopySourceDataToDatabase.setObjectName("DialogCopySourceDataToDatabase")
        DialogCopySourceDataToDatabase.resize(699, 441)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DialogCopySourceDataToDatabase.sizePolicy().hasHeightForWidth())
        DialogCopySourceDataToDatabase.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(DialogCopySourceDataToDatabase)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.formLayout.setObjectName("formLayout")
        self.labelSourceLayerComboBox = QtWidgets.QLabel(DialogCopySourceDataToDatabase)
        self.labelSourceLayerComboBox.setObjectName("labelSourceLayerComboBox")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.labelSourceLayerComboBox)
        self.mMapLayerComboBoxSource = QgsMapLayerComboBox(DialogCopySourceDataToDatabase)
        self.mMapLayerComboBoxSource.setObjectName("mMapLayerComboBoxSource")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.mMapLayerComboBoxSource)
        self.verticalLayout.addLayout(self.formLayout)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(12, -1, 12, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_8 = QtWidgets.QLabel(DialogCopySourceDataToDatabase)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout.addWidget(self.label_8)
        self.label_7 = QtWidgets.QLabel(DialogCopySourceDataToDatabase)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout.addWidget(self.label_7)
        self.label_6 = QtWidgets.QLabel(DialogCopySourceDataToDatabase)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout.addWidget(self.label_6)
        self.label_3 = QtWidgets.QLabel(DialogCopySourceDataToDatabase)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.scrollArea = QtWidgets.QScrollArea(DialogCopySourceDataToDatabase)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 685, 360))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.gridLayoutSourceTargetMatch = QtWidgets.QGridLayout()
        self.gridLayoutSourceTargetMatch.setObjectName("gridLayoutSourceTargetMatch")
        self.label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName("label")
        self.gridLayoutSourceTargetMatch.addWidget(self.label, 0, 1, 1, 1)
        self.comboBox_2 = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.comboBox_2.setObjectName("comboBox_2")
        self.gridLayoutSourceTargetMatch.addWidget(self.comboBox_2, 0, 3, 1, 1)
        self.comboBox = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.comboBox.setObjectName("comboBox")
        self.gridLayoutSourceTargetMatch.addWidget(self.comboBox, 0, 2, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setMinimumSize(QtCore.QSize(0, 100))
        self.label_2.setObjectName("label_2")
        self.gridLayoutSourceTargetMatch.addWidget(self.label_2, 0, 0, 1, 1)
        self.verticalLayout_3.addLayout(self.gridLayoutSourceTargetMatch)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(0, -1, -1, -1)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.pushButtonCancel = QtWidgets.QPushButton(DialogCopySourceDataToDatabase)
        self.pushButtonCancel.setObjectName("pushButtonCancel")
        self.horizontalLayout_2.addWidget(self.pushButtonCancel)
        self.pushButtonNext = QtWidgets.QPushButton(DialogCopySourceDataToDatabase)
        self.pushButtonNext.setObjectName("pushButtonNext")
        self.horizontalLayout_2.addWidget(self.pushButtonNext)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(DialogCopySourceDataToDatabase)
        QtCore.QMetaObject.connectSlotsByName(DialogCopySourceDataToDatabase)

    def retranslateUi(self, DialogCopySourceDataToDatabase):
        _translate = QtCore.QCoreApplication.translate
        DialogCopySourceDataToDatabase.setWindowTitle(_translate("DialogCopySourceDataToDatabase", "Kopio lähdeaineistoa tietokantaan"))
        self.labelSourceLayerComboBox.setText(_translate("DialogCopySourceDataToDatabase", "Valitse lähdekarttataso:"))
        self.label_8.setText(_translate("DialogCopySourceDataToDatabase", "Lähdekenttä"))
        self.label_7.setText(_translate("DialogCopySourceDataToDatabase", "Lähdetietotyyppi"))
        self.label_6.setText(_translate("DialogCopySourceDataToDatabase", "Kohdetaulu"))
        self.label_3.setText(_translate("DialogCopySourceDataToDatabase", "Kohdekenttä"))
        self.label.setText(_translate("DialogCopySourceDataToDatabase", "TextLabel"))
        self.label_2.setText(_translate("DialogCopySourceDataToDatabase", "TextLabel"))
        self.pushButtonCancel.setText(_translate("DialogCopySourceDataToDatabase", "Peruuta"))
        self.pushButtonNext.setText(_translate("DialogCopySourceDataToDatabase", "Seuraava"))

from qgsmaplayercombobox import QgsMapLayerComboBox
