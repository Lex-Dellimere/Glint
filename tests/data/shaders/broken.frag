#version 330 core
#include "inc/bad.glsl"
out vec4 FragColor;
void main() { FragColor = vec4(broken(), 1.0); }
