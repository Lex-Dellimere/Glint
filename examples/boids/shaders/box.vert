#version 430 core
// The 12 edges of the box, made from gl_VertexID.
uniform mat4 uView;
uniform mat4 uProj;
uniform float uBox;
void main() {
  int e = gl_VertexID / 2;
  int end = gl_VertexID % 2;
  vec3 a;
  int axis = e / 4;
  int k = e % 4;
  float s1 = (k & 1) == 0 ? -1.0 : 1.0;
  float s2 = (k & 2) == 0 ? -1.0 : 1.0;
  float t = end == 0 ? -1.0 : 1.0;
  if (axis == 0) { a = vec3(t, s1, s2); }
  else if (axis == 1) { a = vec3(s1, t, s2); }
  else { a = vec3(s1, s2, t); }
  gl_Position = uProj * uView * vec4(a * uBox * 0.8, 1.0);
}
