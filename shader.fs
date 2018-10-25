/*
 * Author: Mshoe
 */

#version 430

uniform vec2 iResolution; // viewport resolution (in pixels)
uniform vec4 iMouse; // Mouse pixel coords. xy: current, zw: click
uniform float iTime; // shader playback time (in seconds)

uniform mat4 iCamera;

const vec3 camera_from = iCamera[3].xyz;
const vec3 camera_dir = -iCamera[2].xyz;
const vec3 camera_right = iCamera[0].xyz;
const vec3 camera_up = iCamera[1].xyz;


#define DEBUG 0
//
//  DepthShader.fsh
//  created with Shaderific

const float VOX_W = 20.0;
const float VOX_H = 20.0;

const int CHUNK_W = 50;
const int CHUNK_H = 10;

//usamplerBuffer voxel_chunk;

const vec3 VEC_NULL = vec3(0.0, 0.0, 0.0);
const vec3 VEC_POS_X = vec3(1.0, 0.0, 0.0);
const vec3 VEC_NEG_X = vec3(-1.0, 0.0, 0.0);
const vec3 VEC_POS_Y = vec3(0.0, 1.0, 0.0);
const vec3 VEC_NEG_Y = vec3(0.0, -1.0, 0.0);
const vec3 VEC_POS_Z = vec3(0.0, 0.0, 1.0);
const vec3 VEC_NEG_Z = vec3(0.0, 0.0, -1.0);

int surface_of_cube(int i, int j, int k) {
	if (i == 0 || j == CHUNK_H -1 || j == 0 || k == CHUNK_W - 1) {
		return 1;
	}
	return 0;
}

int simple_world(int i, int j, int k) {
	if (0 <= i && i < CHUNK_W &&
		0 <= j && j < CHUNK_H &&
		0 <= k && k < CHUNK_W) {

		if (i % 4 == 0 || (j % 3 == 0 && !(k % 4 == 0))) {
			return 1;
		}
	}
   	return 0;
}

float map(vec3 p) {
	return float(simple_world(int(floor(p.x + 0.5)), int(floor(p.y + 0.5)), int(floor(p.z + 0.5))));
}

vec3 simple_map(int blockID) {
   if (blockID != 0) {
      return vec3(1.0, 0.0, 0.0);
   }
   return vec3(0.0, 0.0, 0.0);
}

float plane_intersect(float s, float v, float r) {
   // intersection between line and a plane
   return (r - s) / v;
}

/*
mat4 lookat(vec3 from, vec3 to, vec3 tmp_up) {
	// move this to the cpu later and pass it as a uniform
	mat4 res;
	vec3 forward = normalize(from - to);
	vec3 right = cross(tmp_up, forward);
	vec3 up = cross(forward, right);

	res[0] = vec4(right, 0.0);
	res[1] = vec4(up, 0.0);
	res[2] = vec4(forward, 0.0);
	res[3] = vec4(from, 1.0);

	return res;
}
*/

void voxel_plane_intersect(float s, float v, float r0, float r1,
                           out float t) {
   // This function returns whether the ray hits plane r0, r1, or neither
   // r0 < r1
   // If the ray described by P(t) = S + tV hits r0 or r1, 
   // return the parametric value in t

	if (v == 0.0) {
		t = -1.0;
		return;
	}
	else if (v > 0.0) {
		if (s < r0)
			t = plane_intersect(s, v, r0);
		else if (s < r1) // in between the two faces
			t = plane_intersect(s, v, r1);
		else
			t = -1.0;
		return;
	}
	else if (v < 0.0) {
		if (s > r1)
			t = plane_intersect(s, v, r1);
		else if (s > r0) // in between the two faces
			t = plane_intersect(s, v, r1);
		else
			t = -1.0;
		return;
	}
}

