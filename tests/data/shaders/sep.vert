#version 410 core
layout (location = 0) in vec2 aPos;
out gl_PerVertex { vec4 gl_Position; };
void main() { gl_Position = vec4(aPos, 0.0, 1.0); }
