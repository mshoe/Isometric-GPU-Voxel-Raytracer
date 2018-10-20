# Isometric-GPU-Voxel-Raytracer
(cool_parking_lot.png)
A parking lot rendered from my engine.

Using:
- ModernGL for the OpenGL interface
- PyGame for window and context creation

Design decisions:
Q: Why Python?
A: It is a simple high-level language. My output is much faster when I code in Python, which is important for keeping me motivated on larger projects. If this graphics engine starts developing into an actual game, I'll start porting it over to C++.
Also, the big meat of the code is in GLSL, so the slowness of Python is not really a bottleneck.

Q: Why Isometric?
A: It looks better for the type of game I'm trying to make.