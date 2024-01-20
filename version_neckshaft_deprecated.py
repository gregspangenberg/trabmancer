import trimesh
import shoulder
import shoulder.utils
import pathlib
import numpy as np
from itertools import groupby
import skspatial.objects
import matplotlib.pyplot as plt
import networkx as nx
import plotly.graph_objects as go
import vedo
import time
import pandas as pd


def read_txt_array(filepath):
    # Open the file in read mode
    with open(filepath, "r") as file:
        # Read the file content
        content = file.read()

    # Split the content by newlines to get each line as a list element
    lines = content.split("\n")

    # Iterate through the lines and extract the coordinates
    coordinates = []
    for i, line in enumerate(lines):
        if i < 6:
            continue
        # Check if the line contains coordinates (X, Y, Z)
        if any(x in line for x in ["X", "Y", "Z"]):
            # Split the line by ':' to get the coordinate values
            values = line.split(": ")[1]
            # Split the values by ' ' to get individual X, Y, Z values
            x, y, z = values.split()
            # Convert the values to float and add them to the list of coordinates
            coordinates.append([float(x), float(y), float(z)])
            # break
    # Print the extracted coordinates
    return np.array(coordinates)


def key_func(file_path):
    # Here, we extract the file name without the extension
    # and split it on the "_" character to get the matching part
    return file_path.stem.split("_")[0]


def apply_head_csys(h, anp_ct):
    """transform to apml coordinate sytstem"""
    # anterior is  +x
    # posterior is -x
    # medial is    +y
    # lateral is   -y
    # z is up and down canal

    anp = shoulder.utils.transform_pts(anp_ct, h.transform)

    # fit plane
    plane = skspatial.objects.Plane.best_fit(anp)
    # find rotation so x axis is parallel to plane
    theta = np.arctan2(plane.normal[0], plane.normal[1])
    trfm = np.identity(4)
    trfm[:2, :2] = np.array(
        [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]
    )

    # apply rotation
    h.apply_csys_custom(trfm, from_ct=False)
    anp = shoulder.utils.transform_pts(anp_ct, h.transform)
    plane = skspatial.objects.Plane.best_fit(anp)

    # translate so head center is the origin
    h.apply_translation(-1 * plane.point)

    return h


def convert_apml_vector(ap_ml_z_vector, left=False):
    """
    a is + and p is -, m is + and lateral is -
    converts the ap_ml_z translations to xyz in apml_csys
    h must be in head_csys
    """
    xyz_vector = ap_ml_z_vector.flatten()
    # if a left humeri then the bg will be in -x
    if left:
        # lefts have +anterior in -x dir
        xyz_vector[0] *= -1
    return xyz_vector


def angle(v1, v2, acute):
    # v1 is your firsr vector
    # v2 is your second vector
    angle = np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    if acute == True:
        return angle
    else:
        return 2 * np.pi - angle


t0 = time.time()
# Group the files by the matching part of their name
files = pathlib.Path("../shoulder_data/bones/non_arthritic").glob("*")
grouped_files = []
for key, group in groupby(sorted(files, key=key_func), key=key_func):
    # Convert the group iterator to a list and append it to the result
    grouped_files.append(list(group))

data = []
for i, bone_files in enumerate(grouped_files):
    # grab out the individual files
    stl = [f for f in bone_files if ".stl" in f.name]
    if len(stl) < 2:
        continue
    # extract stl's
    cort_file = [i for i in stl if "humerus" in i.name][0]
    trab_file = [i for i in stl if "trab" in i.name][0]
    print(cort_file.stem)
    # create shoulder model f rom cortical
    h = shoulder.Humerus(cort_file)
    h.canal.axis([0.5, 0.8])
    h.trans_epiconylar.axis()
    h.bicipital_groove.axis()
    h.apply_csys_canal_transepiconylar()

    # detect side
    left_bool = False
    if np.mean(h.bicipital_groove._axis, axis=0)[0] < 0:
        left_bool = True

    # read anatomic neck arrays and transform to csys
    # if anp not present then continue to next
    try:
        anp = [f for f in bone_files if "anp" in f.name][0]
    except:
        continue

    anp_ct = read_txt_array(anp)
    # load landmarks
    anp = shoulder.utils.transform_pts(anp_ct, h.transform)
    anp_plane = skspatial.objects.Plane.best_fit(anp)

    version = angle(anp_plane.normal, np.array([1, 0, 0]), True)
    version = np.rad2deg(version)
    if not left_bool:
        version = 180 - version
    if version > 90:
        version -= 90
    neckshaft = angle(anp_plane.normal, np.array([0, 0, 1]), False)
    neckshaft = np.rad2deg(neckshaft)
    neckshaft -= 180

    data.append([trab_file.stem, version, neckshaft])
    # h = apply_head_csys(h, anp_ct)
    # print(np.cross(np.array([1, 0, 0]), anp_plane.normal))

pd.DataFrame(
    data,
    columns=[
        "name",
        "version",
        "neckshaft",
    ],
).to_csv(f"data/vs_ns_angles.csv")
