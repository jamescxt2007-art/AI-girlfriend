r"""Deterministic extraction from the original sheet; never overwrites the source.

Run: .\.venv\Scripts\python.exe extract_portraits.py
The traced outer contours remove panel lines, labels, and decorative marks.
All source pixels retain their original colors; only outside alpha is removed.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent / "assets" / "character"
SIZE = (420, 420)
# Source-space silhouettes, cut above the expression labels at y=464.
PORTRAITS = {
    "happy": (556, [
        (388, 464), (388, 393), (398, 367), (410, 341), (415, 310),
        (417, 275), (426, 229), (439, 188), (459, 153), (479, 131),
        (504, 118), (530, 111), (558, 110), (588, 120), (613, 136),
        (634, 159), (650, 190), (662, 223), (674, 265), (682, 302),
        (690, 336), (703, 368), (714, 393), (722, 419), (722, 452),
        (709, 464),
    ]),
    "thoughtful": (916, [
        (739, 464), (739, 415), (748, 389), (759, 364), (766, 332),
        (770, 292), (779, 249), (789, 207), (801, 173), (816, 148),
        (837, 128), (861, 117), (889, 111), (917, 113), (943, 120),
        (969, 135), (990, 157), (1007, 185), (1019, 217), (1027, 249),
        (1035, 284), (1040, 319), (1045, 350), (1053, 377),
        (1067, 393), (1083, 407), (1083, 464),
    ]),
    "playful": (1298, [
        (1100, 464), (1100, 414), (1110, 385), (1121, 355),
        (1136, 339), (1155, 333), (1160, 302), (1151, 279),
        (1151, 246), (1158, 209), (1173, 174), (1194, 144),
        (1220, 126), (1249, 116), (1277, 115), (1304, 119),
        (1330, 130), (1354, 148), (1375, 174), (1388, 207),
        (1396, 242), (1407, 278), (1422, 311), (1443, 338),
        (1458, 357), (1469, 376), (1481, 385), (1493, 406),
        (1493, 464),
    ]),
}

FULL_BODY_OUTLINE = [
    (197, 20), (220, 13), (245, 16), (266, 27), (284, 49),
    (297, 80), (308, 111), (325, 145), (341, 178), (357, 214),
    (374, 253), (385, 289), (382, 325), (369, 350), (360, 378),
    (351, 404), (344, 433), (342, 462), (331, 481), (333, 509),
    (317, 530), (300, 538), (293, 550), (282, 575), (274, 600),
    (267, 625), (259, 650), (258, 675), (249, 700), (251, 725),
    (249, 750), (247, 775), (243, 800), (238, 825), (232, 850),
    (227, 875), (232, 900), (232, 925), (232, 942), (231, 953),
    (245, 970), (260, 983), (262, 1003), (242, 1010), (203, 1005),
    (170, 991), (148, 974), (127, 949), (111, 929), (98, 910),
    (94, 889), (97, 872), (105, 851), (114, 827), (116, 800),
    (127, 775), (136, 750), (141, 725), (150, 700), (164, 675),
    (177, 650), (173, 625), (164, 600), (152, 575), (141, 550),
    (128, 539), (101, 530), (90, 510), (79, 496),
    (68, 483), (66, 454), (66, 426), (61, 401), (49, 379),
    (36, 356), (37, 329), (45, 302), (54, 277), (67, 253),
    (56, 227), (53, 204), (57, 178), (70, 156), (91, 140),
    (112, 131), (133, 132), (146, 137), (152, 112), (157, 83),
    (166, 52), (179, 31),
]


def extract_full_body(source):
    box = (20, 0, 395, 1024)
    body = source.crop(box).convert("RGBA")
    mask = Image.new("L", (375 * 4, 1024 * 4))
    ImageDraw.Draw(mask).polygon([((x - 20) * 4, y * 4) for x, y in FULL_BODY_OUTLINE], fill=255)
    body.putalpha(mask.resize(body.size, Image.Resampling.LANCZOS))
    canvas = Image.new("RGBA", (400, 1040))
    canvas.alpha_composite(body, (12, 8))
    canvas.save(ROOT / "mika-full-body.png")
    print("mika-full-body.png", canvas.size)


def extract():
    with Image.open(ROOT / "mika-reference.png") as source:
        if source.size != (1536, 1024):
            raise ValueError("The traced coordinates expect the original 1536 × 1024 reference sheet.")
        extract_full_body(source)
        for expression, (center, points) in PORTRAITS.items():
            # Crop all portraits to the same source scale and y origin.
            box = (center - 210, 90, center + 210, 510)
            portrait = source.crop(box).convert("RGBA")
            # Supersampling smooths the transparent contour, without repainting.
            mask = Image.new("L", (1680, 1680))
            outline = [((x - box[0]) * 4, (y - box[1]) * 4) for x, y in points]
            ImageDraw.Draw(mask).polygon(outline, fill=255)
            portrait.putalpha(mask.resize(SIZE, Image.Resampling.LANCZOS))
            destination = ROOT / f"mika-{expression}.png"
            portrait.save(destination)
            print(destination.name, portrait.size)


if __name__ == "__main__":
    extract()
