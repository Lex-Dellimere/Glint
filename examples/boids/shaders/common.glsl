// Shared by the boid shaders: buffers, the grid and the settings.
// Boids live in a box from -uBox to +uBox; the grid's cells are uRadius wide,
// so a boid's neighbours are all in its own cell or the 26 around it.
layout(std430, binding = 0) buffer PosA { vec4 posA[]; };
layout(std430, binding = 1) buffer VelA { vec4 velA[]; };
layout(std430, binding = 2) buffer PosB { vec4 posB[]; };
layout(std430, binding = 3) buffer VelB { vec4 velB[]; };
layout(std430, binding = 4) buffer CellCount { uint cellCount[]; };
layout(std430, binding = 5) buffer CellStart { uint cellStart[]; };
layout(std430, binding = 6) buffer BoidCell { uint boidCell[]; };
layout(std430, binding = 7) buffer BoidRank { uint boidRank[]; };

uniform uint uCount;      // number of boids
uniform float uBox;       // half size of the box
uniform float uRadius;    // how far a boid sees
uniform int uGrid;        // cells along one side

ivec3 cellOf(vec3 p) {
  return clamp(ivec3((p + uBox) / uRadius), ivec3(0), ivec3(uGrid - 1));
}

uint cellIndex(ivec3 c) { return uint((c.z * uGrid + c.y) * uGrid + c.x); }
