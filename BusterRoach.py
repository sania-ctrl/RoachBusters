#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageColor
from google import genai
from google.genai import types
import os, json, re, time

os.environ["GEMINI_API_KEY"] = "ADD_KEY_HERE"

# Selecting Image taken from Rasp Pi Camera
def get_highest_numbered_image(folder_path: str | Path) -> Path:
    """
    Finds the image with the highest numeric filename (e.g., 1.jpg, 2.jpg, 3.jpg)
    in the given folder and returns its Path.
    """
    folder = Path(folder_path).expanduser().resolve()
    if not folder.exists():
        raise FileNotFoundError(f"No such folder: {folder}")

    image_files = []
    for f in folder.iterdir():
        if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
            try:
                num = int(f.stem)
                image_files.append((num, f))
            except ValueError:
                pass

    if not image_files:
        raise FileNotFoundError(f"No numbered image files (.jpg/.jpeg/.png) found in {folder}")

    _, highest_file = max(image_files, key=lambda x: x[0])
    print(f"Selected image: {highest_file.name}")
    return highest_file


# selecting next highest image
def next_incremental_name(folder: Path, ext: str = ".txt") -> Path:
    """
    Finds the next numeric filename in the folder (1.txt, 2.txt, ... or 1.jpg, 2.jpg, ...).
    """
    folder.mkdir(parents=True, exist_ok=True)
    nums = []
    for f in folder.glob(f"*{ext}"):
        try:
            nums.append(int(f.stem))
        except ValueError:
            pass
    n = (max(nums) if nums else 0) + 1
    return folder / f"{n}{ext}"