void voxel_intersect(vec3 rs, vec3 rv, 
			float i, float j, float k, 
			float width, float height,
          	out float t, out vec3 n_dir, out vec2 uv, out vec3 u_dir, out vec3 v_dir) {
   // rs is ray starting point
   // rv is ray direction
   // This function computes the intersection between a ray and a box

	float rx0 = i*width + 0.0;
	float ry0 = j*height + 0.0;
	float rz0 = k*width + 0.0;

	float rx1 = (i + 1)*width;
	float ry1 = (j + 1)*height;
	float rz1 = (k + 1)*width;

	bool pos_neg_face;

	voxel_plane_intersect(rs.x, rv.x, rx0, rx1, t);
	if (t > 0.0) {
		vec3 p = rs + t * rv;
		if ( ry0 <= p.y && p.y <= ry1 && rz0 <= p.z && p.z <= rz1 ) {
			n_dir = (rv.x > 0) ? VEC_NEG_X : VEC_POS_X;
			u_dir = VEC_POS_Z;
			v_dir = VEC_POS_Y;

			uv.x = (p.z - rz0) / (rz1 - rz0);
			uv.y = (p.y - ry0) / (ry1 - ry0);
			return;
		}
	}

	voxel_plane_intersect(rs.y, rv.y, ry0, ry1, t);
	if (t > 0.0) {
		vec3 p = rs + t * rv;
		if ( rx0 <= p.x && p.x <= rx1 && rz0 <= p.z && p.z <= rz1 ) {
			n_dir = (rv.y > 0) ? VEC_NEG_Y : VEC_POS_Y;

			u_dir = VEC_POS_X;
			v_dir = VEC_POS_Z;

			uv.x = (p.x - rx0) / (rx1 - rx0);
			uv.y = (p.z - rz0) / (rz1 - rz0);
			return;
		}
	}

	voxel_plane_intersect(rs.z, rv.z, rz0, rz1, t);
	if (t > 0.0) {
		vec3 p = rs + t * rv;
		if ( rx0 <= p.x && p.x <= rx1 && ry0 <= p.y && p.y <= ry1 ) {
			n_dir = (rv.z > 0) ? VEC_NEG_Z : VEC_POS_Z;

			u_dir = VEC_POS_X;
			v_dir = VEC_POS_Y;

			uv.x = (p.x - rx0) / (rx1 - rx0);
			uv.y = (p.y - ry0) / (ry1 - ry0);
			return;
		}
	}

	t = -1.0;
	n_dir = VEC_NULL;
	uv.xy = vec2(-1.0, -1.0);
	u_dir = VEC_NULL;
	v_dir = VEC_NULL;
	return;
}

void construct_ray(vec2 frag_coord, vec3 iso_dir,
                   out vec3 rs, out vec3 rv) {
   // constructs a ray described by the equation P(t) = S + tV
   vec2 st = frag_coord;// / iResolution * 100.0;

   //mat4 camera = lookat(camera_from, camera_to, vec3(0.0, 1.0, 0.0));
   
   //rs = rotation * vec3( st.x + offset.x, st.y + offset.y, -1000.0);
   //rv = rotation * iso_dir;

   rs = camera_from;
   rs += (-iResolution.x / 2.0 + st.x) * camera_right;
   rs += (-iResolution.y / 2.0 + st.y) * camera_up;
   rv = camera_dir;
}

int get_in_bounds(int x, int low, int high) {
	if (x < low)
		return low;
	else if (x > high)
		return high;
	else
		return x;
}

void find_starting_voxel(vec3 rs, vec3 rv, out vec3 rs_onvoxel, 
                         out int i, out int j, out int k,
                         out float t) {
	// finds the voxel that the ray hits first
	vec3 u_dir, v_dir, n_dir;
	vec2 uv;
	voxel_intersect(rs, rv, 
					0.0, 0.0, 0.0, 
					VOX_W * float(CHUNK_W), VOX_H * float(CHUNK_H), 
					t, n_dir, uv, u_dir, v_dir);

	if (t > 0.0) {
		rs_onvoxel = rs + t * rv;
		// for numerical robustness
		i = get_in_bounds(int(floor(rs_onvoxel.x / VOX_W)), 0, CHUNK_W - 1);
		j = get_in_bounds(int(floor(rs_onvoxel.y / VOX_H)), 0, CHUNK_H - 1);
		k = get_in_bounds(int(floor(rs_onvoxel.z / VOX_W)), 0, CHUNK_W - 1);
	}
}

