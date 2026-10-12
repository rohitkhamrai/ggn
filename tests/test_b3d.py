import build123d as bd
part = bd.Solid.make_box(1, 1, 1)
v, f = part.tessellate(0.01)
print(len(v), len(f))
