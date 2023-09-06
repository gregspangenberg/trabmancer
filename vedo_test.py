"""Compute the (signed) distance of one mesh to another"""
import vedo

# Create a sphere object and position it at (10,20,30)
s1 = vedo.Sphere().pos(0, 0, 0)

# Create a cube object with color grey and scaled
# along the x-axis by 2, and positioned at (14,20,30)
s2 = vedo.Sphere(c="grey4", alpha=0.2).scale([0.5, 1, 1]).pos(-0.5, 0, 0)

# Compute the Euclidean distance between the 2 surfaces
# and set the color of the sphere based on the distance
s1.cut_with_plane()
print(s1.distance_to(s2, signed=True))
s1.cmap("hot").add_scalarbar("Signed\nDistance")
print(s1)
# Show the sphere, the cube, the script docstring, axes,
# then close the window
vedo.show(s1, s2, __doc__, axes=1, size=(1000, 500), zoom=1.5).close()
