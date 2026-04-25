import math
import bisect
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
from hpgl_preview.hpgl_parser.parse import parse_hpgl


def show_timeline(draw_speed, travel_speed, art,
                     plotter_unit_mm=0.02488, playback_speed=60):
    hpgl_lines, max_x, max_y = parse_hpgl(f"art/{art}/renders/{art}.hpgl")

    paths = [lines for (_pen, _width, lines) in hpgl_lines if len(lines) > 1]

    fig, ax = plt.subplots()
    fig.canvas.manager.set_window_title(f'Plotting {art}')
    fig.subplots_adjust(bottom=0.18)

    ax.set_xlim(0, max_x)
    ax.set_ylim(max_y, 0)  # inverted y to match plotter coordinates
    ax.set_aspect('equal')

    # Recompute axis limits from actual drawn content to exclude park/travel positions
    if paths:
        all_pts = [pt for path in paths for pt in path]
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        span = max(max(xs) - min(xs), max(ys) - min(ys))
        pad = span * 0.05 + 20
        ax.set_xlim(min(xs) - pad, max(xs) + pad)
        ax.set_ylim(max(ys) + pad, min(ys) - pad)

    draw_line, = ax.plot([], [], lw=1, color='black')
    time_text = ax.text(
        0.02, 0.02, 'Real time: 0.00s', transform=ax.transAxes,
        fontsize=10, verticalalignment='bottom',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7),
    )

    all_moves = []
    for path in paths:
        if not path:
            continue
        # travel (pen up) to start of this stroke
        all_moves.append((path[0][0], path[0][1], False))
        # draw each point in the stroke (pen down)
        for pt in path:
            all_moves.append((pt[0], pt[1], True))

    # build cumulative time array
    times = [0.0]
    for i in range(1, len(all_moves)):
        x1, y1, _ = all_moves[i - 1]
        x2, y2, pen_down = all_moves[i]
        dist_mm = math.hypot(x2 - x1, y2 - y1) * plotter_unit_mm
        speed = draw_speed if pen_down else travel_speed
        times.append(times[-1] + dist_mm / speed)

    total_time = times[-1]

    def render(t):
        frame = bisect.bisect_right(times, t) - 1
        frame = max(0, min(frame, len(all_moves) - 1))

        draw_xs, draw_ys = [], []
        seg_xs, seg_ys = [], []
        in_draw = False

        for j in range(frame + 1):
            x, y, pen_down = all_moves[j]
            if pen_down:
                if not in_draw:
                    seg_xs, seg_ys = [x], [y]
                    in_draw = True
                else:
                    seg_xs.append(x)
                    seg_ys.append(y)
            else:
                if in_draw and seg_xs:
                    draw_xs.extend(seg_xs + [None])
                    draw_ys.extend(seg_ys + [None])
                    seg_xs, seg_ys = [], []
                    in_draw = False

        # interpolate partial progress toward the next move so the pen
        # appears to physically drag along each segment rather than
        # snapping it into existence.
        next_frame = frame + 1
        if next_frame < len(all_moves) and times[next_frame] > times[frame]:
            alpha = (t - times[frame]) / (times[next_frame] - times[frame])
            nx, ny, n_pen_down = all_moves[next_frame]
            cx, cy, _ = all_moves[frame]
            if n_pen_down:
                ix = cx + alpha * (nx - cx)
                iy = cy + alpha * (ny - cy)
                if in_draw:
                    seg_xs.append(ix)
                    seg_ys.append(iy)
                else:
                    # pen just came down — show partial stroke from this point
                    seg_xs, seg_ys = [cx, ix], [cy, iy]
                    in_draw = True

        if in_draw and seg_xs:
            draw_xs.extend(seg_xs + [None])
            draw_ys.extend(seg_ys + [None])

        draw_line.set_data(draw_xs, draw_ys)
        time_text.set_text(
            f'Real time: {t:.1f}s  ({t/60:.1f}min)  /  total: {total_time:.1f}s ({total_time/60:.1f}min)')
        fig.canvas.draw_idle()

    # slider
    ax_slider = fig.add_axes([0.1, 0.06, 0.8, 0.04])
    slider = widgets.Slider(ax_slider, 'Time', 0.0, total_time, valinit=0.0,
                            valstep=total_time / 1000)

    # play/pause button
    ax_btn = fig.add_axes([0.45, 0.01, 0.1, 0.04])
    btn = widgets.Button(ax_btn, 'Play')

    playing = [False]
    last_wall = [None]
    playback_t = [0.0]

    def on_slider(val):
        playback_t[0] = val
        render(val)

    slider.on_changed(on_slider)

    def on_timer(_):
        if not playing[0]:
            return
        import time
        now = time.perf_counter()
        if last_wall[0] is not None:
            elapsed = (now - last_wall[0]) * playback_speed
            playback_t[0] = min(playback_t[0] + elapsed, total_time)
            slider.set_val(playback_t[0])
            if playback_t[0] >= total_time:
                playing[0] = False
                btn.label.set_text('Play')
        last_wall[0] = now

    timer = fig.canvas.new_timer(interval=33)  # ~30 fps
    timer.add_callback(on_timer, None)
    timer.start()

    def on_btn(event):
        import time
        if playing[0]:
            playing[0] = False
            btn.label.set_text('Play')
        else:
            if playback_t[0] >= total_time:
                playback_t[0] = 0.0
            playing[0] = True
            last_wall[0] = time.perf_counter()
            btn.label.set_text('Pause')

    btn.on_clicked(on_btn)

    render(0.0)
    on_btn(None)  # autoplay
    plt.show()
