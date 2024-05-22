from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec, gp_Ax2, gp_Trsf, gp_Ax1
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.GC import GC_MakeArcOfCircle
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.Interface import Interface_Static
import numpy as np

# Define the original ranges for parameters
X_MIN, X_MAX = -1, 1  # x
Y_MIN, Y_MAX = -1, 1  # y
RADIUS_MIN, RADIUS_MAX = 0, 1  # radius
ANGLE_MIN, ANGLE_MAX = 0, 2 * np.pi  # alpha
E_MIN, E_MAX = -1, 1  # e1, e2
S_MIN, S_MAX = 0, 2  # s
THETA_MIN, THETA_MAX = -np.pi, np.pi  # theta
PHI_MIN, PHI_MAX = -np.pi, np.pi  # phi
GAMMA_MIN, GAMMA_MAX = -np.pi, np.pi  # gamma
PX_MIN, PX_MAX = -1, 1  # px
PY_MIN, PY_MAX = -1, 1  # py
PZ_MIN, PZ_MAX = -1, 1  # pz

def reverse_normalize(value, min_val, max_val):
    return min_val + (max_val - min_val) * (value / 255.0)  # Changed to 255.0 to correctly map from [0, 255]

def process_commands(commands):
    shapes = []
    current_wires = []  # List to hold all wires created for the current profile
    wire_builder = BRepBuilderAPI_MakeWire()
    last_end_point = gp_Pnt(0, 0, 0)  # Initial starting point
    print("Initial last_end_point:", last_end_point.X(), last_end_point.Y(), last_end_point.Z())

    for idx, command in enumerate(commands):
        cmd_type = int(command[0])
        print(f"Processing command {idx}: {command}")

        try:
            if cmd_type == 4:  # <SOL> token starts a new wire
                if wire_builder.IsDone():
                    current_wires.append(wire_builder.Wire())
                wire_builder = BRepBuilderAPI_MakeWire()

            elif cmd_type == 0:  # Line
                if command[1] != -1 and command[2] != -1:
                    start = last_end_point
                    end_x = reverse_normalize(float(command[1]), X_MIN, X_MAX)
                    end_y = reverse_normalize(float(command[2]), Y_MIN, Y_MAX)
                    end = gp_Pnt(end_x, end_y, 0.0)
                    print(f"Creating Line from ({start.X()}, {start.Y()}, {start.Z()}) to ({end.X()}, {end.Y()}, {end.Z()})")
                    edge = BRepBuilderAPI_MakeEdge(start, end).Shape()
                    wire_builder.Add(edge)
                    last_end_point = end

            elif cmd_type == 1:  # Arc
                if command[1] != -1 and command[2] != -1 and command[3] != -1 and command[4] != -1:
                    start = last_end_point
                    end_x = reverse_normalize(float(command[1]), X_MIN, X_MAX)
                    end_y = reverse_normalize(float(command[2]), Y_MIN, Y_MAX)
                    center_x = reverse_normalize(float(command[3]), X_MIN, X_MAX)
                    center_y = reverse_normalize(float(command[4]), Y_MIN, Y_MAX)
                    end = gp_Pnt(end_x, end_y, 0.0)
                    center = gp_Pnt(center_x, center_y, 0.0)
                    print(f"Creating Arc from ({start.X()}, {start.Y()}, {start.Z()}) to ({end.X()}, {end.Y()}, {end.Z()}) with center ({center.X()}, {center.Y()}, {center.Z()})")
                    arc = GC_MakeArcOfCircle(start, center, end).Value()
                    edge = BRepBuilderAPI_MakeEdge(arc).Shape()
                    wire_builder.Add(edge)
                    last_end_point = end

            elif cmd_type == 2:  # Circle
                if command[1] != -1 and command[2] != -1 and command[5] != -1:
                    center_x = reverse_normalize(float(command[1]), X_MIN, X_MAX)
                    center_y = reverse_normalize(float(command[2]), Y_MIN, Y_MAX)
                    radius = reverse_normalize(float(command[5]), RADIUS_MIN, RADIUS_MAX)
                    center = gp_Pnt(center_x, center_y, 0.0)
                    print(f"Creating Circle with center ({center.X()}, {center.Y()}, {center.Z()}) and radius {radius}")
                    circle = BRepBuilderAPI_MakeEdge(gp_Pnt(center.X() + radius, center.Y(), 0), center).Shape()
                    wire_builder.Add(circle)

            elif cmd_type == 5:  # Extrude
                if wire_builder.IsDone():
                    current_wires.append(wire_builder.Wire())
                wire_builder = BRepBuilderAPI_MakeWire()  # Reset for the next profile

                # Create faces for all wires in the current profile
                faces = []
                for wire in current_wires:
                    if wire.IsNull():
                        print("Error: Wire creation failed.")
                        continue
                    face = BRepBuilderAPI_MakeFace(wire)
                    if face.IsDone():
                        shapes.append(face.Shape())
                    else:
                        print("Error: Face creation failed.")
                        continue

                # Clear the current wires list for the next profile
                current_wires = []

                # Apply extrusion to the faces
                theta = reverse_normalize(float(command[6]), THETA_MIN, THETA_MAX)
                phi = reverse_normalize(float(command[7]), PHI_MIN, PHI_MAX)
                gamma = reverse_normalize(float(command[8]), GAMMA_MIN, GAMMA_MAX)
                px = reverse_normalize(float(command[9]), PX_MIN, PX_MAX)
                py = reverse_normalize(float(command[10]), PY_MIN, PY_MAX)
                pz = reverse_normalize(float(command[11]), PZ_MIN, PZ_MAX)
                s = reverse_normalize(float(command[12]), S_MIN, S_MAX)
                e1 = reverse_normalize(float(command[13]), E_MIN, E_MAX)
                e2 = reverse_normalize(float(command[14]), E_MIN, E_MAX)

                b = int(command[15])
                u = int(command[16])

                print(f"Creating Extrude with theta={theta}, phi={phi}, gamma={gamma}, px={px}, py={py}, pz={pz}, s={s}, e1={e1}, e2={e2}, b={b}, u={u}")

                # Create transformation matrix for orientation
                trsf = gp_Trsf()
                trsf.SetTranslationPart(gp_Vec(px, py, pz))

                # Apply rotations around X, Y, and Z axes
                trsf.SetRotation(gp_Ax1(last_end_point, gp_Dir(1, 0, 0)), theta)
                trsf.SetRotation(gp_Ax1(last_end_point, gp_Dir(0, 1, 0)), phi)
                trsf.SetRotation(gp_Ax1(last_end_point, gp_Dir(0, 0, 1)), gamma)

                axis = gp_Ax2(last_end_point, gp_Dir(0, 0, 1))
                for face in faces:
                    prism = BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, e1 + e2))
                    if prism.IsDone():
                        shapes.append(prism.Shape())
                    else:
                        print("Error: Prism creation failed.")
                        continue

            elif cmd_type == 3:  # EOS
                print("End of Sequence encountered.")
                break
        except Exception as e:
            print(f"Error processing command {idx} ({command}): {e}")

    # Check if there's a final closed wire that needs to be added as a face
    if wire_builder.IsDone():
        current_wires.append(wire_builder.Wire())
    wire_builder = BRepBuilderAPI_MakeWire()

    for wire in current_wires:
        if not wire.IsNull():
            face = BRepBuilderAPI_MakeFace(wire)
            if face.IsDone():
                shapes.append(face.Shape())
            else:
                print("Error: Final face creation failed.")
        else:
            print("Error: Final wire creation failed.")

    return shapes

