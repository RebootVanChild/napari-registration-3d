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
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QPushButton,
    QWidget,
)

from ._util import (
    get_affine_matrix_from_landmarks,
    inverse_rotation_of_camera,
    mid_point_of_shortest_line,
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
        # self.main_viewer = napari_viewer
        self.src_viewer = None
        self.src_image_layer = None
        self.src_lines_layer = None
        self.src_points_layer = None
        self.src_physical_pixel_size = None
        # self.tgt_viewer = None
        self.tgt_viewer = napari_viewer
        self.tgt_image_layer = None
        self.tgt_lines_layer = None
        self.tgt_points_layer = None
        self.tgt_physical_pixel_size = None

        self.landmark_pair_index = 0
        # matrix calculated to apply on src image to align
        self.src_transformation_matrix = np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        )

        self.overlay_image_layer = None

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

        # landmark list box
        self.landmark_list_box = QListWidget()
        self.landmark_list_box.currentRowChanged.connect(
            self.landmark_list_box_item_current_row_changed
        )
        hbox_landmark_list_box_controls = QHBoxLayout()
        clear_line_pair_selection_btn = QPushButton("Clear selection")
        clear_line_pair_selection_btn.clicked.connect(
            self.clear_point_pair_selection
        )
        delete_line_pair_btn = QPushButton("Delete line pair")
        delete_line_pair_btn.clicked.connect(self.delete_line_pair)
        hbox_landmark_list_box_controls.addWidget(
            clear_line_pair_selection_btn
        )
        hbox_landmark_list_box_controls.addWidget(delete_line_pair_btn)

        hbox_overlay_controls = QHBoxLayout()
        align_images_btn = QPushButton("Align images")
        align_images_btn.clicked.connect(self.align_images_btn_clicked)
        self.overlay_btn = QCheckBox("Overlay")
        self.overlay_btn.stateChanged.connect(self.set_overlay_visibility)
        hbox_overlay_controls.addWidget(align_images_btn)
        hbox_overlay_controls.addWidget(self.overlay_btn)

        align_viewers_btn = QPushButton("Align viewers")
        align_viewers_btn.clicked.connect(self.align_viewers_btn_clicked)

        main_layout = QFormLayout()
        main_layout.addRow("Source image", hbox_select_src_file)
        main_layout.addRow("Target image", hbox_select_tgt_file)
        main_layout.addRow(start_btn)
        main_layout.addRow(self.landmark_list_box)
        main_layout.addRow(hbox_landmark_list_box_controls)
        main_layout.addRow(align_viewers_btn)
        main_layout.addRow(hbox_overlay_controls)
        self.setLayout(main_layout)

    def load_images(self):
        if self.src_file_path.text() != "" and self.tgt_file_path.text() != "":
            # open viewer windows
            self.src_viewer = napari.Viewer(ndisplay=3)
            # self.tgt_viewer = napari.Viewer(ndisplay=3)
            self.tgt_viewer.dims.ndisplay = 3
            # load images
            # source image
            self.src_viewer.open(self.src_file_path.text())
            self.src_image_layer = self.src_viewer.layers[0]
            self.src_image_layer.name = "Source image"
            self.src_image_layer.colormap = "red"
            # target image
            self.tgt_viewer.open(self.tgt_file_path.text())
            self.tgt_image_layer = self.tgt_viewer.layers[0]
            self.tgt_image_layer.name = "Target image"
            self.tgt_image_layer.colormap = "green"
            # overlay image
            self.tgt_viewer.open(self.src_file_path.text())
            self.overlay_image_layer = self.tgt_viewer.layers[1]
            self.overlay_image_layer.name = "Aligned image"
            self.overlay_image_layer.colormap = "red"
            self.overlay_image_layer.blending = "additive"
            self.overlay_image_layer.affine = self.src_transformation_matrix
            self.overlay_image_layer.visible = False
            # image info
            self.src_physical_pixel_size = np.array(
                self.src_viewer.layers[0].extent.step
            )
            self.tgt_physical_pixel_size = np.array(
                self.tgt_viewer.layers[0].extent.step
            )
            # lines layer
            self.src_lines_layer = self.src_viewer.add_shapes(
                ndim=3, shape_type="line", name="temp line"
            )
            self.tgt_lines_layer = self.tgt_viewer.add_shapes(
                ndim=3, shape_type="line", name="temp line"
            )
            # point layer
            self.src_points_layer = self.src_viewer.add_points(
                ndim=3, name="Landmarks"
            )
            self.tgt_points_layer = self.tgt_viewer.add_points(
                ndim=3, name="Landmarks"
            )
            # set layer selection to image
            self.src_viewer.layers.selection = {self.src_image_layer}
            self.tgt_viewer.layers.selection = {self.tgt_image_layer}

            # callback func, called on mouse click when image layer is active
            @self.src_image_layer.mouse_double_click_callbacks.append
            def src_viewer_on_click(layer, event):
                # if src points is no more than tgt points
                if len(self.src_points_layer.data) <= len(
                    self.tgt_points_layer.data
                ):
                    near_point, far_point = layer.get_ray_intersections(
                        event.position,
                        event.view_direction,
                        event.dims_displayed,
                    )
                    if (near_point is not None) and (far_point is not None):
                        new_line = (
                            np.array([near_point, far_point])
                            * self.src_physical_pixel_size
                        )
                        # if no line yet
                        if len(self.src_lines_layer.data) == 0:
                            self.src_lines_layer.add(
                                new_line, shape_type="line"
                            )
                        # if already a line exist
                        else:
                            existed_line = self.src_lines_layer.data[0]
                            new_point = mid_point_of_shortest_line(
                                existed_line, new_line
                            )
                            self.src_lines_layer.data = []
                            self.src_points_layer.add(new_point)
                            # if src points match tgt points
                            # new pair is created
                            if len(self.src_points_layer.data) == len(
                                self.tgt_points_layer.data
                            ):
                                self.landmark_pair_index += 1
                                self.landmark_list_box.addItem(
                                    "landmark pair "
                                    + str(self.landmark_pair_index)
                                )

            @self.tgt_image_layer.mouse_double_click_callbacks.append
            def tgt_viewer_on_click(layer, event):
                # if tgt points is no more than src points
                if len(self.tgt_points_layer.data) <= len(
                    self.src_points_layer.data
                ):
                    near_point, far_point = layer.get_ray_intersections(
                        event.position,
                        event.view_direction,
                        event.dims_displayed,
                    )
                    if (near_point is not None) and (far_point is not None):
                        new_line = (
                            np.array([near_point, far_point])
                            * self.tgt_physical_pixel_size
                        )
                        # if no line yet
                        if len(self.tgt_lines_layer.data) == 0:
                            self.tgt_lines_layer.add(
                                new_line, shape_type="line"
                            )
                        # if already a line exist
                        else:
                            existed_line = self.tgt_lines_layer.data[0]
                            new_point = mid_point_of_shortest_line(
                                existed_line, new_line
                            )
                            self.tgt_lines_layer.data = []
                            self.tgt_points_layer.add(new_point)
                            # if tgt points match src points
                            # new pair is created
                            if len(self.tgt_points_layer.data) == len(
                                self.src_points_layer.data
                            ):
                                self.landmark_pair_index += 1
                                self.landmark_list_box.addItem(
                                    "landmark pair "
                                    + str(self.landmark_pair_index)
                                )

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

    def align_images_btn_clicked(self):
        print("affine matrix:")
        self.src_transformation_matrix = get_affine_matrix_from_landmarks(
            self.src_points_layer.data, self.tgt_points_layer.data
        )
        print(self.src_transformation_matrix)
        self.overlay_image_layer.affine = self.src_transformation_matrix
        self.overlay_btn.setChecked(True)

    def set_overlay_visibility(self):
        if self.overlay_btn.isChecked():
            self.overlay_image_layer.visible = True
        else:
            self.overlay_image_layer.visible = False

    def align_viewers_btn_clicked(self):
        # TODO: incorrect transformation
        new_camera_euler_angles = inverse_rotation_of_camera(
            self.src_transformation_matrix[:3, :3],
            self.tgt_viewer.camera.angles,
        )
        self.src_viewer.camera.angles = new_camera_euler_angles

    def landmark_list_box_item_current_row_changed(self):
        row = self.landmark_list_box.currentRow()
        if row != -1:
            self.src_points_layer.selected_data = {row}
            self.tgt_points_layer.selected_data = {row}
        else:
            self.src_points_layer.selected_data = {}
            self.tgt_points_layer.selected_data = {}
        self.src_points_layer.refresh()
        self.tgt_points_layer.refresh()

    def clear_point_pair_selection(self):
        self.landmark_list_box.setCurrentRow(-1)

    def delete_line_pair(self):
        row = self.landmark_list_box.currentRow()
        if row != -1:
            self.src_points_layer.selected_data = {row}
            self.tgt_points_layer.selected_data = {row}
            self.src_points_layer.remove_selected()
            self.tgt_points_layer.remove_selected()
            self.clear_point_pair_selection()
            self.landmark_list_box.takeItem(row)
