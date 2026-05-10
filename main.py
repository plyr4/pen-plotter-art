import importlib
import inspect
import json
import os
import subprocess
import sys
import click
import questionary
import vpype
import vsketch
from hpgl_preview.timeline import show_timeline
from rich.console import Console
from rich.rule import Rule
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

# vpype device name used when writing HPGL (sets correct plotter units / paper limits)
# hp7475a, designmate, hp7440a, artisan, dmp_161, hp7550, dxy, sketchmate
HPGL_DEVICE = "hp7475a"
HPGL_PAGE_SIZE = "a4"
HPGL_LANDSCAPE = True
HPGL_CENTER = True
HPGL_VELOCITY = None

# (used by the preview animation)
# plotter speeds in mm/s (used for animation timing)
DRAW_SPEED = 40.0   # mm/s, pen down
TRAVEL_SPEED = 200.0  # mm/s, pen up


# 1 vpype px = 1/96 inch = 25.4/96 mm
_PX_TO_MM = 25.4 / 96


def print_doc_info(doc, art):
    console = Console()
    table = Table(title=f"[bold]{art}.svg[/bold]", show_footer=True)
    table.add_column("Layer", style="cyan")
    table.add_column("Strokes", justify="right", footer_style="bold")
    table.add_column("Segments", justify="right", footer_style="bold")
    table.add_column("Points", justify="right", footer_style="bold")
    table.add_column("Pen-down", justify="right", footer_style="bold")

    total_strokes = total_segments = total_points = 0
    total_length_mm = 0.0

    for lid, layer in sorted(doc.layers.items()):
        strokes = len(layer)
        segments = layer.segment_count()
        points = sum(len(line) for line in layer.lines)
        length_mm = layer.length() * _PX_TO_MM
        total_strokes += strokes
        total_segments += segments
        total_points += points
        total_length_mm += length_mm
        table.add_row(
            str(lid),
            str(strokes),
            str(segments),
            str(points),
            f"{length_mm / 1000:.2f} m",
        )

    table.columns[1].footer = str(total_strokes)
    table.columns[2].footer = str(total_segments)
    table.columns[3].footer = str(total_points)
    table.columns[4].footer = f"{total_length_mm / 1000:.2f} m"

    pen_up_mm = doc.pen_up_length() * _PX_TO_MM
    console.print()
    console.print(table)
    console.print(
        f"  [dim]pen-up travel:[/dim] [yellow]{pen_up_mm / 1000:.2f} m[/yellow]"
    )
    console.print()


def _file_size_str(path):
    if not os.path.exists(path):
        return "[red]missing[/red]"
    size = os.path.getsize(path)
    if size >= 1_048_576:
        return f"{size / 1_048_576:.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size} B"


def print_file_info(svg_path, hpgl_path):
    console = Console()
    console.print(
        f"  [cyan]SVG [/cyan]  [dim]{svg_path}[/dim]  {_file_size_str(svg_path)}")
    console.print(
        f"  [cyan]HPGL[/cyan]  [dim]{hpgl_path}[/dim]  {_file_size_str(hpgl_path)}")
    console.print()


def apply_config(sketch_cls, config_path):
    with open(config_path) as f:
        config = json.load(f)
    for key, value in config.items():
        if key.startswith("__"):
            continue
        attr = getattr(sketch_cls, key, None)
        if isinstance(attr, vsketch.Param):
            attr.value = type(attr.value)(value)


def draw_svg(doc, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        vpype.write_svg(f, doc, center=True)


def plot_hpgl(doc, path, page_size, landscape, center, device, velocity):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        vpype.write_hpgl(
            f,
            doc,
            page_size,
            landscape,
            center,
            device,
            velocity,
            absolute=True,
        )


def generate_and_write(sketch_cls, svg_out, hpgl_out, art):
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), TimeElapsedColumn()) as progress:
        task = progress.add_task(f"Drawing {art}...", total=None)
        sketch = sketch_cls.execute(finalize=True)
        doc = sketch.vsk.document
        draw_svg(doc, svg_out)
        progress.update(
            task, description=f"Writing {os.path.basename(hpgl_out)}...")
        plot_hpgl(doc, hpgl_out, HPGL_PAGE_SIZE, HPGL_LANDSCAPE,
                  HPGL_CENTER, HPGL_DEVICE, HPGL_VELOCITY)
        progress.update(task, description=f"Done — {art}")
    return doc


@click.group()
def cli():
    pass