void ray_trace(vec3 rs, vec3 rv, 
               inout int i, inout int j, inout int k, 
               out float t, out vec3 n_dir, out int blockID) {

	// THE RAY TRACING ALGORITHM!!!

	// find whether to increment or decrement the voxel index as we travel along the ray
	
	int di = (rv.x > 0.0) ? 1 : -1;
	int dj = (rv.y > 0.0) ? 1 : -1;
	int dk = (rv.z > 0.0) ? 1 : -1;

	// find the deltas (distance along ray to get to next voxel per dimension)
	float dx = (rv.x != 0.0) ? VOX_W / abs(rv.x) : VOX_W * CHUNK_W;
	float dy = (rv.y != 0.0) ? VOX_H / abs(rv.y) : VOX_H * CHUNK_H;
	float dz = (rv.z != 0.0) ? VOX_W / abs(rv.z) : VOX_W * CHUNK_W;

	dx = VOX_W / abs(rv.x);
	dy = VOX_H / abs(rv.y);
	dz = VOX_W / abs(rv.z);
	
	float tx, ty, tz;

	float sCellx = (di == 1) ? VOX_W * float(i+1) - rs.x : rs.x - VOX_W * float(i);
	float sCelly = (dj == 1) ? VOX_H * float(j+1) - rs.y : rs.y - VOX_H * float(j);
	float sCellz = (dk == 1) ? VOX_W * float(k+1) - rs.z : rs.z - VOX_W * float(k);

	tx = sCellx / abs(rv.x);
	ty = sCelly / abs(rv.y);
	tz = sCellz / abs(rv.z);


	while (	0 <= i && i < CHUNK_W &&
	      	0 <= j && j < CHUNK_H &&
	      	0 <= k && k < CHUNK_W) {
	  
		// terminating condition
		blockID = simple_world(i, j, k);

		if (blockID != 0) {
			t = min(tx, min(ty, tz));
			n_dir = VEC_NULL;
			return;
		}
		
		if (tx < ty) {
			if (tx < tz) {
				tx += dx;
				i += di;
			} else {
				tz += dz;
				k += dk;
			}
		}
		else {
			if (ty < tz) {
				ty += dy;
				j += dj;
			} else {
				tz += dz;
				k += dk;
			}
		}
	}

	t = min(tx, min(ty, tz));
	blockID = 0;
	n_dir = VEC_NULL;
	return;
}

void get_edge_vectors( 	vec3 n_dir, vec3 u_dir, vec3 v_dir, vec3 pos, 
						out vec4 va, out vec4 vc) {

	vec3 vax = pos - v_dir;
	vec3 vay = pos + v_dir;
	vec3 vaz = pos - u_dir;
	vec3 vaw = pos + u_dir;

	va = vec4(map(vax), map(vay), map(vaz), map(vaw));

	vec3 vcx = pos + n_dir - v_dir;
	vec3 vcy = pos + n_dir + v_dir;
	vec3 vcz = pos + n_dir - u_dir;
	vec3 vcw = pos + n_dir + u_dir;

	vc = vec4(map(vcx), map(vcy), map(vcz), map(vcw));
}

void get_corner_vectors( 	vec3 n_dir, vec3 u_dir, vec3 v_dir, vec3 pos, 
							out vec4 vb, out vec4 vd) {
	vec3 vbx = pos - v_dir - u_dir;
	vec3 vby = pos + v_dir - u_dir;
	vec3 vbz = pos + v_dir + u_dir;
	vec3 vbw = pos - v_dir + u_dir;

	vb = vec4(map(vbx), map(vby), map(vbz), map(vbw));

	vec3 vdx = pos + n_dir - v_dir - u_dir;
	vec3 vdy = pos + n_dir + v_dir - u_dir;
	vec3 vdz = pos + n_dir + v_dir + u_dir;
	vec3 vdw = pos + n_dir - v_dir + u_dir;

	vd = vec4(map(vdx), map(vdy), map(vdz), map(vdw));
}

void find_surrounding_voxels(	vec3 n_dir, vec3 u_dir, vec3 v_dir, int i, int j, int k,
								out vec4 va, out vec4 vb, out vec4 vc, out vec4 vd) {
	// first find every voxel surrounding the i,j,k voxel
	
	vec3 pos = vec3(float(i), float(j), float(k));

	get_edge_vectors(n_dir, u_dir, v_dir, pos, va, vc);
	get_corner_vectors(n_dir, u_dir, v_dir, pos, vb, vd);
}

float maxcomp( in vec4 v ) {
	return max( max(v.x, v.y), max(v.z, v.w) );
}

float isEdge( in vec2 uv, vec4 va, vec4 vb, vec4 vc, vec4 vd)
{
	vec2 st = 1.0 - uv;

	// sides
	vec4 wb = smoothstep( 0.85, 0.95, vec4(	st.y,
											uv.y,
											st.x,
											uv.x) ) * (1.0 - va + va * vc);

	
	// corners
	vec4 wc = smoothstep( 0.85, 0.95, vec4( st.x * st.y,
											st.x * uv.y,
											uv.x * uv.y,
											uv.x * st.y) ) * (1.0 - vb + vd * vb);
	
	return maxcomp( max(wb, wc) );
}

