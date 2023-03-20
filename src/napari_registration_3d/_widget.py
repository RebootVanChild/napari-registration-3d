"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
from functools import partial
from typing import TYPE_CHECKING

import napari
from qtpy.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

if TYPE_CHECKING:
    pass


class MainWidget(QWidget):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # in one of two ways:
    # 1. use a parameter called `napari_viewer`, as done here
    # 2. use a type annotation of 'napari.viewer.Viewer' for any parameter
    def __init__(self, napari_viewer):
        super().__init__()
        self.main_viewer = napari_viewer
        self.src_viewer = None
        self.src_points_layer = None
        self.src_lines_layer = None
        self.tgt_viewer = None
        self.tgt_points_layer = None
        self.tgt_lines_layer = None

        self.src_file_path = QLineEdit(self)
        self.tgt_file_path = QLineEdit(self)
        src_browse_btn = QPushButton("Browse")
        src_browse_btn.clicked.connect(partial(self.select_file, "source"))
        tgt_browse_btn = QPushButton("Browse")
        tgt_browse_btn.clicked.connect(partial(self.select_file, "target"))
        hbox_select_src_file = QHBoxLayout()
        hbox_select_src_file.addWidget(self.src_file_path)
        hbox_select_src_file.addWidget(src_browse_btn)
        hbox_select_tgt_file = QHBoxLayout()
        hbox_select_tgt_file.addWidget(self.tgt_file_path)
        hbox_select_tgt_file.addWidget(tgt_browse_btn)
        start_btn = QPushButton("Start")
        start_btn.clicked.connect(self.load_images)

        main_layout = QFormLayout()
        main_layout.addRow("Source image", hbox_select_src_file)
        main_layout.addRow("Target image", hbox_select_tgt_file)
        main_layout.addRow(start_btn)
        self.setLayout(main_layout)

    def load_images(self):
        if self.src_file_path.text() != "" and self.tgt_file_path.text() != "":
            # open viewer windows
            self.src_viewer = napari.Viewer()
            self.tgt_viewer = napari.Viewer()
            # load images
            self.src_viewer.open(self.src_file_path.text())
            self.tgt_viewer.open(self.tgt_file_path.text())
            self.src_viewer.layers[0].colormap = "red"
            self.tgt_viewer.layers[0].colormap = "green"
            self.src_viewer.dims.ndisplay = 3
            self.tgt_viewer.dims.ndisplay = 3
            # point layer
            self.src_points_layer = self.src_viewer.add_points(
                [], name="point"
            )
            self.tgt_points_layer = self.tgt_viewer.add_points(
                [], name="point"
            )
            print(self.src_points_layer)

    def select_file(self, file_type):
        if file_type == "source":
            fileName, _ = QFileDialog.getOpenFileName(
                self, "Select Source Image", "", "CZI Files (*.czi)"
            )
            self.src_file_path.setText(fileName)
        if file_type == "target":
            fileName, _ = QFileDialog.getOpenFileName(
                self, "Select Target Image", "", "CZI Files (*.czi)"
            )
            self.tgt_file_path.setText(fileName)
