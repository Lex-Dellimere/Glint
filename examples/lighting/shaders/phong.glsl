// Phong lighting: ambient + diffuse + specular. Edit this while the example
// runs: Glint rebuilds the program when you save.
vec3 phong(vec3 normal, vec3 fragPos, vec3 lightPos, vec3 viewPos, vec3 lightColor) {
  vec3 ambient = 0.1 * lightColor;
  vec3 norm = normalize(normal);
  vec3 lightDir = normalize(lightPos - fragPos);
  vec3 diffuse = max(dot(norm, lightDir), 0.0) * lightColor;
  vec3 viewDir = normalize(viewPos - fragPos);
  vec3 reflectDir = reflect(-lightDir, norm);
  vec3 specular = 0.5 * pow(max(dot(viewDir, reflectDir), 0.0), 32.0) * lightColor;
  return ambient + diffuse + specular;
}
