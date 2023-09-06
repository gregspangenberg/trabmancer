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


t0 = time.time()
# Group the files by the matching part of their name
files = pathlib.Path("../shoulder_data/bones/non_arthritic").glob("*")
grouped_files = []
for key, group in groupby(sorted(files, key=key_func), key=key_func):
    # Convert the group iterator to a list and append it to the result
    grouped_files.append(list(group))

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

    # read anatomic neck arrays and transform to csys
    # if anp not present then continue to next
    try:
        anp = [f for f in bone_files if "anp" in f.name][0]
    except:
        continue

    anp_ct = read_txt_array(anp)
    h = apply_head_csys(h, anp_ct)

    # load landmarks
    anp = shoulder.utils.transform_pts(anp_ct, h.transform)
    anp_plane = skspatial.objects.Plane.best_fit(anp)
    surgical_neck = h.bicipital_groove.surgical_neck
    surgical_neck_pt = np.mean(surgical_neck, axis=0)

    # detect side
    left_bool = False
    if np.mean(h.bicipital_groove._axis, axis=0)[0] < 0:
        left_bool = True

    # load transformed meshes
    cort = h.mesh.copy()
    trab = trimesh.load_mesh(trab_file).apply_transform(h.transform)

    # iterate through variations
    ap_dir = np.arange(-5, 6, step=1)
    ml_dir = np.arange(-5, 6, step=1)
    depth = np.arange(-5, 6, step=1)
    ns_angles = np.arange(-10, 11, step=1)
    vs_angles = np.arange(-10, 11, step=1)

    data = []
    for depth_incr in depth:
        for ns_angle_incr in ns_angles:
            for vs_angle_incr in vs_angles:
                # increment position
                cut_plane_point = anp_plane.point

                # increment depth
                cut_plane_point = cut_plane_point + (depth_incr * anp_plane.normal)
                # increments neck shaft and version angles
                # spherical coordinates are [radius, ns angle-90, version], all in radians
                cut_plane_normal = anp_plane.normal.reshape(-1, 3)
                sphr = vedo.cart2spher(
                    cut_plane_normal[:, 0],
                    cut_plane_normal[:, 1],
                    cut_plane_normal[:, 2],
                )
                sphr[1:, :] = np.rad2deg(sphr[1:, :])  # convert to degrees
                sphr[1, :] += ns_angle_incr  # increment neck-shaft angle
                sphr[2, :] += vs_angle_incr  # increment version
                sphr[1:, :] = np.deg2rad(sphr[1:, :])  # convert to radians
                sphr = sphr.flatten()
                # convert back to cartesian
                cut_plane_normal = vedo.spher2cart(sphr[0], sphr[1], sphr[2])
                # compensate for right left differences in a-p
                cut_plane_normal = convert_apml_vector(cut_plane_normal, left=left_bool)

                # cut the trab at the anp and surgical neck
                trab_cut = trab
                # trab_cut = trab.slice_plane(
                #     plane_origin=cut_plane_point,
                #     plane_normal=-1 * cut_plane_normal,
                # )
                # trab_cut = trab_cut.slice_plane(
                #     plane_origin=surgical_neck_pt, plane_normal=[0, 0, 1]
                # )
                # convert to vedo
                trab_cut = vedo.trimesh2vedo(trab_cut)
                # create hemisphere
                implant = (
                    vedo.Sphere(c="grey4", alpha=0.8).scale(1).pos(cut_plane_point)
                )
                implant.cut_with_plane(
                    origin=cut_plane_point, normal=-1 * cut_plane_normal
                )

                for ap_incr in ap_dir:
                    for ml_incr in ml_dir:
                        # translate
                        implant_center = cut_plane_point.copy()
                        implant_center[0] += ap_incr
                        ml_vector = np.cross(np.array([1, 0, 0]), anp_plane.normal)
                        implant_center += ml_incr * ml_vector
                        implant_center = convert_apml_vector(
                            implant_center, left=left_bool
                        )

                        # cast ray along -normal
                        ray = vedo.spher2cart(1000, sphr[1], sphr[2])
                        intersect = trab_cut.intersect_with_line(
                            implant_center, implant_center - ray
                        )
                        if len(intersect):
                            ray_dist = vedo.mag(intersect[0] - implant_center)

                        else:
                            ray_dist = 0
                            print("fail")

                        data.append(
                            [
                                depth_incr,
                                ns_angle_incr,
                                vs_angle_incr,
                                ap_incr,
                                ml_incr,
                                ray_dist,
                            ]
                        )

                    # compute all distances
                    # distances = trab_cut.distance_to(implant, signed=True)
                    # trab_cut.cmap("hot").add_scalarbar("Signed\nDistance")
                    # vedo.show(
                    #     trab_cut, implant, __doc__, axes=1, size=(1000, 500), zoom=1.5
                    # ).close()
    print(f"{trab_file.stem} took {time.time() - t0:.2f} seconds")
    # data = np.array(data)
    pd.DataFrame(
        data,
        columns=[
            "depth",
            "ns_angle",
            "vs_angle",
            "ap_translation",
            "ml_translation",
            "ray_dist",
        ],
    ).to_csv(f"data/{trab_file.stem}.csv")
