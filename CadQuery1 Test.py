import cadquery as cq

# Create a cube: length, width, height in millimeters
cube = cq.Workplane("XY").box(100, 100, 100)

# Display the model in the CadQuery editor
show_object(cube)