float sky_light(float y_pos) {
	return y_pos / (float(CHUNK_H) * VOX_H);
}

float calcOcc(	vec2 uv,
				vec4 va, vec4 vb, vec4 vc, vec4 vd) {
	vec2 st = 1.0 - uv;

	// edges
	vec4 wa = vec4( st.y, uv.y, st.x, uv.x) * vc;

	// corners
	vec4 wb = vec4( st.x * st.y,
					st.x * uv.y,
					uv.x * uv.y,
					uv.x * st.y) * vd * (1.0 - vc.xzyw) * (1.0 - vc.zywx);

	//wb = vec4(0.0);
	return 	wa.x + wa.y + wa.z + wa.w + 
			wb.x + wb.y + wb.z + wb.w;
}

bool hover_voxel(	vec2 mouse, vec2 fc, vec3 iso_dir,
					int st_i, int st_j, int st_k) {
	// create a glow around the mouse cursor

	float x = mouse.x;
	float y = mouse.y;

	// check if the mouse is near the frag coordinate
	if ((step(x - VOX_W * 2.0, fc.x) -
		step(x + VOX_W * 2.0, fc.x)) *
		(step(y - VOX_H * 2.0, fc.y) -
		step(y + VOX_H * 2.0, fc.y)) < 0.99) {
		return false;
	}

	vec3 rs, rv, rs_onvoxel;
	construct_ray(mouse.xy, iso_dir, rs, rv);

	float t;
	int i, j, k;
	vec3 n_dir;
	
	find_starting_voxel(rs, rv, rs_onvoxel, i, j, k, t);
	if (t > 0.0) {
		int blockID;
		ray_trace(rs_onvoxel, rv, i, j, k, t, n_dir, blockID);

		if (st_i == i && st_j == j && st_k == k && blockID != 0) {
			
			return true;
		}
	}

	return false;
}

void main()
{

	vec3 debugColor = vec3(0.0, 0.0, 0.0);
	vec3 color = vec3(0.0, 0.0, 0.0);
	vec3 hover_color = vec3(0.0);

	vec2 st = gl_FragCoord.xy / iResolution;
	float time = iTime;
	//float mouse = mousePos(iMouse.xy / iResolution, st);


	vec3 rs, rv; // the vectors describing the ray P(t) = S + tV
	vec3 iso_dir = normalize(vec3(0.0, -0.5, 1.0));

	//rotation = mat3(1.0);
	// first construct the ray (rs, rv)
	construct_ray(gl_FragCoord.xy, iso_dir, rs, rv);

	// then find the voxel in the voxel grid the ray starts at
	float t;
	int i, j, k;
	vec3 n_dir;
	
	vec3 rs_onvoxel;
	find_starting_voxel(rs, rv, rs_onvoxel, i, j, k, t);
	
#if DEBUG
	if (t > 0.0) {
		if (k == 0)
			debugColor.x = 1.0;
		if (k == 1)
			debugColor.y = 1.0;

	}
#endif

	if (t > 0.0) {
		int blockID;
		ray_trace(rs_onvoxel, rv, i, j, k, t, n_dir, blockID);


		if (blockID != 0) {
			t = 0.0;
			vec3 u_dir, v_dir;
			vec2 uv;
			voxel_intersect(rs, rv, i, j, k, VOX_W, VOX_H, t, n_dir, uv, u_dir, v_dir);
			vec4 va, vb, vc, vd;
			find_surrounding_voxels(n_dir, u_dir, v_dir, i, j, k, va, vb, vc, vd);

			color.x = 1.0;
			vec4 v0 = vec4(0.0);
			//color.y = isEdge(uv, v0, v0, v0, v0);
			float edge = isEdge(uv, va, vb, vc, vd);

			color.y = edge;
			
			
			float light = sky_light((rs + t*rv).y);
			light *= 1.0 - 0.5 * calcOcc(uv, va, vb, vc, vd);
			color *= light;

			// for getting the voxel the mouse is hovering over
			if (hover_voxel(iMouse.xy, gl_FragCoord.xy,
					iso_dir, i, j, k)) {
				hover_color.y = 1.0;
			}
		}
	}


	
	
	gl_FragColor = vec4(color + hover_color, 1.0);
#if DEBUG
	gl_FragColor = vec4(debugColor, 1.0);
#endif

}