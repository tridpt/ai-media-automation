"""Sinh nội dung (ảnh / audio / gif) bằng OpenAI hoặc Claude.

Lưu ý về khả năng của model:
- Tạo ẢNH: OpenAI có API tạo ảnh (gpt-image-1 / DALL-E). Claude KHÔNG tạo ảnh,
  nên nếu chọn model=claude cho ảnh, ta dùng Claude để tinh chỉnh/viết prompt
  rồi vẫn gọi OpenAI để render (fallback). Bạn có thể đổi tuỳ nhu cầu.
- Tạo AUDIO (MP3): dùng OpenAI text-to-speech.
- Tạo GIF: tạo nhiều khung ảnh rồi ghép bằng Pillow.
"""
import os
import base64
from io import BytesIO

from PIL import Image

from config import CONFIG
from src.retry import with_retry

# OpenAI được import "lười" (chỉ khi cần gọi API thật) để chế độ mock
# không bắt buộc phải cài thư viện openai.
_openai = None


def _get_openai():
    """Khởi tạo client OpenAI khi cần (lazy)."""
    global _openai
    if _openai is None:
        from openai import OpenAI

        if not CONFIG.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY chưa được cấu hình")
        kwargs = {"api_key": CONFIG.OPENAI_API_KEY}
        # Cho phép trỏ tới endpoint tương thích OpenAI (proxy/self-host).
        if CONFIG.OPENAI_BASE_URL:
            kwargs["base_url"] = CONFIG.OPENAI_BASE_URL
        _openai = OpenAI(**kwargs)
    return _openai


def _ensure_output_dir():
    os.makedirs(CONFIG.OUTPUT_DIR, exist_ok=True)


@with_retry(what="Claude refine prompt")
def _refine_prompt_with_claude(description: str) -> str:
    """Dùng Claude để viết lại mô tả thành prompt chi tiết hơn (tuỳ chọn)."""
    if not CONFIG.ANTHROPIC_API_KEY:
        return description
    from anthropic import Anthropic

    client = Anthropic(api_key=CONFIG.ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": (
                    "Rewrite the following into a vivid, detailed image "
                    f"generation prompt. Return only the prompt.\n\n{description}"
                ),
            }
        ],
    )
    return msg.content[0].text.strip()


@with_retry(what="OpenAI tạo ảnh")
def _generate_image_bytes(prompt: str) -> bytes:
    """Gọi OpenAI tạo 1 ảnh, trả về bytes PNG."""
    client = _get_openai()
    resp = client.images.generate(
        model=CONFIG.OPENAI_IMAGE_MODEL, prompt=prompt, size="1024x1024", n=1
    )
    # gpt-image-1 trả về b64_json; dall-e-3 mặc định trả về url -> xử lý cả hai.
    item = resp.data[0]
    if getattr(item, "b64_json", None):
        return base64.b64decode(item.b64_json)
    if getattr(item, "url", None):
        import requests

        r = requests.get(item.url, timeout=60)
        r.raise_for_status()
        return r.content
    raise RuntimeError("API tạo ảnh không trả về b64_json lẫn url")


def generate(task: dict) -> str:
    """Sinh output cho 1 task. Trả về đường dẫn file local đã tạo.

    task cần có: id, description, output_format, model
    """
    _ensure_output_dir()
    task_id = task.get("id") or task.get("_row")
    description = task["description"]
    fmt = task["output_format"].strip().lower()
    model = task["model"].strip().lower()

    # Chế độ mock: tạo file giả, không gọi API AI nào cả
    if CONFIG.MOCK:
        return _make_mock(task_id, description, fmt)

    # Nếu chọn claude thì dùng claude để tinh chỉnh prompt trước
    prompt = _refine_prompt_with_claude(description) if model == "claude" else description

    if fmt in ("png", "jpg", "jpeg"):
        return _make_image(task_id, prompt, fmt)
    if fmt == "gif":
        return _make_gif(task_id, prompt)
    if fmt in ("mp3", "audio"):
        return _make_audio(task_id, description)
    raise ValueError(f"Định dạng không hỗ trợ: {fmt}")


def _make_mock(task_id, description, fmt) -> str:
    """Tạo file giả để test pipeline offline (không gọi API).

    - Ảnh PNG/JPG: vẽ 1 ảnh có ghi mô tả bằng Pillow.
    - GIF: ghép vài khung ảnh màu khác nhau.
    - MP3: ghi 1 file nhị phân giả (đủ để upload/log/test luồng).
    """
    from PIL import ImageDraw

    fmt = fmt.lower()
    if fmt in ("png", "jpg", "jpeg"):
        ext = "jpg" if fmt in ("jpg", "jpeg") else "png"
        path = os.path.join(CONFIG.OUTPUT_DIR, f"task_{task_id}.{ext}")
        img = Image.new("RGB", (512, 512), (30, 90, 150))
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), "[MOCK]", fill=(255, 255, 0))
        draw.text((20, 60), _wrap(description), fill=(255, 255, 255))
        img.save(path, "JPEG" if ext == "jpg" else "PNG")
        return path

    if fmt == "gif":
        path = os.path.join(CONFIG.OUTPUT_DIR, f"task_{task_id}.gif")
        colors = [(200, 60, 60), (60, 200, 60), (60, 60, 200)]
        frames = []
        for i, c in enumerate(colors):
            fr = Image.new("RGB", (256, 256), c)
            d = ImageDraw.Draw(fr)
            d.text((10, 10), f"[MOCK] frame {i + 1}", fill=(255, 255, 255))
            frames.append(fr)
        frames[0].save(
            path, save_all=True, append_images=frames[1:], duration=500, loop=0
        )
        return path

    if fmt in ("mp3", "audio"):
        path = os.path.join(CONFIG.OUTPUT_DIR, f"task_{task_id}.mp3")
        # ghi vài byte giả để có file thật trên đĩa
        with open(path, "wb") as f:
            f.write(b"ID3" + b"\x00" * 128 + description.encode("utf-8"))
        return path

    raise ValueError(f"Định dạng không hỗ trợ: {fmt}")


def _wrap(text, width=48):
    """Ngắt dòng đơn giản cho text vẽ lên ảnh mock."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def _make_image(task_id, prompt, fmt) -> str:
    data = _generate_image_bytes(prompt)
    img = Image.open(BytesIO(data)).convert("RGB")
    ext = "jpg" if fmt in ("jpg", "jpeg") else "png"
    path = os.path.join(CONFIG.OUTPUT_DIR, f"task_{task_id}.{ext}")
    img.save(path, "JPEG" if ext == "jpg" else "PNG")
    return path


def _make_gif(task_id, prompt) -> str:
    """Tạo GIF đơn giản từ nhiều biến thể khung hình."""
    frames = []
    for i in range(3):
        data = _generate_image_bytes(f"{prompt} (frame {i + 1})")
        frames.append(Image.open(BytesIO(data)).convert("RGB"))
    path = os.path.join(CONFIG.OUTPUT_DIR, f"task_{task_id}.gif")
    frames[0].save(
        path, save_all=True, append_images=frames[1:], duration=600, loop=0
    )
    return path


@with_retry(what="OpenAI tạo audio")
def _make_audio(task_id, text) -> str:
    client = _get_openai()
    path = os.path.join(CONFIG.OUTPUT_DIR, f"task_{task_id}.mp3")
    with client.audio.speech.with_streaming_response.create(
        model=CONFIG.OPENAI_TTS_MODEL, voice="alloy", input=text
    ) as resp:
        resp.stream_to_file(path)
    return path