def export_step_file(shapes, filename="output_model.step"):
    writer = STEPControl_Writer()
    Interface_Static.SetCVal("write.step.schema", "AP214")  # Set STEP schema, can be AP203 or AP214

    # Transfer shapes to the writer
    for shape in shapes:
        if shape.IsNull():
            print("Warning: Encountered a null shape, skipping.")
            continue

        shape_type = shape.ShapeType()
        print(f"Transferring shape of type {shape_type}")

        try:
            writer.Transfer(shape, STEPControl_AsIs)
        except Exception as e:
            print(f"Error transferring shape: {e}")
            continue

    # Writing the file
    status = writer.Write(filename)
    if status == 0:
        print(f"Failed to export STEP file to {filename}")
    else:
        print(f"STEP file has been exported successfully to {filename}")
        

commands = np.array([
    [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # <SOL>
    [2, 176, 128, -1, -1, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Circle
    [5, -1, -1, -1, -1, -1, 128, 128, 128, 119, 128, 128, 18, 220, 128, 0, 0],  # Extrude
    [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # <SOL>
    [2, 176, 128, -1, -1, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Circle
    [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # <SOL>
    [2, 176, 128, -1, -1, 35, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Circle
    [5, -1, -1, -1, -1, -1, 128, 128, 255, 140, 128, 220, 24, 132, 128, 1, 0],  # Extrude
    [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # <SOL>
    [2, 176, 128, -1, -1, 48, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Circle
    [5, -1, -1, -1, -1, -1, 128, 128, 255, 137, 128, 220, 18, 132, 128, 1, 0],  # Extrude
    [3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]   # <EOS>
])

commands2 = np.array([
    [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # <SOL>
    [0, 214, 128, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Line
    [0, 214, 223, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Line
    [0, 128, 223, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Line
    [0, 128, 128, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Line
    [5, -1, -1, -1, -1, -1, 192, 192, 64, 41, 128, 224, 192, 163, 128, 0, 0],  # Extrude
    [4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # <SOL>
    [1, 140, 116, 64, 1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Arc
    [0, 211, 116, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Line
    [1, 223, 128, 64, 1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Arc
    [0, 223, 211, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Line
    [1, 211, 223, 64, 1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Arc
    [0, 140, 223, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Line
    [1, 128, 211, 64, 1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Arc
    [0, 128, 128, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # Line
    [5, -1, -1, -1, -1, -1, 192, 192, 192, 198, 163, 67, 140, 121, 128, 2, 0],  # Extrude
    [3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]   # <EOS>
])


shapes = process_commands(commands)
export_step_file(shapes, filename="output_model.step")
