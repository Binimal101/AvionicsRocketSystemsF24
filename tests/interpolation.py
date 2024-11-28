import numpy as np
from math import acos, sin, cos
import reyax_test as reyax


def slerp(q1, q2, t):
    """
    Perform Spherical Linear Interpolation (SLERP) between two quaternions.
    
    :param q1: Starting quaternion as a numpy array [w, x, y, z].
    :param q2: Ending quaternion as a numpy array [w, x, y, z].
    :param t: Interpolation factor (0 <= t <= 1).
    :return: Interpolated quaternion as a numpy array [w, x, y, z].
    """
    q1 = np.array(q1)
    q2 = np.array(q2)

    # Normalize quaternions
    q1 /= np.linalg.norm(q1)
    q2 /= np.linalg.norm(q2)

    # Compute the cosine of the angle between quaternions
    dot = np.dot(q1, q2)

    # Ensure the shortest path is taken
    if dot < 0.0:
        q2 = -q2
        dot = -dot

    # If quaternions are too close, use linear interpolation
    if dot > 0.9995:
        return (1.0 - t) * q1 + t * q2

    # Calculate the angle between the quaternions
    theta_0 = acos(dot)
    theta = theta_0 * t

    # Compute the interpolated quaternion
    q_perp = q2 - q1 * dot
    q_perp /= np.linalg.norm(q_perp)

    return q1 * cos(theta) + q_perp * sin(theta)

'''
def interpolate_quaternions(input_data):
    """
    Interpolates between quaternions in the input data using SLERP.

    :param input_data: List containing timeDelta and a sequence of quaternion dictionaries.
    :return: List of interpolated quaternions.
    """
    time_delta = input_data[0]
    quaternions = input_data[1:]

    # Convert quaternion dictionaries to numpy arrays
    quat_array = [
        [q["rotation_w"], q["rotation_x"], q["rotation_y"], q["rotation_z"]]
        for q in quaternions
    ]

    # Calculate the number of interpolation steps to maintain 10 FPS
    fps = 10
    num_steps = int(time_delta * fps)

    interpolated_quats = []

    for i in range(len(quat_array) - 1):
        q1 = quat_array[i]
        q2 = quat_array[i + 1]

        # Interpolate between q1 and q2
        for step in range(num_steps):
            t = step / num_steps
            interpolated_quat = slerp(q1, q2, t)
            interpolated_quats.append(interpolated_quat)

    # Add the last quaternion explicitly to ensure continuity
    interpolated_quats.append(quat_array[-1])

    return interpolated_quats
'''
def interpolate_quaternions(input_data):
    """
    Interpolates between quaternions in the input data using SLERP and includes the original quaternions.
    
    :param input_data: List containing timeDelta and a sequence of quaternion dictionaries.
    :return: List of quaternions including both original and interpolated quaternions.
    """
    time_delta = input_data[0]
    quaternions = input_data[1:]

    # Convert quaternion dictionaries to numpy arrays
    quat_array = [
        [q["rotation_w"], q["rotation_x"], q["rotation_y"], q["rotation_z"]]
        for q in quaternions
    ]

    # Calculate the number of interpolation steps to maintain 10 FPS
    fps = 10
    num_steps = int(time_delta * fps)

    # Combine original and interpolated quaternions
    combined_quats = []

    for i in range(len(quat_array) - 1):
        q1 = quat_array[i]
        q2 = quat_array[i + 1]

        # Add the original quaternion
        if i == 0:
            combined_quats.append(q1)

        # Interpolate between q1 and q2
        for step in range(1, num_steps):
            t = step / num_steps
            interpolated_quat = slerp(q1, q2, t)
            combined_quats.append(interpolated_quat)

        # Ensure the last quaternion of the pair is added only once
        combined_quats.append(q2)

    return combined_quats



# data would be from method recieve(self)

if __name__ == "__main__":
    input_data = [
        0.4,  # timeDelta
        {
            "rotation_w": 0.23356,
            "rotation_x": -0.1234,
            "rotation_y": 1.0,
            "rotation_z": 0.0
        },
        {
            "rotation_w": 0.64234,
            "rotation_x": 0.93434,
            "rotation_y": 0.34544,
            "rotation_z": 0.2343256
        },{
            "rotation_w": 0.12342,
            "rotation_x": 0.694,
            "rotation_y": 0.4547,
            "rotation_z": 0.0
        },{
            "rotation_w": -0.23356,
            "rotation_x": -0.0990,
            "rotation_y": -1.0,
            "rotation_z": 0.2093903
        }
    ]

    combined = interpolate_quaternions(input_data) # the data we need
    for q in combined:
        print(q)

def graphData(combined): # not needed, will delete later 
    return combined

# Adjust the test interpretation to align with the observed extra frame behavior
#don't need, to test if its more then 10 frames per second



# a cool way I could display data on my end, don't feel like it
'''
Time: 0.00, Quaternion: [1.0, -0.00030517578125, -6.103515625e-05, 0.0]
Time: 0.10, Quaternion: [7.36212800e-01 2.19520598e-01 6.40154400e-01 2.90206645e-04]
Time: 0.20, Quaternion: [0.0838623046875, 0.323486328125, 0.9425048828125, 0.00042724609375]
Time: 0.30, Quaternion: [8.39545279e-02 3.23427876e-01 9.42512410e-01 7.32427724e-04]
Time: 0.40, Quaternion: [0.08404541015625, 0.3233642578125, 0.9425048828125, 0.00103759765625]
Time: 0.60, Quaternion: [0.08612060546875, 0.323974609375, 0.942138671875, 0.00579833984375]
Time: 0.70, Quaternion: [0.09247235 0.32395841 0.94144787 0.01394715]
Time: 0.80, Quaternion: [0.09881591796875, 0.32391357421875, 0.940673828125, 0.0220947265625]
Time: 1.00, Quaternion: [0.125244140625, 0.3310546875, 0.93426513671875, 0.04339599609375]
Time: 1.20, Quaternion: [0.10467529296875, 0.33099365234375, 0.93695068359375, 0.03973388671875]
Time: 1.40, Quaternion: [0.10400390625, 0.3292236328125, 0.937255859375, 0.04833984375]
'''

