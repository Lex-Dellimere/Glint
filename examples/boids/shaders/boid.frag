#version 430 core
in vec3 vWorld;
in vec3 vColor;
in float vSide;
uniform vec3 uEye;
out vec4 FragColor;
void main() {
  vec3 n = normalize(cross(dFdx(vWorld), dFdy(vWorld)));
  vec3 toEye = normalize(uEye - vWorld);
  if (dot(n, toEye) < 0.0) { n = -n; }
  vec3 l = normalize(vec3(0.4, 0.9, 0.3));
  float dif = 0.35 + 0.65 * max(dot(n, l), 0.0);
  float rim = pow(1.0 - max(dot(n, toEye), 0.0), 3.0);
  vec3 col = vColor * dif + vec3(0.6, 0.8, 1.0) * rim * 0.5;
  float d = length(uEye - vWorld);
  col = mix(col, vec3(0.015, 0.02, 0.045), clamp((d - 60.0) / 260.0, 0.0, 0.85));   // fog
  FragColor = vec4(col, 1.0);
}
