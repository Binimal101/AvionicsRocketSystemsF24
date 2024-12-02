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


def interpolate_quaternions(input_data): # give it the points you have in the format below, and it will give you the interpolated data
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
#this is my hardcoded test
if __name__ == "__main__":
    '''input_data = [
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
    ]'''
    input_data = [0.2, {'rotation_w': 1.0, 'rotation_x': -0.00030517578125, 'rotation_y': -6.103515625e-05, 'rotation_z': 0.0}, {'rotation_w': 0.0838623046875, 'rotation_x': 0.323486328125, 'rotation_y': 0.9425048828125, 'rotation_z': 0.00042724609375}, {'rotation_w': 0.08404541015625, 'rotation_x': 0.3233642578125, 'rotation_y': 0.9425048828125, 'rotation_z': 0.00103759765625}, {'rotation_w': 0.08612060546875, 'rotation_x': 0.323974609375, 'rotation_y': 0.942138671875, 'rotation_z': 0.00579833984375}, {'rotation_w': 0.09881591796875, 'rotation_x': 0.32391357421875, 'rotation_y': 0.940673828125, 'rotation_z': 0.0220947265625}, {'rotation_w': 0.125244140625, 'rotation_x': 0.3310546875, 'rotation_y': 0.93426513671875, 'rotation_z': 0.04339599609375}, {'rotation_w': 0.10467529296875, 'rotation_x': 0.33099365234375, 'rotation_y': 0.93695068359375, 'rotation_z': 0.03973388671875}, {'rotation_w': 0.10400390625, 'rotation_x': 0.3292236328125, 'rotation_y': 0.937255859375, 'rotation_z': 0.04833984375}, {'rotation_w': 0.084716796875, 'rotation_x': 0.3380126953125, 'rotation_y': 0.93670654296875, 'rotation_z': 0.0340576171875}, {'rotation_w': 0.05535888671875, 'rotation_x': 0.3316650390625, 'rotation_y': 0.941650390625, 'rotation_z': -0.01702880859375}, {'rotation_w': -0.0029296875, 'rotation_x': 0.32586669921875, 'rotation_y': 0.9404296875, 'rotation_z': -0.09661865234375}, {'rotation_w': -0.060546875, 'rotation_x': 0.32244873046875, 'rotation_y': 0.92266845703125, 'rotation_z': -0.20263671875}, {'rotation_w': -0.0960693359375, 'rotation_x': 0.32061767578125, 'rotation_y': 0.89892578125, 'rotation_z': -0.28277587890625}, {'rotation_w': -0.119873046875, 'rotation_x': 0.3052978515625, 'rotation_y': 0.87884521484375, 'rotation_z': -0.346435546875}, {'rotation_w': -0.14654541015625, 'rotation_x': 0.28955078125, 'rotation_y': 0.84747314453125, 'rotation_z': -0.4039306640625}, {'rotation_w': -0.1875, 'rotation_x': 0.2908935546875, 'rotation_y': 0.81610107421875, 'rotation_z': -0.46282958984375}, {'rotation_w': -0.25634765625, 'rotation_x': 0.30810546875, 'rotation_y': 0.75469970703125, 'rotation_z': -0.51947021484375}, {'rotation_w': -0.3291015625, 'rotation_x': 0.31683349609375, 'rotation_y': 0.69024658203125, 'rotation_z': -0.5611572265625}, {'rotation_w': -0.36810302734375, 'rotation_x': 0.3111572265625, 'rotation_y': 0.62408447265625, 'rotation_z': -0.614990234375}, {'rotation_w': -0.40386962890625, 'rotation_x': 0.30950927734375, 'rotation_y': 0.5467529296875, 'rotation_z': -0.6649169921875}, {'rotation_w': -0.4368896484375, 'rotation_x': 0.29205322265625, 'rotation_y': 0.46771240234375, 'rotation_z': -0.710693359375}, {'rotation_w': -0.4739990234375, 'rotation_x': 0.276611328125, 'rotation_y': 0.38787841796875, 'rotation_z': -0.74053955078125}, {'rotation_w': -0.5047607421875, 'rotation_x': 0.27447509765625, 'rotation_y': 0.30120849609375, 'rotation_z': -0.76104736328125}, {'rotation_w': -0.51824951171875, 'rotation_x': 0.27593994140625, 'rotation_y': 0.2579345703125, 'rotation_z': -0.76727294921875}, {'rotation_w': -0.483154296875, 'rotation_x': 0.27716064453125, 'rotation_y': 0.320556640625, 'rotation_z': -0.76611328125}, {'rotation_w': -0.4090576171875, 'rotation_x': 0.2803955078125, 'rotation_y': 0.47882080078125, 'rotation_z': -0.72442626953125}, {'rotation_w': -0.3092041015625, 'rotation_x': 0.321533203125, 'rotation_y': 0.633056640625, 'rotation_z': -0.63262939453125}, {'rotation_w': -0.2374267578125, 'rotation_x': 0.3604736328125, 'rotation_y': 0.728759765625, 'rotation_z': -0.53155517578125}, {'rotation_w': -0.1456298828125, 'rotation_x': 0.38916015625, 'rotation_y': 0.80487060546875, 'rotation_z': -0.42376708984375}, {'rotation_w': -0.009765625, 'rotation_x': 0.416748046875, 'rotation_y': 0.8687744140625, 'rotation_z': -0.26715087890625}, {'rotation_w': 0.10540771484375, 'rotation_x': 0.45733642578125, 'rotation_y': 0.8792724609375, 'rotation_z': -0.08154296875}, {'rotation_w': 0.140625, 'rotation_x': 0.46734619140625, 'rotation_y': 0.87213134765625, 'rotation_z': 0.033935546875}, {'rotation_w': 0.11688232421875, 'rotation_x': 0.36907958984375, 'rotation_y': 0.9215087890625, 'rotation_z': 0.03155517578125}, {'rotation_w': 0.0772705078125, 'rotation_x': 0.2454833984375, 'rotation_y': 0.9661865234375, 'rotation_z': 0.01629638671875}, {'rotation_w': 0.039794921875, 'rotation_x': 0.12127685546875, 'rotation_y': 0.99176025390625, 'rotation_z': 0.00872802734375}, {'rotation_w': -0.00164794921875, 'rotation_x': -0.39532470703125, 'rotation_y': 0.91851806640625, 'rotation_z': 0.0032958984375}, {'rotation_w': -0.0289306640625, 'rotation_x': -0.4696044921875, 'rotation_y': 0.88232421875, 'rotation_z': -0.01214599609375}, {'rotation_w': -0.04107666015625, 'rotation_x': -0.53369140625, 'rotation_y': 0.8446044921875, 'rotation_z': -0.008544921875}, {'rotation_w': -0.01123046875, 'rotation_x': -0.576416015625, 'rotation_y': 0.81707763671875, 'rotation_z': -0.00616455078125}, {'rotation_w': 0.004150390625, 'rotation_x': -0.621337890625, 'rotation_y': 0.783447265625, 'rotation_z': 0.01123046875}, {'rotation_w': 0.0184326171875, 'rotation_x': -0.6448974609375, 'rotation_y': 0.7635498046875, 'rotation_z': 0.02838134765625}, {'rotation_w': 0.0321044921875, 'rotation_x': -0.62823486328125, 'rotation_y': 0.77703857421875, 'rotation_z': 0.02386474609375}, {'rotation_w': 0.06494140625, 'rotation_x': -0.53582763671875, 'rotation_y': 0.841796875, 'rotation_z': 0.00048828125}, {'rotation_w': 0.1038818359375, 'rotation_x': -0.41473388671875, 'rotation_y': 0.90399169921875, 'rotation_z': 0.00567626953125}, {'rotation_w': 0.1065673828125, 'rotation_x': -0.20086669921875, 'rotation_y': 0.9735107421875, 'rotation_z': 0.02294921875}, {'rotation_w': 0.0899658203125, 'rotation_x': 0.005126953125, 'rotation_y': 0.98797607421875, 'rotation_z': -0.01763916015625}, {'rotation_w': 0.08197021484375, 'rotation_x': 0.1566162109375, 'rotation_y': 0.982421875, 'rotation_z': -0.0596923828125}, {'rotation_w': 0.01690673828125, 'rotation_x': 0.18505859375, 'rotation_y': 0.9412841796875, 'rotation_z': -0.281982421875}, {'rotation_w': -0.19207763671875, 'rotation_x': 0.19464111328125, 'rotation_y': 0.83538818359375, 'rotation_z': -0.47674560546875}, {'rotation_w': -0.41815185546875, 'rotation_x': 0.26068115234375, 'rotation_y': 0.6820068359375, 'rotation_z': -0.5404052734375}, {'rotation_w': -0.62579345703125, 'rotation_x': 0.3157958984375, 'rotation_y': 0.5340576171875, 'rotation_z': -0.47271728515625}, {'rotation_w': -0.74005126953125, 'rotation_x': 0.31268310546875, 'rotation_y': 0.42437744140625, 'rotation_z': -0.417724609375}, {'rotation_w': -0.821044921875, 'rotation_x': 0.26593017578125, 'rotation_y': 0.3238525390625, 'rotation_z': -0.38763427734375}, {'rotation_w': -0.7869873046875, 'rotation_x': 0.2623291015625, 'rotation_y': 0.313720703125, 'rotation_z': -0.46197509765625}, {'rotation_w': -0.6273193359375, 'rotation_x': 0.3651123046875, 'rotation_y': 0.2249755859375, 'rotation_z': -0.6500244140625}, {'rotation_w': -0.4736328125, 'rotation_x': 0.43157958984375, 'rotation_y': 0.1224365234375, 'rotation_z': -0.75787353515625}, {'rotation_w': -0.30853271484375, 'rotation_x': 0.50299072265625, 'rotation_y': 0.1229248046875, 'rotation_z': -0.79791259765625}, {'rotation_w': -0.1202392578125, 'rotation_x': 0.54608154296875, 'rotation_y': 0.39178466796875, 'rotation_z': -0.73065185546875}, {'rotation_w': 0.0174560546875, 'rotation_x': 0.54949951171875, 'rotation_y': 0.56561279296875, 'rotation_z': -0.6146240234375}, {'rotation_w': 0.09661865234375, 'rotation_x': 0.4578857421875, 'rotation_y': 0.76934814453125, 'rotation_z': -0.43487548828125}, {'rotation_w': 0.1546630859375, 'rotation_x': 0.33880615234375, 'rotation_y': 0.90240478515625, 'rotation_z': -0.216796875}, {'rotation_w': 0.17413330078125, 'rotation_x': 0.20477294921875, 'rotation_y': 0.963134765625, 'rotation_z': 0.0126953125}, {'rotation_w': 0.1846923828125, 'rotation_x': 0.09417724609375, 'rotation_y': 0.95831298828125, 'rotation_z': 0.18896484375}, {'rotation_w': 0.07696533203125, 'rotation_x': 0.16510009765625, 'rotation_y': 0.9033203125, 'rotation_z': 0.3883056640625}, {'rotation_w': -0.08074951171875, 'rotation_x': 0.359130859375, 'rotation_y': 0.78936767578125, 'rotation_z': 0.49127197265625}, {'rotation_w': -0.1905517578125, 'rotation_x': 0.6234130859375, 'rotation_y': 0.63177490234375, 'rotation_z': 0.41937255859375}, {'rotation_w': -0.2462158203125, 'rotation_x': 0.8243408203125, 'rotation_y': 0.43463134765625, 'rotation_z': 0.2662353515625}, {'rotation_w': -0.32501220703125, 'rotation_x': 0.9267578125, 'rotation_y': 0.186279296875, 'rotation_z': -0.02813720703125}, {'rotation_w': -0.34356689453125, 'rotation_x': 0.8760986328125, 'rotation_y': -0.1519775390625, 'rotation_z': -0.30218505859375}, {'rotation_w': -0.30987548828125, 'rotation_x': 0.7410888671875, 'rotation_y': -0.38226318359375, 'rotation_z': -0.45672607421875}, {'rotation_w': -0.20941162109375, 'rotation_x': 0.68182373046875, 'rotation_y': -0.46966552734375, 'rotation_z': -0.520263671875}, {'rotation_w': -0.096435546875, 'rotation_x': 0.6798095703125, 'rotation_y': -0.47943115234375, 'rotation_z': -0.54656982421875}, {'rotation_w': -0.1097412109375, 'rotation_x': 0.72479248046875, 'rotation_y': -0.4208984375, 'rotation_z': -0.53424072265625}, {'rotation_w': -0.25836181640625, 'rotation_x': 0.815673828125, 'rotation_y': -0.10626220703125, 'rotation_z': -0.506591796875}, {'rotation_w': -0.2066650390625, 'rotation_x': 0.777587890625, 'rotation_y': 0.43328857421875, 'rotation_z': -0.40606689453125}, {'rotation_w': -0.0064697265625, 'rotation_x': 0.57177734375, 'rotation_y': 0.805908203125, 'rotation_z': -0.15325927734375}, {'rotation_w': 0.083984375, 'rotation_x': 0.26092529296875, 'rotation_y': 0.9564208984375, 'rotation_z': 0.10040283203125}, {'rotation_w': 0.0811767578125, 'rotation_x': -0.01007080078125, 'rotation_y': 0.95269775390625, 'rotation_z': 0.292724609375}, {'rotation_w': 0.01031494140625, 'rotation_x': -0.05255126953125, 'rotation_y': 0.8941650390625, 'rotation_z': 0.44451904296875}, {'rotation_w': -0.1197509765625, 'rotation_x': 0.06170654296875, 'rotation_y': 0.77008056640625, 'rotation_z': 0.624267578125}, {'rotation_w': -0.1805419921875, 'rotation_x': 0.08685302734375, 'rotation_y': 0.66693115234375, 'rotation_z': 0.7176513671875}, {'rotation_w': -0.2081298828125, 'rotation_x': 0.03173828125, 'rotation_y': 0.5504150390625, 'rotation_z': 0.80792236328125}, {'rotation_w': -0.14971923828125, 'rotation_x': -0.063232421875, 'rotation_y': 0.51458740234375, 'rotation_z': 0.8419189453125}, {'rotation_w': 0.02081298828125, 'rotation_x': -0.2183837890625, 'rotation_y': 0.5401611328125, 'rotation_z': 0.81243896484375}, {'rotation_w': 0.17034912109375, 'rotation_x': -0.32379150390625, 'rotation_y': 0.563232421875, 'rotation_z': 0.7408447265625}, {'rotation_w': 0.25146484375, 'rotation_x': -0.42156982421875, 'rotation_y': 0.61920166015625, 'rotation_z': 0.61285400390625}, {'rotation_w': 0.20794677734375, 'rotation_x': -0.522216796875, 'rotation_y': 0.71954345703125, 'rotation_z': 0.4078369140625}, {'rotation_w': 0.10919189453125, 'rotation_x': -0.57269287109375, 'rotation_y': 0.780517578125, 'rotation_z': 0.22552490234375}, {'rotation_w': -0.03277587890625, 'rotation_x': -0.58477783203125, 'rotation_y': 0.80938720703125, 'rotation_z': 0.04315185546875}, {'rotation_w': -0.13006591796875, 'rotation_x': -0.47454833984375, 'rotation_y': 0.86920166015625, 'rotation_z': -0.0484619140625}, {'rotation_w': -0.26031494140625, 'rotation_x': -0.31597900390625, 'rotation_y': 0.89605712890625, 'rotation_z': -0.1715087890625}, {'rotation_w': -0.36163330078125, 'rotation_x': -0.0574951171875, 'rotation_y': 0.87481689453125, 'rotation_z': -0.31719970703125}, {'rotation_w': -0.4593505859375, 'rotation_x': 0.19488525390625, 'rotation_y': 0.7677001953125, 'rotation_z': -0.40203857421875}, {'rotation_w': -0.57293701171875, 'rotation_x': 0.43084716796875, 'rotation_y': 0.5614013671875, 'rotation_z': -0.41351318359375}, {'rotation_w': -0.63262939453125, 'rotation_x': 0.57427978515625, 'rotation_y': 0.3330078125, 'rotation_z': -0.39886474609375}, {'rotation_w': -0.66680908203125, 'rotation_x': 0.65228271484375, 'rotation_y': 0.11444091796875, 'rotation_z': -0.34173583984375}, {'rotation_w': -0.63067626953125, 'rotation_x': 0.72064208984375, 'rotation_y': -0.08660888671875, 'rotation_z': -0.27459716796875}, {'rotation_w': -0.54058837890625, 'rotation_x': 0.74920654296875, 'rotation_y': -0.11492919921875, 'rotation_z': -0.36505126953125}, {'rotation_w': -0.511474609375, 'rotation_x': 0.74609375, 'rotation_y': -0.1326904296875, 'rotation_z': -0.4051513671875}, {'rotation_w': -0.53887939453125, 'rotation_x': 0.7396240234375, 'rotation_y': -0.0770263671875, 'rotation_z': -0.395751953125}, {'rotation_w': -0.50628662109375, 'rotation_x': 0.72271728515625, 'rotation_y': 0.1956787109375, 'rotation_z': -0.42791748046875}, {'rotation_w': -0.32427978515625, 'rotation_x': 0.5760498046875, 'rotation_y': -1.36029052734375, 'rotation_z': -0.3922119140625}, {'rotation_w': -0.0748291015625, 'rotation_x': 0.33807373046875, 'rotation_y': 0.91375732421875, 'rotation_z': -0.2125244140625}, {'rotation_w': 0.19012451171875, 'rotation_x': 0.0379638671875, 'rotation_y': 0.97381591796875, 'rotation_z': -0.11859130859375}, {'rotation_w': 0.22918701171875, 'rotation_x': -0.18255615234375, 'rotation_y': 0.94842529296875, 'rotation_z': 0.1209716796875}, {'rotation_w': 0.07916259765625, 'rotation_x': -0.12042236328125, 'rotation_y': 0.89129638671875, 'rotation_z': 0.429931640625}, {'rotation_w': -0.035888671875, 'rotation_x': -0.01953125, 'rotation_y': 0.76910400390625, 'rotation_z': 0.6378173828125}, {'rotation_w': -0.17510986328125, 'rotation_x': 0.2197265625, 'rotation_y': 0.706787109375, 'rotation_z': 0.64923095703125}, {'rotation_w': -0.22601318359375, 'rotation_x': 0.5072021484375, 'rotation_y': 0.7308349609375, 'rotation_z': 0.39691162109375}, {'rotation_w': -0.14459228515625, 'rotation_x': 0.388427734375, 'rotation_y': 0.83428955078125, 'rotation_z': 0.363525390625}, {'rotation_w': 0.11102294921875, 'rotation_x': -0.0264892578125, 'rotation_y': 0.971435546875, 'rotation_z': 0.20806884765625}, {'rotation_w': 0.15478515625, 'rotation_x': -0.3687744140625, 'rotation_y': 0.91107177734375, 'rotation_z': 0.10003662109375}, {'rotation_w': 0.03924560546875, 'rotation_x': -0.44183349609375, 'rotation_y': 0.8795166015625, 'rotation_z': 0.1722412109375}, {'rotation_w': -0.04754638671875, 'rotation_x': -0.25567626953125, 'rotation_y': 0.802490234375, 'rotation_z': 0.53704833984375}, {'rotation_w': -0.07916259765625, 'rotation_x': -0.1689453125, 'rotation_y': 0.7587890625, 'rotation_z': 0.62408447265625}, {'rotation_w': 0.0650634765625, 'rotation_x': -0.340087890625, 'rotation_y': 0.88330078125, 'rotation_z': 0.3160400390625}, {'rotation_w': 0.19659423828125, 'rotation_x': -0.4107666015625, 'rotation_y': 0.8837890625, 'rotation_z': 0.10772705078125}, {'rotation_w': 0.07598876953125, 'rotation_x': -0.23919677734375, 'rotation_y': 0.863525390625, 'rotation_z': 0.43743896484375}, {'rotation_w': -0.0360107421875, 'rotation_x': -0.125732421875, 'rotation_y': 0.81939697265625, 'rotation_z': 0.55810546875}, {'rotation_w': 0.04339599609375, 'rotation_x': -0.272705078125, 'rotation_y': 0.94012451171875, 'rotation_z': 0.199951171875}, {'rotation_w': 0.06890869140625, 'rotation_x': -0.28759765625, 'rotation_y': 0.95037841796875, 'rotation_z': 0.0965576171875}, {'rotation_w': 0.0631103515625, 'rotation_x': -0.24090576171875, 'rotation_y': 0.95703125, 'rotation_z': 0.14862060546875}, {'rotation_w': 0.07403564453125, 'rotation_x': -0.182861328125, 'rotation_y': 0.96038818359375, 'rotation_z': 0.19671630859375}, {'rotation_w': 0.103759765625, 'rotation_x': -0.1375732421875, 'rotation_y': 0.9622802734375, 'rotation_z': 0.21051025390625}]


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