def run_local_bbox(
    image_path: str,
    *,
    model_name: str = "gemini-2.5-pro",
    prompt: str = "Give an explanation of why the item potentially attracts cockroaches as label. Only allowed to label cockroach.",
    system_instructions: str = """
Return bounding boxes as a JSON array with labels. Never return masks or code fencing. Limit to 25 objects.
Each item must be: {"box_2d":[y1, x1, y2, x2], "label":"..."} with normalized coords in 0..1000.
If an object appears multiple times, distinguish by color/size/position.
""",
    max_side: int = 640,
    temperature: float = 0.3,
    boxed_dir: Path | None = None,
    labels_dir: Path | None = None,
    retry: int = 3,
    backoff_sec: int = 10,
) -> tuple[Path, Path]:
    """
    Loads a local image, calls Gemini for bounding boxes, draws boxes + labels,
    saves boxed image to boxed_dir/<n>.jpg and labels to labels_dir/<n>.txt.

    Returns (boxed_image_path, label_text_path).
    """

    def parse_json_output(text: str) -> str:
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip() == "```json":
                text = "\n".join(lines[i + 1 :])
                text = text.split("```")[0]
                break
        return text

    def next_font():
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        for p in candidates:
            if Path(p).exists():
                try:
                    return ImageFont.truetype(p, size=16)
                except Exception:
                    pass
        return ImageFont.load_default()

    def draw_boxes(img: Image.Image, boxes_json: str):
        try:
            boxes = json.loads(parse_json_output(boxes_json))
        except Exception as e:
            raise RuntimeError(f"Model did not return valid JSON: {e}\nRaw text:\n{boxes_json}")

        draw = ImageDraw.Draw(img)
        w, h = img.size
        base_colors = [
            'red','green','blue','yellow','orange','pink','purple','brown','gray','beige',
            'turquoise','cyan','magenta','lime','navy','maroon','teal','olive','coral',
            'lavender','violet','gold','silver'
        ]
        colors = base_colors + list(ImageColor.colormap.keys())
        font = next_font()

        labels_local = []
        for i, bb in enumerate(boxes):
            color = colors[i % len(colors)]
            y1, x1, y2, x2 = bb["box_2d"]
            ax1 = int(x1 / 1000 * w)
            ay1 = int(y1 / 1000 * h)
            ax2 = int(x2 / 1000 * w)
            ay2 = int(y2 / 1000 * h)
            if ax1 > ax2:
                ax1, ax2 = ax2, ax1
            if ay1 > ay2:
                ay1, ay2 = ay2, ay1
            draw.rectangle([(ax1, ay1), (ax2, ay2)], outline=color, width=4)
            if "label" in bb:
                txt = str(bb["label"])
                labels_local.append(txt)
                tw, th = draw.textbbox((0, 0), txt, font=font)[2:]
                pad = 4
                draw.rectangle(
                    [ax1 + 4, ay1 + 4, ax1 + 4 + tw + 2 * pad, ay1 + 4 + th + 2 * pad],
                    fill="black",
                )
                draw.text((ax1 + 4 + pad, ay1 + 4 + pad), txt, fill=color, font=font)
        return labels_local

    def load_image(path: Path, max_side=640) -> Image.Image:
        img = Image.open(path).convert("RGB")
        img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        return img

    # ---------- main ----------
    src = Path(image_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"No such image: {src}")

    img = load_image(src, max_side=max_side)

    client = genai.Client()

    # Retrying in case LLM provides wrong output
    last_err = None
    for attempt in range(1, retry + 1):
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=[prompt, img],
                config=types.GenerateContentConfig(
                    system_instruction=system_instructions,
                    temperature=temperature,
                    safety_settings=[
                        types.SafetySetting(
                            category="HARM_CATEGORY_DANGEROUS_CONTENT",
                            threshold="BLOCK_ONLY_HIGH",
                        )
                    ],
                    thinking_config=types.ThinkingConfig(thinking_budget=-1),
                ),
            )
            break  # success
        except Exception as e:
            last_err = e
            if attempt < retry:
                print(f"[Attempt {attempt}/{retry}] Model call failed: {e}\nRetrying in {backoff_sec}s...")
                time.sleep(backoff_sec)
            else:
                raise

    if not getattr(resp, "text", None):
        raise RuntimeError(f"Model returned no text. Full response: {resp}")

    out_img = img.copy()
    labels = draw_boxes(out_img, resp.text)

    # Images annotated by Gemini sent to the annotated or "boxed" images folder
    base_dir = Path(__file__).resolve().parent
    boxed_dir = boxed_dir or (base_dir / "boxed_images")
    labels_dir = labels_dir or (base_dir / "label")
    boxed_dir.mkdir(exist_ok=True, parents=True)
    labels_dir.mkdir(exist_ok=True, parents=True)

    # Save outputs with incremental numbering
    boxed_path = next_incremental_name(boxed_dir, ext=".jpg")
    out_img.save(boxed_path, quality=95)

    label_path = next_incremental_name(labels_dir, ext=".txt")
    with open(label_path, "w", encoding="utf-8") as f:
        f.write(f"image={src.name}\n")
        for line in labels:
            f.write(line.rstrip() + "\n")

    print(f"Saved boxed image: {boxed_path}")
    print(f"Saved labels: {label_path}")
    return boxed_path, label_path


# Main function that processes the images, then annotates it, and then adds in the labels
def buster_main(
    images_dir: str | Path = None,
    boxed_dir: str | Path = None,
    labels_dir: str | Path = None,
) -> tuple[Path, Path]:
    """
    Orchestrates the full pipeline:
      - picks highest-numbered image from images_dir
      - runs Gemini bbox pipeline
      - saves outputs into boxed_dir and labels_dir
      - returns (boxed_image_path, label_text_path)
    """
    base = Path(__file__).resolve().parent
    images_dir = Path(images_dir) if images_dir else (base / "images")
    boxed_dir = Path(boxed_dir) if boxed_dir else (base / "boxed_images")
    labels_dir = Path(labels_dir) if labels_dir else (base / "label")

    highest_image = get_highest_numbered_image(images_dir)
    return run_local_bbox(
        str(highest_image),
        boxed_dir=boxed_dir,
        labels_dir=labels_dir,
        retry=3,
        backoff_sec=10,
    )


if __name__ == "__main__":
    boxed_path, label_path = buster_main()
    print("Done.", boxed_path, label_path)
