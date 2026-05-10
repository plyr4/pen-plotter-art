import os
import sys
import vsketch
from shapely.geometry import LineString

# cross-compatibility with "vsk run" 
# fmt: off
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.mesh import project_mesh
from models.models import MODELS_PATH
from utils.noise import load_noise, sample_noise
from utils.wiggle import wiggle_polyline
# fmt: on

MM_TO_PX = 96.0 / 25.4
STL_PATH = os.path.join(MODELS_PATH, "cube", "cube.stl")
NOISE_PATH = os.path.join(os.path.dirname(__file__), "noise2.png")

class CubeNoiseSketch(vsketch.SketchClass):
    page_size = vsketch.Param("a4")
    landscape = vsketch.Param(True)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size(self.page_size, landscape=self.landscape)
        vsk.scale("1mm")
        width = vsk.width / MM_TO_PX
        height = vsk.height / MM_TO_PX

        noise = load_noise(NOISE_PATH)
        amplitude = 2.5
        lines = project_mesh(STL_PATH, width, height)
        for line in lines:
            wiggled = wiggle_polyline(
                line,
                lambda mx, my: sample_noise(
                    noise, mx, my, width, height) * amplitude,
                segments=400,
            )
            vsk.geometry(LineString(wiggled))

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesort")


if __name__ == "__main__":
    CubeNoiseSketch.display()
