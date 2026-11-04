#version 330 core
#include "phong.glsl"
out vec4 FragColor;
in vec3 Normal;
in vec3 FragPos;
uniform vec3 lightPos;
uniform vec3 viewPos;
uniform vec3 lightColor;
uniform vec3 objectColor;
void main() {
  FragColor = vec4(phong(Normal, FragPos, lightPos, viewPos, lightColor) * objectColor, 1.0);
}
