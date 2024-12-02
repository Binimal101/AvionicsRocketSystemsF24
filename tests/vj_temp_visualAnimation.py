#THIS IS USED TO VISUALIZE THE FRAMERATE OF INTERPOLATED DATA
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Function to convert quaternion to rotation matrix
def quaternion_to_rotation_matrix(q):
    """
    Convert a quaternion to a 3x3 rotation matrix.
    :param q: Quaternion [w, x, y, z]
    :return: 3x3 rotation matrix
    """
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y**2 + z**2), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x**2 + z**2), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x**2 + y**2)]
    ])

# Function to animate 3D rotation
def animate_rotation(quaternions, interval=100):
    """
    Animate a 3D object rotation based on quaternion data.
    :param quaternions: List of quaternions
    :param interval: Time between frames in milliseconds
    """
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    # Initial object: a 3D arrow represented by its direction vector
    vector = np.array([1, 0, 0])  # Start pointing along X-axis
    arrow, = ax.plot([0, vector[0]], [0, vector[1]], [0, vector[2]], color='r', lw=3)

    def update(frame):
        rotation_matrix = quaternion_to_rotation_matrix(quaternions[frame])
        rotated_vector = rotation_matrix @ vector
        arrow.set_data([0, rotated_vector[0]], [0, rotated_vector[1]])
        arrow.set_3d_properties([0, rotated_vector[2]])
        return arrow,

    ani = FuncAnimation(fig, update, frames=len(quaternions), interval=interval, blit=True)
    plt.show()

# Example quaternion data for testing
quaternion_data = [
    [1.0, 0.0, 0.0, 0.0],        # Starting position (identity quaternion)
    [0.923, 0.382, 0.0, 0.0],    # Pitch 45 degrees
    [0.707, 0.707, 0.0, 0.0],    # Pitch 90 degrees
    [0.5, 0.866, 0.0, 0.0],      # Pitch 120 degrees
    [0.0, 1.0, 0.0, 0.0],        # Pitch 180 degrees
    [-0.5, 0.866, 0.0, 0.0],     # Pitch 240 degrees
    [-0.707, 0.707, 0.0, 0.0],   # Pitch 270 degrees
    [-0.923, 0.382, 0.0, 0.0],   # Pitch 315 degrees
    [-1.0, 0.0, 0.0, 0.0],       # Pitch 360 degrees (back to starting rotation)
    [-0.923, 0.0, 0.382, 0.0],   # Yaw 45 degrees
    [-0.707, 0.0, 0.707, 0.0],   # Yaw 90 degrees
    [-0.5, 0.0, 0.866, 0.0],     # Yaw 120 degrees
    [0.0, 0.0, 1.0, 0.0],        # Yaw 180 degrees
    [0.5, 0.0, 0.866, 0.0],      # Yaw 240 degrees
    [0.707, 0.0, 0.707, 0.0],    # Yaw 270 degrees
    [0.923, 0.0, 0.382, 0.0],    # Yaw 315 degrees
    [1.0, 0.0, 0.0, 0.0],        # Yaw 360 degrees (back to starting rotation)
    [0.923, 0.0, 0.0, 0.382],    # Roll 45 degrees
    [0.707, 0.0, 0.0, 0.707],    # Roll 90 degrees
    [0.5, 0.0, 0.0, 0.866],      # Roll 120 degrees
    [0.0, 0.0, 0.0, 1.0],        # Roll 180 degrees
    [-0.5, 0.0, 0.0, 0.866],     # Roll 240 degrees
    [-0.707, 0.0, 0.0, 0.707],   # Roll 270 degrees
    [-0.923, 0.0, 0.0, 0.382],   # Roll 315 degrees
    [-1.0, 0.0, 0.0, 0.0]        # Roll 360 degrees (back to starting rotation)
]


# Visualize rotation based on quaternion data
animate_rotation(quaternion_data)
