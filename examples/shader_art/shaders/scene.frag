#version 330 core
// A raymarched scene: liquid chrome blobs over a mirror floor, a glowing ring,
// soft shadows, ambient occlusion, reflections and fog. Edit and save while it
// runs: the preview rebuilds it (an error shows at the top, the old one keeps going).
#include "sdf.glsl"
in vec2 uv;
out vec4 FragColor;
uniform float uTime;
uniform vec2 uRes;
uniform vec3 uEye;
uniform vec3 uTarget;

const int STEPS = 160;
const float FAR = 60.0;

// The scene: x = distance, y = material (1 floor, 2 chrome, 3 ring)
vec2 map(vec3 p) {
  float t = uTime;
  vec3 a = vec3(sin(t * 0.9) * 1.1, 1.15 + sin(t * 1.3) * 0.35, cos(t * 0.7) * 0.9);
  vec3 b = vec3(cos(t * 0.6) * 1.2, 1.0 + cos(t * 1.1) * 0.4, sin(t * 0.8) * 1.1);
  vec3 c = vec3(sin(t * 0.5 + 2.0) * 0.8, 1.6 + sin(t * 0.9) * 0.3, cos(t * 1.2 + 1.0) * 0.7);
  float blob = smin(smin(sdSphere(p - a, 0.62), sdSphere(p - b, 0.55), 0.55), sdSphere(p - c, 0.45), 0.5);
  blob += 0.025 * sin(p.x * 9.0 + t * 2.0) * sin(p.y * 7.0 - t) * sin(p.z * 8.0);   // rippling skin
  vec2 res = vec2(blob, 2.0);
  vec3 q = p - vec3(0.0, 1.25, 0.0);
  q.xy = rot(t * 0.35) * q.xy;
  q.yz = rot(0.9 + sin(t * 0.4) * 0.3) * q.yz;
  float ring = sdTorus(q, vec2(2.15, 0.06));
  if (ring < res.x) { res = vec2(ring, 3.0); }
  float floor_ = p.y;
  if (floor_ < res.x) { res = vec2(floor_, 1.0); }
  return res;
}

vec3 normalAt(vec3 p) {
  vec2 e = vec2(0.0008, 0.0);
  return normalize(vec3(map(p + e.xyy).x - map(p - e.xyy).x,
                        map(p + e.yxy).x - map(p - e.yxy).x,
                        map(p + e.yyx).x - map(p - e.yyx).x));
}

vec2 march(vec3 ro, vec3 rd) {
  float t = 0.0;
  for (int i = 0; i < STEPS; i++) {
    vec2 h = map(ro + rd * t);
    if (h.x < 0.0004 * t) { return vec2(t, h.y); }
    t += h.x * 0.9;
    if (t > FAR) { break; }
  }
  return vec2(FAR, 0.0);
}

float softShadow(vec3 ro, vec3 rd) {
  float res = 1.0;
  float t = 0.02;
  for (int i = 0; i < 64; i++) {
    float h = map(ro + rd * t).x;
    res = min(res, 10.0 * h / t);
    t += clamp(h, 0.02, 0.3);
    if (res < 0.002 || t > 12.0) { break; }
  }
  return clamp(res, 0.0, 1.0);
}

float ambientOcclusion(vec3 p, vec3 n) {
  float occ = 0.0;
  float w = 1.0;
  for (int i = 1; i <= 5; i++) {
    float d = 0.06 * float(i);
    occ += w * (d - map(p + n * d).x);
    w *= 0.6;
  }
  return clamp(1.0 - 2.5 * occ, 0.0, 1.0);
}

vec3 sky(vec3 rd) {
  float h = clamp(rd.y * 0.5 + 0.5, 0.0, 1.0);
  vec3 col = mix(vec3(0.004, 0.004, 0.01), vec3(0.035, 0.02, 0.08), h);
  col += vec3(1.0, 0.35, 0.8) * pow(max(dot(rd, normalize(vec3(-0.5, 0.25, -1.0))), 0.0), 24.0) * 0.45;
  col += vec3(0.2, 0.7, 1.0) * pow(max(dot(rd, normalize(vec3(0.8, 0.15, 0.6))), 0.0), 18.0) * 0.4;
  return col;
}