@cli.command()
@click.option("--art", default=None, help="Art piece folder name inside art/")
@click.option("--config", "config_name", default=None, help="Config file name inside art/<art>/config/")
def run(art, config_name):
    if art is None:
        available = sorted(
            d for d in os.listdir("art")
            if os.path.isdir(os.path.join("art", d)) and not d.startswith("_")
        )
        art = questionary.select(
            "Select an art piece:", choices=available).ask()
        if art is None:
            raise SystemExit(0)

    try:
        art_module = importlib.import_module(f"art.{art}.generate")
    except ModuleNotFoundError:
        available = sorted(
            d for d in os.listdir("art")
            if os.path.isdir(os.path.join("art", d)) and not d.startswith("_")
        )
        raise click.ClickException(
            f"art '{art}' not found. Available: {', '.join(available)}")

    sketch_cls = None
    for _name, obj in inspect.getmembers(art_module, inspect.isclass):
        if (issubclass(obj, vsketch.SketchClass)
                and obj is not vsketch.SketchClass
                and obj.__module__ == art_module.__name__):
            sketch_cls = obj
            break

    if sketch_cls is None:
        raise click.ClickException(
            f"no vsketch.SketchClass subclass found in art/{art}/generate.py")

    config_path = None
    if config_name is not None:
        fname = config_name if config_name.endswith(
            ".json") else config_name + ".json"
        config_path = os.path.join("art", art, "config", fname)
        if not os.path.exists(config_path):
            raise click.ClickException(
                f"config '{config_name}' not found at {config_path}")
    else:
        config_dir = os.path.join("art", art, "config")
        if os.path.isdir(config_dir):
            configs = sorted(f for f in os.listdir(
                config_dir) if f.endswith(".json"))
            if configs:
                choice = questionary.select(
                    "Select a config (or skip):",
                    choices=["(none)"] + configs,
                ).ask()
                if choice is None:
                    raise SystemExit(0)
                if choice != "(none)":
                    config_path = os.path.join(config_dir, choice)

    if config_path is not None:
        apply_config(sketch_cls, config_path)

    config_suffix = ""
    config_stem = None
    if config_path is not None:
        config_stem = os.path.splitext(os.path.basename(config_path))[0]
        config_suffix = f"_{config_stem}"

    svg_out = os.path.join("art", art, "renders", f"{art}{config_suffix}.svg")
    hpgl_out = os.path.join("art", art, "renders",
                            f"{art}{config_suffix}.hpgl")

    console = Console()
    title = f"[bold]{art}[/bold]"
    if config_stem:
        title += f"  [dim]config: {config_stem}[/dim]"
    console.print()
    console.print(Rule(title, style="cyan"))
    console.print(f"  [dim]{svg_out}[/dim]")
    console.print()

    skip_generation = False
    if os.path.exists(svg_out):
        regenerate = questionary.confirm(
            f"'{os.path.basename(svg_out)}' already exists — regenerate?",
            default=False,
        ).ask()
        if regenerate is None:
            raise SystemExit(0)
        skip_generation = not regenerate

    vpype_doc = None
    if not skip_generation:
        vpype_doc = generate_and_write(sketch_cls, svg_out, hpgl_out, art)
        print_doc_info(vpype_doc, art)

    print_file_info(svg_out, hpgl_out)

    def refresh():
        to_reload = [m for name, m in list(
            sys.modules.items()) if name.startswith("art.")]
        for mod in to_reload:
            importlib.reload(mod)
        reloaded = importlib.import_module(f"art.{art}.generate")
        importlib.reload(reloaded)
        cls = None
        for _name, obj in inspect.getmembers(reloaded, inspect.isclass):
            if (issubclass(obj, vsketch.SketchClass)
                    and obj is not vsketch.SketchClass
                    and obj.__module__ == reloaded.__name__):
                cls = obj
                break
        if cls is None:
            return
        if config_path is not None:
            apply_config(cls, config_path)
        generate_and_write(cls, svg_out, hpgl_out, art)

    if questionary.confirm(f"View timeline for {os.path.basename(hpgl_out)}?", default=False).ask():
        show_timeline(DRAW_SPEED, TRAVEL_SPEED, art, on_refresh=refresh)


@cli.command()
@click.argument("name", required=False, default=None)
def new(name):
    if name is None:
        name = questionary.text("Name your new art piece:").ask()
        if not name:
            raise SystemExit(0)
    if os.path.exists(os.path.join("art", name)):
        raise click.ClickException(
            f"art piece '{name}' already exists in art/")
    template_dir = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "sketch_template")
    vsk_bin = os.path.join(os.path.dirname(sys.executable), "vsk")
    env = {**os.environ, "VSK_TEMPLATE": template_dir}
    subprocess.run([vsk_bin, "init", f"art/{name}"], env=env, check=True)

    if questionary.confirm(f"Run '{name}' now?", default=True).ask():
        subprocess.run(
            [sys.executable, os.path.abspath(__file__), "run", "--art", name],
            check=True,
        )


if __name__ == "__main__":
    cli()
