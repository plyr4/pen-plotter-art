import os
import sys
import vsketch

# cross-compatibility with "vsk run" 
# fmt: off
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.models import MODELS_PATH 
# fmt: on


class {{cookiecutter.class_name}}(vsketch.SketchClass):
    # Sketch parameters:
    radius = vsketch.Param(2.0)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("{{cookiecutter.page_size}}",
                 landscape={{cookiecutter.landscape}})
        vsk.scale("{{cookiecutter.preferred_unit}}")

        # implement your sketch here
        vsk.circle(0, 0, self.radius, mode="radius")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype(
            "linemerge --tolerance 0.5mm linesimplify --tolerance 0.1mm linesort reloop --tolerance 0.05mm")


if __name__ == "__main__":
    {{cookiecutter.class_name}}.display()
