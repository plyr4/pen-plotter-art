import os
import sys
import vsketch
from shapely.geometry import LineString
import math
import random

# cross-compatibility with "vsk run" 
# fmt: off
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.mesh import project_mesh_occluded
from models.models import MODELS_PATH
# fmt: on


MM_TO_PX = 96.0 / 25.4


class CubeSpiralSketch(vsketch.SketchClass):
    page_size = vsketch.Param("a4")
    landscape = vsketch.Param(True)

    # --- Spiral layout ---
    # density only — doesn't affect spiral size
    num_skulls = vsketch.Param(48)
    # how many full revolutions the spiral covers
    turns = vsketch.Param(3.0)
    inner_radius = vsketch.Param(3.0)       # mm, radius at the very center
    outer_radius = vsketch.Param(120.0)     # mm, radius at the outermost skull

    # --- Mesh scale ---
    scale_inner = vsketch.Param(0.05)       # scale of the innermost skull
    scale_outer = vsketch.Param(2.5)        # scale of the outermost skull

    # --- Rotation ---
    rot_x = vsketch.Param(25.0)
    rot_z_base = vsketch.Param(45.0)
    spin_with_angle = vsketch.Param(True)

    # --- Noise ---
    position_noise = vsketch.Param(2.0)
    noise_seed = vsketch.Param(42)

    # --- Black hole at center ---
    # mm, radius of the noisy center circle
    blackhole_radius = vsketch.Param(8.0)
    # points in the perimeter (more = smoother base)
    blackhole_points = vsketch.Param(120)
    # mm of radial noise on the perimeter
    blackhole_noise = vsketch.Param(2.5)

    # --- STL frames cycled across skulls ---
    skull_1_stl = vsketch.Param("laughing_skull/skull_1.stl")
    skull_2_stl = vsketch.Param("laughing_skull/skull_2.stl")
    skull_3_stl = vsketch.Param("laughing_skull/skull_3.stl")

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size(self.page_size, landscape=self.landscape)
        vsk.scale("1mm")
        width = vsk.width / MM_TO_PX
        height = vsk.height / MM_TO_PX
        cx = width / 2
        cy = height / 2

        stl_filenames = [self.skull_1_stl, self.skull_2_stl, self.skull_3_stl]
        models_dir = MODELS_PATH

        n = max(self.num_skulls - 1, 1)
        theta_max = 2 * math.pi * self.turns

        r_growth = math.log(self.outer_radius / self.inner_radius) / theta_max
        s_growth = math.log(self.scale_outer / self.scale_inner) / theta_max

        # pre-compute positions for centering
        raw_positions = []
        for i in range(self.num_skulls):
            theta = theta_max * i / n
            r = self.inner_radius * math.exp(r_growth * theta)
            rng_jitter = random.Random(self.noise_seed + i)
            raw_positions.append((
                r *
                math.cos(theta) + rng_jitter.uniform(-self.position_noise,
                                                     self.position_noise),
                r *
                math.sin(theta) + rng_jitter.uniform(-self.position_noise,
                                                     self.position_noise),
            ))

        xs = [p[0] for p in raw_positions]
        ys = [p[1] for p in raw_positions]
        spiral_cx = (min(xs) + max(xs)) / 2
        spiral_cy = (min(ys) + max(ys)) / 2

        # black hole: noisy filled circle drawn first (behind everything)
        bh_rng = random.Random(self.noise_seed)
        bh_pts = self.blackhole_points
        bh_cx = cx + (-spiral_cx)  # same offset as spiral
        bh_cy = cy + (-spiral_cy)

        # draw as a filled disc using concentric noisy rings
        num_rings = max(int(self.blackhole_radius / 1.2), 3)
        for ring in range(num_rings, -1, -1):
            ring_r = self.blackhole_radius * ring / num_rings
            pts = []
            for j in range(bh_pts + 1):
                a = 2 * math.pi * j / bh_pts
                noise = bh_rng.uniform(-self.blackhole_noise,
                                       self.blackhole_noise) * (ring / num_rings)
                rr = max(0.0, ring_r + noise)
                pts.append((bh_cx + rr * math.cos(a),
                           bh_cy + rr * math.sin(a)))
            vsk.geometry(LineString(pts))

        for i in range(self.num_skulls):
            theta = theta_max * i / n

            pos_x = cx + raw_positions[i][0] - spiral_cx
            pos_y = cy + raw_positions[i][1] - spiral_cy

            scale = self.scale_inner * math.exp(s_growth * theta)

            rot_z = math.radians(self.rot_z_base)
            if self.spin_with_angle:
                rot_z += theta

            stl_path = os.path.join(
                models_dir, stl_filenames[i % len(stl_filenames)])

            for polyline in project_mesh_occluded(
                stl_path, width, height,
                rot_x=math.radians(self.rot_x),
                rot_z=rot_z,
                scale=scale,
                center_x=pos_x,
                center_y=pos_y,
            ):
                vsk.geometry(LineString(polyline))

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype(
            "squiggles linemerge --tolerance 0.5mm linesimplify --tolerance 0.1mm linesort reloop --tolerance 0.05mm")


if __name__ == "__main__":
    CubeSpiralSketch.display()
