#version 430 core
// One boid = a small arrowhead (two triangles), placed and turned by its velocity.
#include "common.glsl"
uniform mat4 uView;
uniform mat4 uProj;
uniform float uSize;
out vec3 vWorld;
out vec3 vColor;
out float vSide;

vec3 hue(float h) {
  return clamp(abs(fract(h + vec3(0.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0, 0.0, 1.0);
}

void main() {
  uint id = uint(gl_InstanceID);
  vec3 p = posA[id].xyz;
  vec3 v = velA[id].xyz;
  float crowd = velA[id].w;
  vec3 f = normalize(v);
  vec3 side = normalize(cross(f, abs(f.y) > 0.95 ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 1.0, 0.0)));
  vec3 up = cross(side, f);
  // corners: nose, left wing, top of the back, nose, top of the back, right wing
  vec3 nose = f * 1.6;
  vec3 back = -f * 0.8 + up * 0.35;
  vec3 left = -f * 0.6 - side * 0.7;
  vec3 right = -f * 0.6 + side * 0.7;
  vec3 corner;
  int k = gl_VertexID;
  if (k == 0 || k == 3) { corner = nose; }
  else if (k == 1) { corner = left; }
  else if (k == 5) { corner = right; }
  else { corner = back; }
  vWorld = p + corner * uSize;
  vSide = (k < 3) ? -1.0 : 1.0;
  // colour by heading, warmer where the flock is dense
  float h = atan(f.z, f.x) / 6.2831853 + 0.5;
  vColor = mix(hue(h) * 0.75 + 0.25, vec3(1.0, 0.55, 0.25), clamp(crowd / 40.0, 0.0, 0.6));
  gl_Position = uProj * uView * vec4(vWorld, 1.0);
}
