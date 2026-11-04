#version 330 core
#include "inc/common.glsl"
out vec4 FragColor;
uniform vec4 col;
uniform float k;
void main() { FragColor = vec4(tint() * k, 1.0) * col; }
