#version 430 core
out vec4 FragColor;
void main() {
  vec2 q = gl_PointCoord * 2.0 - 1.0;
  float r = dot(q, q);
  if (r > 1.0) { discard; }
  FragColor = vec4(vec3(1.0, 0.2, 0.35) * (1.4 - r), 1.0);
}
