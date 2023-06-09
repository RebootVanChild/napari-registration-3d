import numpy as np


# mid point of shortest line
def mid_point_of_shortest_line(line1, line2):
    p1 = line1[0]
    v1 = line1[1] - line1[0]
    p2 = line2[0]
    v2 = line2[1] - line2[0]
    n = np.cross(v1, v2)
    a = np.array([v1, -v2, n]).T
    b = np.array(p2 - p1).T
    x = np.linalg.solve(a, b)
    endpoint1 = p1 + x[0] * v1
    endpoint2 = p2 + x[1] * v2
    midpoint = (endpoint1 + endpoint2) / 2
    return midpoint


def get_affine_matrix_from_landmarks(
    source_points_landmarks, target_points_landmarks
):
    pts_count = len(source_points_landmarks)
    A = np.zeros((pts_count * 3, 12))
    b = np.zeros(pts_count * 3)
    for i in range(pts_count):
        # build A
        A[i * 3][0] = source_points_landmarks[i][0]
        A[i * 3][1] = source_points_landmarks[i][1]
        A[i * 3][2] = source_points_landmarks[i][2]
        A[i * 3][3] = 1
        A[i * 3 + 1][4] = source_points_landmarks[i][0]
        A[i * 3 + 1][5] = source_points_landmarks[i][1]
        A[i * 3 + 1][6] = source_points_landmarks[i][2]
        A[i * 3 + 1][7] = 1
        A[i * 3 + 2][8] = source_points_landmarks[i][0]
        A[i * 3 + 2][9] = source_points_landmarks[i][1]
        A[i * 3 + 2][10] = source_points_landmarks[i][2]
        A[i * 3 + 2][11] = 1
        # build b
        b[i * 3] = target_points_landmarks[i, 0]
        b[i * 3 + 1] = target_points_landmarks[i, 1]
        b[i * 3 + 2] = target_points_landmarks[i, 2]
    x = np.linalg.solve(np.dot(A.T, A), np.dot(A.T, b.T))
    matrix = np.append(x.reshape(3, 4), [[0.0, 0.0, 0.0, 1.0]], axis=0)
    print(matrix)
    return matrix


def rot_matrix_zyx_to_xyz(matrixZYX):
    matrixXYZ = np.rot90(matrixZYX, 2)
    return matrixXYZ


def rot_matrix_xyz_to_zyx(matrixXYZ):
    matrixZYX = np.rot90(matrixXYZ, 2)
    return matrixZYX
