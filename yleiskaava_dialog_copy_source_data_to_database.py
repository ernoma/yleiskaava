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
        DialogCopySourceDataToDatabase.resize(503, 312)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DialogCopySourceDataToDatabase.sizePolicy().hasHeightForWidth())
        DialogCopySourceDataToDatabase.setSizePolicy(sizePolicy)
        DialogCopySourceDataToDatabase.setMinimumSize(QtCore.QSize(0, 0))
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
        self.tableWidgetSourceTargetMatch = QtWidgets.QTableWidget(DialogCopySourceDataToDatabase)
        self.tableWidgetSourceTargetMatch.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tableWidgetSourceTargetMatch.setObjectName("tableWidgetSourceTargetMatch")
        self.tableWidgetSourceTargetMatch.setColumnCount(0)
        self.tableWidgetSourceTargetMatch.setRowCount(0)
        self.verticalLayout.addWidget(self.tableWidgetSourceTargetMatch)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(0, -1, -1, -1)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButtonCancel = QtWidgets.QPushButton(DialogCopySourceDataToDatabase)
        self.pushButtonCancel.setObjectName("pushButtonCancel")
        self.horizontalLayout_2.addWidget(self.pushButtonCancel)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.pushButtonNext = QtWidgets.QPushButton(DialogCopySourceDataToDatabase)
        self.pushButtonNext.setObjectName("pushButtonNext")
        self.horizontalLayout_2.addWidget(self.pushButtonNext)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(DialogCopySourceDataToDatabase)
        QtCore.QMetaObject.connectSlotsByName(DialogCopySourceDataToDatabase)

    def retranslateUi(self, DialogCopySourceDataToDatabase):
        _translate = QtCore.QCoreApplication.translate
        DialogCopySourceDataToDatabase.setWindowTitle(_translate("DialogCopySourceDataToDatabase", "Kopioi lähdeaineistoa tietokantaan (vaihe 1/3)"))
        self.labelSourceLayerComboBox.setText(_translate("DialogCopySourceDataToDatabase", "Valitse lähdekarttataso:"))
        self.pushButtonCancel.setText(_translate("DialogCopySourceDataToDatabase", "Peruuta"))
        self.pushButtonNext.setText(_translate("DialogCopySourceDataToDatabase", "Seuraava"))

from qgsmaplayercombobox import QgsMapLayerComboBox
