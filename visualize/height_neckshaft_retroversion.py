import vedo
import shoulder
import pathlib
import numpy as np
from itertools import groupby


def key_func(file_path):
    # Here, we extract the file name without the extension
    # and split it on the "_" character to get the matching part
    return file_path.stem.split("_")[0]


files = pathlib.Path("../shoulder_data/bones/non_arthritic").glob("*")
grouped_files = []
for key, group in groupby(sorted(files, key=key_func), key=key_func):
    # Convert the group iterator to a list and append it to the result
    grouped_files.append(list(group))

for i, bone_files in enumerate(grouped_files):
    if i in [0, 1]:
        continue
    # grab out the individual files
    stl = [f for f in bone_files if ".stl" in f.name]

    # extract stl's
    cort_file = [i for i in stl if "humerus" in i.name][0]
    trab_file = [i for i in stl if "trab" in i.name][0]
    print(cort_file.stem)

    # create shoulder model from cortical
    h = shoulder.Humerus(cort_file)
    # h.apply_csys_canal_transepiconylar()
    h.apply_csys_canal_articular()
    anp = h.anatomic_neck.plane()

    hv = vedo.trimesh2vedo(h.mesh)

    ost = shoulder.HumeralHeadOsteotomy(h)
    ost.offset_depth_anp_normal(-5)
    ost.offest_neckshaft(10)

    plane_og = ost.plane
    hv.cut_with_plane([0, 0, 50], [0, 0, 1], invert=False)
    hv.color("grey5", alpha=0.99)
    hvc = hv.clone()
    hvc.cut_with_plane(plane_og.point, plane_og.normal, invert=True)

    ost.offset_retroversion(10)
    plane_p = ost.plane
    print(ost.neckshaft_rel)
    hvp1 = hv.clone()
    hvp2 = hv.clone()
    hvp1.cut_with_plane(plane_p.point, plane_p.normal, invert=False)
    hvp1.cut_with_plane(plane_og.point, plane_og.normal, invert=True)
    hvp2.cut_with_plane(plane_p.point, plane_p.normal, invert=True)
    hvp2.cut_with_plane(plane_og.point, plane_og.normal, invert=False)
    hvp1.color("green7", alpha=0.999)
    hvp2.color("green6", alpha=0.999)
    hvp1 = hvp1.wireframe()
    hvcp = hv.clone()
    hvcp.cut_with_plane(plane_p.point, plane_p.normal, invert=True)
    hvcpc = hvcp.cap(return_cap=True)
    hvcp.cut_with_plane(plane_og.point, plane_og.normal, invert=True)
    hvcpc.color("black", alpha=0.55)

    ost.offset_retroversion(-20)
    plane_n = ost.plane
    print(ost.neckshaft_rel)
    hvn1 = hv.clone()
    hvn2 = hv.clone()
    hvn1.cut_with_plane(plane_n.point, plane_n.normal, invert=False)
    hvn1.cut_with_plane(plane_og.point, plane_og.normal, invert=True)
    hvn2.cut_with_plane(plane_n.point, plane_n.normal, invert=True)
    hvn2.cut_with_plane(plane_og.point, plane_og.normal, invert=False)
    hvn1.color("red7", alpha=0.999)
    hvn2.color("red6", alpha=0.999)
    hvn1 = hvn1.wireframe()
    hvcn = hv.clone()
    hvcn.cut_with_plane(plane_n.point, plane_n.normal, invert=True)
    hvcnc = hvcn.cap(return_cap=True)
    hvcn.cut_with_plane(plane_og.point, plane_og.normal, invert=True)
    hvcnc.color("black", alpha=0.45)

    hvs = [hvn1, hvn2, hvcn, hvcnc]
    plt = vedo.Plotter(interactive=False)
    plt.azimuth(-40)
    plt.elevation(-55)
    plt.roll(45)
    radius = hvc.diagonal_size() / 3
    plt.add_ambient_occlusion(radius)
    plt.show(*hvs, size=(1200, 1800), zoom=1.8)
    plt.screenshot("img/height-_ns+_rv-.png").close()

    hvs = [hvp1, hvp2, hvcp, hvcpc]
    plt = vedo.Plotter(interactive=False)
    plt.azimuth(-40)
    plt.elevation(-55)
    plt.roll(45)
    radius = hvc.diagonal_size() / 3
    plt.add_ambient_occlusion(radius)
    plt.show(*hvs, size=(1200, 1800), zoom=1.8)
    plt.screenshot("img/height-_ns+_rv+.png")
    plt.close()
    break
