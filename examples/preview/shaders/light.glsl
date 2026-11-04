// Try editing this while the preview runs, for example make the specular 2.0,
// or break it on purpose to see the error at the top of the window.
vec3 shade(vec3 normal, vec3 fragPos, vec3 lightPos, vec3 viewPos) {
  vec3 n = normalize(normal);
  vec3 l = normalize(lightPos - fragPos);
  vec3 v = normalize(viewPos - fragPos);
  float diffuse = max(dot(n, l), 0.0);
  float specular = 0.5 * pow(max(dot(v, reflect(-l, n)), 0.0), 32.0);
  return vec3(0.12 + diffuse + specular);
}
