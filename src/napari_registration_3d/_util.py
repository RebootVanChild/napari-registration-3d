import math

import numpy as np
from scipy.optimize import basinhopping


def rigidBodyToMatrix(rotation, translation):
    # in z,y,x order
    m_rotation_z = np.array(
        [
            [math.cos(rotation[2]), -math.sin(rotation[2]), 0, 0],
            [math.sin(rotation[2]), math.cos(rotation[2]), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
    )
    m_rotation_y = np.array(
        [
            [math.cos(rotation[1]), 0, math.sin(rotation[1]), 0],
            [0, 1, 0, 0],
            [-math.sin(rotation[1]), 0, math.cos(rotation[1]), 0],
            [0, 0, 0, 1],
        ]
    )
    m_rotation_x = np.array(
        [
            [1, 0, 0, 0],
            [0, math.cos(rotation[0]), -math.sin(rotation[0]), 0],
            [0, math.sin(rotation[0]), math.cos(rotation[0]), 0],
            [0, 0, 0, 1],
        ]
    )
    m_rotation = m_rotation_z.dot(m_rotation_y).dot(m_rotation_x)
    m_rigidbody = m_rotation
    m_rigidbody[0][3] = translation[0]
    m_rigidbody[1][3] = translation[1]
    m_rigidbody[2][3] = translation[2]
    return m_rigidbody


# line(dot, direction)
def distBetweenLines(line1, line2):
    n = np.cross(line1[1] - line1[0], line2[1] - line2[0])
    return np.linalg.norm(n.dot(line2[0] - line1[0])) / np.linalg.norm(n)


def applyRigidBodyMatrixToLine(line, m_rigidbody):
    p0 = np.append(line[0], 1)
    p1 = np.append(line[1], 1)
    return np.array(
        [m_rigidbody.dot(p0.T)[:-1].T, m_rigidbody.dot(p1.T)[:-1].T]
    )


# params=[rotx, roty, rotz, transx, trany, transz]
def lineDistSquareErr(params, src_lines, tgt_lines):
    rotation = params[0:3]
    translation = params[3:6]
    matrix = rigidBodyToMatrix(rotation, translation)
    squared_err_sum = sum(
        np.square(
            np.array(
                list(
                    map(
                        lambda x, y: distBetweenLines(
                            applyRigidBodyMatrixToLine(x, matrix), y
                        ),
                        src_lines,
                        tgt_lines,
                    )
                )
            )
        )
    )
    return squared_err_sum


def find_rigid_body_4x4_matrix_from_lines(src_lines, tgt_lines):
    x0 = np.array([0, 0, 0, 0, 0, 0])
    minimizer_kwargs = {"method": "BFGS", "args": (src_lines, tgt_lines)}
    res = basinhopping(
        lineDistSquareErr, x0, minimizer_kwargs=minimizer_kwargs, niter=100
    )
    m_found = rigidBodyToMatrix(res.x[0:3], res.x[3:6])
    return m_found