import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from io import BytesIO
import base64
import os
import tempfile

# Палитра RAVI (полная)
def build_ravi_palette():
    stops = [
        (0.00, "#1a006e"), (0.10, "#0000ff"), (0.25, "#00cfff"),
        (0.40, "#00ff80"), (0.50, "#80ff00"), (0.62, "#ffff00"),
        (0.72, "#ffaa00"), (0.82, "#ff3300"), (0.90, "#ff0000"),
        (1.00, "#ffcccc"),
    ]
    return mcolors.LinearSegmentedColormap.from_list(
        "ravi_thermal",
        [(s[0], mcolors.to_rgb(s[1])) for s in stops],
        N=2048
    )

FULL_PALETTE_CMAP = build_ravi_palette()
FULL_PALETTE = [FULL_PALETTE_CMAP(i / 2047) for i in range(2048)]

def process_video(file_bytes: bytes, t_min: float, t_max: float, threshold: float):
    """Возвращает (image_base64, max_map_base64)"""
    # Сохраняем байты во временный файл
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ravi') as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    cap = cv2.VideoCapture(tmp_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        frames.append(gray)
    cap.release()
    os.unlink(tmp_path)

    if not frames:
        raise ValueError("Не удалось прочитать ни одного кадра из файла.")

    frames = np.stack(frames, axis=0)
    max_map = frames.max(axis=0)

    # Перевод в температуру
    temp_map = (max_map / 255.0) * (t_max - t_min) + t_min

    # Генерируем изображение с текущим порогом
    image_base64 = render_heatmap(temp_map, t_min, t_max, threshold)

    # Сохраняем max_map для пересчёта порога (сжимаем)
    max_map_flat = max_map.astype(np.float32).flatten().tobytes()
    max_map_base64 = base64.b64encode(max_map_flat).decode('utf-8')

    return image_base64, max_map_base64, max_map.shape

def render_heatmap(temp_map: np.ndarray, t_min: float, t_max: float, threshold: float) -> str:
    """Строит тепловую карту с заданным порогом и возвращает base64 PNG"""
    # Обрезанная палитра
    cmap = build_clipped_palette(t_min, t_max, threshold)

    fig, ax = plt.subplots(figsize=(12, 9), dpi=150)
    im = ax.imshow(temp_map, cmap=cmap, vmin=threshold, vmax=t_max, interpolation="nearest")
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, extend="min")
    cbar.set_label("Температура (°C)", fontsize=12)
    cbar.set_ticks([threshold, (threshold + t_max)/2, t_max])
    cbar.set_ticklabels([f"{threshold:.0f}°", f"{(threshold+t_max)/2:.0f}°", f"{t_max:.0f}°"])
    ax.set_title(f"Карта максимальных температур (порог > {threshold:.0f}°C)", fontsize=13, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode('utf-8')

def build_clipped_palette(t_min, t_max, threshold):
    """Палитра с обрезкой ниже порога (чёрный цвет)"""
    thresh_norm = (threshold - t_min) / (t_max - t_min)
    n = 2048
    indices = np.linspace(thresh_norm, 1.0, n)
    clipped_colors = FULL_PALETTE_CMAP(indices)
    cmap = mcolors.ListedColormap(clipped_colors, name="ravi_clipped")
    cmap.set_under("black")
    return cmap

def recolor_image(max_map_base64: str, shape: tuple, t_min: float, t_max: float, threshold: float) -> str:
    """Пересчитывает карту из сохранённой max_map с новым порогом"""
    max_map_flat = base64.b64decode(max_map_base64)
    max_map = np.frombuffer(max_map_flat, dtype=np.float32).reshape(shape)
    temp_map = (max_map / 255.0) * (t_max - t_min) + t_min
    return render_heatmap(temp_map, t_min, t_max, threshold)