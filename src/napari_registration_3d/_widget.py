"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
from functools import partial
from typing import TYPE_CHECKING

import napari
import numpy as np
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
        self.src_image_layer = None
        self.src_points_layer = None
        self.src_lines_layer = None
        self.src_physical_pixel_size = None
        self.tgt_viewer = None
        self.tgt_image_layer = None
        self.tgt_points_layer = None
        self.tgt_lines_layer = None
        self.tgt_physical_pixel_size = None

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
        hbox_controls = QHBoxLayout()
        add_btn = QPushButton("Add line")
        add_btn.clicked.connect(self.add_btn_clicked)
        del_btn = QPushButton("Delete line")
        hbox_controls.addWidget(add_btn)
        hbox_controls.addWidget(del_btn)

        main_layout = QFormLayout()
        main_layout.addRow("Source image", hbox_select_src_file)
        main_layout.addRow("Target image", hbox_select_tgt_file)
        main_layout.addRow(start_btn)
        main_layout.addRow(hbox_controls)
        self.setLayout(main_layout)

    def load_images(self):
        if self.src_file_path.text() != "" and self.tgt_file_path.text() != "":
            # open viewer windows
            self.src_viewer = napari.Viewer(ndisplay=3)
            self.tgt_viewer = napari.Viewer(ndisplay=3)
            # lines layer, add first all 0 data to lock on 3d
            self.src_lines_layer = self.src_viewer.add_shapes(
                [[0, 0, 0], [0, 0, 0]], shape_type="line", name="Lines"
            )
            self.tgt_lines_layer = self.tgt_viewer.add_shapes(
                [[0, 0, 0], [0, 0, 0]], shape_type="line", name="Lines"
            )
            # load images
            self.src_viewer.open(self.src_file_path.text())
            self.tgt_viewer.open(self.tgt_file_path.text())
            self.src_image_layer = self.src_viewer.layers[0]
            self.tgt_image_layer = self.tgt_viewer.layers[0]
            self.src_image_layer.name = "Source image"
            self.tgt_image_layer.name = "Target image"
            self.src_image_layer.colormap = "red"
            self.tgt_image_layer.colormap = "green"
            self.src_physical_pixel_size = np.array(
                self.src_viewer.layers[0].extent.step
            )
            self.tgt_physical_pixel_size = np.array(
                self.tgt_viewer.layers[0].extent.step
            )

            # callback func, called on mouse click when image layer is active
            @self.src_image_layer.mouse_double_click_callbacks.append
            def src_viewer_on_click(layer, event):
                near_point, far_point = layer.get_ray_intersections(
                    event.position, event.view_direction, event.dims_displayed
                )
                if (near_point is not None) and (far_point is not None):
                    ray = (
                        np.array([near_point, far_point])
                        * self.src_physical_pixel_size
                    )
                    self.src_lines_layer.add(ray, shape_type="line")

            @self.tgt_image_layer.mouse_double_click_callbacks.append
            def tgt_viewer_on_click(layer, event):
                near_point, far_point = layer.get_ray_intersections(
                    event.position, event.view_direction, event.dims_displayed
                )
                if (near_point is not None) and (far_point is not None):
                    ray = (
                        np.array([near_point, far_point])
                        * self.tgt_physical_pixel_size
                    )
                    self.tgt_lines_layer.add(ray, shape_type="line")

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

    def add_btn_clicked(self):
        # TODO
        print("TODO")
