"""
Layanan Pengecekan Poligon Zona Kamera (Tahap 6).
Posisi seseorang diuji terhadap poligon zona berdasarkan titik kaki / pusat bawah kotak orang:
(foot_x = (x1 + x2) / 2, foot_y = y2).
Mendukung poligon berformat koordinat ternormalisasi [0.0 .. 1.0].
"""

from typing import List, Tuple, Union


def point_in_polygon(x: float, y: float, polygon: List[Union[List[float], Tuple[float, float]]]) -> bool:
    """
    Algoritma Ray-Casting untuk menentukan apakah titik (x, y) berada di dalam poligon.
    Polygon adalah list titik [[x0, y0], [x1, y1], ...].
    """
    n = len(polygon)
    if n < 3:
        return False

    inside = False
    p1x, p1y = polygon[0][0], polygon[0][1]

    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n][0], polygon[i % n][1]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        x_inters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= x_inters:
                            inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def get_person_foot_point(bbox: Tuple[float, float, float, float]) -> Tuple[float, float]:
    """
    Mengambil titik kaki / pusat bawah dari bounding box orang (x1, y1, x2, y2).
    Mengembalikan (foot_x, foot_y) = ((x1 + x2) / 2, y2).
    """
    x1, y1, x2, y2 = bbox
    foot_x = (x1 + x2) / 2.0
    foot_y = y2
    return foot_x, foot_y


def is_person_in_zone(
    bbox: Tuple[float, float, float, float],
    polygon: List[Union[List[float], Tuple[float, float]]],
    frame_width: float = 1.0,
    frame_height: float = 1.0,
) -> bool:
    """
    Mengecek apakah titik kaki orang berada di dalam poligon zona.
    Jika frame_width > 1.0 atau frame_height > 1.0, maka bbox dinormalisasi terhadap dimensi frame
    atau poligon dinormalisasi sesuai skala.
    """
    foot_x, foot_y = get_person_foot_point(bbox)

    # Jika bbox dalam skala piksel, ubah ke skala normalisasi [0..1]
    if frame_width > 1.0 and frame_height > 1.0:
        norm_x = foot_x / frame_width
        norm_y = foot_y / frame_height
    else:
        norm_x = foot_x
        norm_y = foot_y

    return point_in_polygon(norm_x, norm_y, polygon)
