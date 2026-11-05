#version 430 core
// The predator: a glowing point sprite.
uniform mat4 uView;
uniform mat4 uProj;
uniform vec3 uPredator;
void main() {
  gl_Position = uProj * uView * vec4(uPredator, 1.0);
  gl_PointSize = 900.0 / gl_Position.w;
}
