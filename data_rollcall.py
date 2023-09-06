import shoulder
import pathlib
import numpy
from itertools import groupby


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


# Group the files by the matching part of their name
files = pathlib.Path("../shoulder_data/bones/non_arthritic").glob("*")
grouped_files = []
for key, group in groupby(sorted(files, key=key_func), key=key_func):
    # Convert the group iterator to a list and append it to the result
    grouped_files.append(list(group))

# grouped_files = [group for group in grouped_files if len(group) > 4]

# for i, bone_files in enumerate(grouped_files):
#     # grab out the individual files
#     stl = [f for f in bone_files if ".stl" in f.name]
#     print(i)
#     print(stl)
#     try:
#         anp = [f for f in bone_files if "anp" in f.name][0]
#         print(anp.name)
#     except:
#         print("no anp!")
#     print()

good_i = 0
for i, bone_files in enumerate(grouped_files):
    # grab out the individual files
    stl = [f for f in bone_files if ".stl" in f.name]
    # print(stl)
    try:
        anp = [f for f in bone_files if "anp" in f.name][0]
        # print(anp.name)
        if len(stl) == 2:
            good_i += 1
            print(good_i)
            print(stl)
            print(anp.name)
    except:
        print("no anp!")
