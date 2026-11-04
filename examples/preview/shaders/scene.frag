#version 330 core
#include "light.glsl"
in vec3 Normal;
in vec3 FragPos;
out vec4 FragColor;
uniform vec3 lightPos;
uniform vec3 viewPos;
uniform vec3 objectColor;
void main() {
  FragColor = vec4(shade(Normal, FragPos, lightPos, viewPos) * objectColor, 1.0);
}