vec3 ringGlow(vec3 ro, vec3 rd, float maxT) {
  // cheap volumetric glow: sample distance to the ring along the ray
  vec3 g = vec3(0.0);
  float t = 0.0;
  for (int i = 0; i < 40; i++) {
    vec3 p = ro + rd * t;
    vec3 q = p - vec3(0.0, 1.25, 0.0);
    q.xy = rot(uTime * 0.35) * q.xy;
    q.yz = rot(0.9 + sin(uTime * 0.4) * 0.3) * q.yz;
    float d = sdTorus(q, vec2(2.15, 0.06));
    g += vec3(1.0, 0.25, 0.7) * 0.004 / (0.01 + d * d * 160.0);
    t += max(d * 0.5, 0.08);
    if (t > maxT) { break; }
  }
  return g;
}

vec3 shade(vec3 ro, vec3 rd, vec2 hit, out vec3 nextRo, out vec3 nextRd, out float refl) {
  vec3 p = ro + rd * hit.x;
  vec3 n = normalAt(p);
  vec3 lightDir = normalize(vec3(0.6, 0.9, 0.4));
  float sh = softShadow(p + n * 0.01, lightDir);
  float ao = ambientOcclusion(p, n);
  float dif = max(dot(n, lightDir), 0.0) * sh;
  float spe = pow(max(dot(reflect(-lightDir, n), -rd), 0.0), 64.0) * sh;
  float fre = pow(1.0 - max(dot(n, -rd), 0.0), 5.0);
  vec3 col;
  nextRo = p + n * 0.01;
  nextRd = reflect(rd, n);
  if (hit.y < 1.5) {                                  // mirror-ish checker floor
    vec2 c = floor(p.xz * 1.0);
    float check = mod(c.x + c.y, 2.0);
    vec3 base = mix(vec3(0.03), vec3(0.09, 0.08, 0.12), check);
    col = base * (0.25 + dif) * ao;
    refl = 0.25 + 0.5 * fre;
  } else if (hit.y < 2.5) {                           // chrome
    col = vec3(0.04) * ao + vec3(1.0) * spe * 1.5;
    refl = 0.85;
  } else {                                            // glowing ring
    col = vec3(3.0, 0.8, 2.2);
    refl = 0.0;
  }
  return col;
}

void main() {
  vec2 p = (uv * uRes - 0.5 * uRes) / uRes.y;
  vec3 fw = normalize(uTarget - uEye);
  vec3 rt = normalize(cross(fw, vec3(0.0, 1.0, 0.0)));
  vec3 up = cross(rt, fw);
  vec3 ro = uEye;
  vec3 rd = normalize(p.x * rt + p.y * up + 1.6 * fw);

  vec3 col = vec3(0.0);
  vec3 weight = vec3(1.0);
  float firstT = FAR;
  for (int bounce = 0; bounce < 3; bounce++) {
    vec2 hit = march(ro, rd);
    if (bounce == 0) { firstT = hit.x; col += ringGlow(ro, rd, hit.x); }
    if (hit.y == 0.0) { col += weight * sky(rd); break; }
    vec3 nro;
    vec3 nrd;
    float refl;
    vec3 c = shade(ro, rd, hit, nro, nrd, refl);
    float fog = exp(-0.03 * hit.x * hit.x * 0.05);
    col += weight * (1.0 - refl) * mix(sky(rd), c, fog);
    weight *= refl * mix(vec3(1.0), vec3(0.9, 0.85, 1.0), float(bounce));
    if (refl < 0.01) { break; }
    ro = nro;
    rd = nrd;
  }
  // tone map (ACES fit), vignette, gamma
  col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);
  col *= 1.0 - 0.35 * dot(p, p);
  FragColor = vec4(pow(clamp(col, 0.0, 1.0), vec3(1.0 / 2.2)), 1.0);
}
