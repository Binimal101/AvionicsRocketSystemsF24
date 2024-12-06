import numpy as np
from math import acos, sin, cos

class Interpolate:
    def __init__(self, fps = 20):
        self.lastquaternion = None
        self.fps = fps

    def slerp(self, q1: list, q2: list, t) -> list: # math used to interpolate quanterions
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

        return (q1 * cos(theta) + q_perp * sin(theta))

    def interpolate_quaternion(self, time_delta: float, quaternion) -> list: # This is the method you would call for the interpolated data, returns a list of list with the original and interpolated data
        """
        Interpolates between quaternions in the input data using SLERP and includes the original quaternions.
        
        :param input_data: List containing timeDelta and a sequence of quaternion dictionaries.
        :return: List of quaternions including both original and interpolated quaternions.
        """
        
        if self.lastquaternion is None:
            self.lastquaternion = quaternion
            return [quaternion]
        
        # Convert quaternion dictionaries to numpy arrays
            
        quat_array = [
            self.lastquaternion, 
            [quaternion["rotation_w"], quaternion["rotation_x"], quaternion["rotation_y"], quaternion["rotation_z"]]
        ]

        # Calculate the number of interpolation steps to maintain 10 FPS
        num_steps = int(time_delta * self.fps)

        # Combine original and interpolated quaternions
        combined_quats = []

        for i in range(len(quat_array) - 1): #should only run once
            q1 = quat_array[i]
            q2 = quat_array[i + 1]

            # Add the original quaternion
            if i == 0:
                combined_quats.append(q1)

            # Interpolate between q1 and q2
            for step in range(1, num_steps):
                t = step / num_steps
                interpolated_quat = self.slerp(q1, q2, t)
                combined_quats.append(interpolated_quat)

            # Ensure the last quaternion of the pair is added only once
            combined_quats.append(q2)
            self.lastquaternion = q2

        return combined_quats