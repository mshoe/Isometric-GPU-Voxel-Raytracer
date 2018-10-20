#version 430



uniform vec2 iResolution; // viewport resolution (in pixels)
uniform vec4 iMouse; // Mouse pixel coords. xy: current, zw: click
uniform float iTime; // shader playback time (in seconds)


out vec4 f_color;

const float VOX_W = 1.0;
const float VOX_H = 0.5;

const int MAX_X = 10;
const int MAX_Y = 10;
const int MAX_Z = 10;

const int FACE_NONE = -1;
const int FACE_FRONT_Z = 0;
const int FACE_BACK_Z = 1;
const int FACE_FRONT_X = 2;
const int FACE_BACK_X = 3;
const int FACE_UP_Y = 4;
const int FACE_DOWN_Y = 5;

bool map(int i, int j, int k) {
	if (i >= 0 && i <= 3 && j >= 0 && j <= 1) {
		return true;
	}
	return false;
}

float plane_intersect(float s, float v, float r) {
	// intersection between line and a plane
	return (r - s) / v;
}

void box_plane_intersect(	float s, float v, float r0, float r1, 
							out float t, out bool front_back) {
	// check if ray is intersecting the plane r0 first or r1 first
	// if return value is < 0, then the ray is starting from inside the box
	// face = true => r1 intersected first
	// face = false => r0 intersected first

	if (v == 0.0) {
		// ray is parallel with this dimensional plane
		t = -1.0;
		face = false;
	}
	else if (v > 0.0) {
		// ray is intersecting r0 first, because r0 < r1
		t = plane_intersect(s, v, r0);
		face = false;
	}
	else if (v < 0.0) {
		// ray is intersecting r1 first, because r0 < r1
		t = (plane_intersect(s, v, r1));
		face = true;
	}
}

bool ray_in_bounds(float s, float v, float t, float r0, float r1) {
	float p = s + t * v;
	if (p >= r0 && p <= r1) {
		return true;
	}
	return false;
}

void box_intersect(vec3 rs, vec3 rv, int i, int j, int k, float width, float height,
					out float t, out int face) {
	// rs is the ray starting point
	// rv is the ray direction
	// this function computes the intersection between a ray and a box
	// returns: vec3 showing which face it intersects

	// planes representing faces of the voxel
	// r*0 < r*1
	float rx0 = i + 0.0;
	float ry0 = j + 0.0;
	float rz0 = k + 0.0;
	float rx1 = i + width;
	float ry1 = j + height;
	float rz1 = k + width;
	
	float t;
	int face;
	bool front_back;

	box_plane_intersect(rs.x, rv.x, rx0, rx1, t, front_back);
	if (t > 0.0 && 
		ray_in_bounds(rs.y, rv.y, t, ry0, ry1) &&
		ray_in_bounds(rs.z, rv.z, t, rz0, rz1)) {
		if (front_back)
			face = FACE_FRONT_X;
		else
			face = FACE_BACK_X;
		return;
	}
		

	t = box_plane_intersect(rs.y, rv.y, ry0, ry1);
	if (t > 0.0 &&
		ray_in_bounds(rs.x, rv.x, t, rx0, rx1) &&
		ray_in_bounds(rs.z, rv.z, t, rz0, rz1)) {
		if (front_back)
			face = FACE_UP_Y;
		else
			face = FACE_DOWN_Y;
		return;
	}
		

	t = box_plane_intersect(rs.z, rv.z, rz0, rz1);
	if (t > 0.0 &&
		ray_in_bounds(rs.x, rv.x, t, rx0, rx1) &&
		ray_in_bounds(rs.y, rv.y, t, ry0, ry1)) {
		if (front_back)
			face = FACE_FRONT_Z;
		else
			face = FACE_BACK_Z;
	}

	face = FACE_NONE;
	return;
}

float mousePos(in vec2 mouse, in vec2 st) {
	// create a glow around the mouse cursor

	float x = mouse.x;
	float y = mouse.y;
	float radius = 0.2;
	return 
		(smoothstep(x - radius, x, st.x) -
		smoothstep(x, x + radius, st.x)) *
		(smoothstep(y - radius, y, st.y) -
		smoothstep(y, y + radius, st.y));
}

void construct_ray(	in vec2 st, in vec3 dir, in float unzoom, in float z_start, in mat3 rotation,
					out vec3 rs, out vec3 rv) 
{
	// given st: the screen coordinates, and dir: the direction,
	// return a ray defined by P(t) = S + tV

	rs = rotation * vec3(st.x * unzoom, st.y * unzoom, z_start);
	rv = rotation * dir; // (0.0, -0.5, 1.0) for standard isometric view
}

ivec3 find_starting_voxel(	vec3 rs, vec3 rv, vec3 origin) {
	// given rs: the starting point of the ray and,
	// rv: the direction of the ray,
	// return the i, j, k indices of the starting voxel
	// this is done by doing a ray box intersection with the entire chunk

	float t;
	int face;
	box_intersect(rs, rv, 0, 0, 0, VOX_W * MAX_X, VOX_H * MAX_Y, t, face);
	if (t > 0) {
		vec3 point = rs + t * rv;
		int i = floor(point.x / VOX_W);
		int j = floor(point.y / VOX_H);
		int k = floor(point.z / VOX_W);
		return ivec3(i, j, k);
	}
	else {
		
	}

	
}

void main() {
	vec2 st = gl_FragCoord.xy / iResolution * 20.0;
	float time = iTime;
	float mouse = mousePos(iMouse.xy / iResolution, st);

	mat3 rotation;
	rotation[0] = vec3(cos(radians(-45.0)), 0.0, -sin(radians(-45.0)));
	rotation[1] = vec3 (0.0, 1.0, 0.0);
	rotation[2] = vec3(sin(radians(-45.0)), 0.0, cos(radians(-45.0)));

	vec3 rs = rotation * vec3(st.x, st.y, -5.0);
	vec3 rv = rotation * vec3(0.0, -0.5, 1.0);

	/*vec3 box = box_intersect(rs, rv, 0, 0, 0);
	vec3 box2 = box_intersect(rs, rv, 1, 0, 0);
	vec3 box3 = box_intersect(rs, rv, 0, 0, 1);
	*/
	f_color = vec4(vec3(0.0), 1.0);


	//f_color = vec4(mouse, mouse, sin(iTime) / 2.0 + 0.5,1.0);

}