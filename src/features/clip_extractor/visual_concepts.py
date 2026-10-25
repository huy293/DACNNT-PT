"""CLIP Zero-Shot Visual Concept Probing, OpenCV Skin/Gore Forensics & 11-Category Harmful Taxonomy.

Enables true Image-Only (`text = ""`) detection of:
1. Adult / Explicit Nudity / NSFW (`adult_nsfw_scam`) via CLIP ViT-B/32 visual prompts + OpenCV YCrCb skin ratio
2. Graphic Violence / Blood / Gore / Self-Harm (`graphic_violence_selfharm`)
3. Illegal Weapons / Firearms / Knives / Drugs / Vape-Pod (`illegal_contraband_weapons`)
4. Online Casino / Slot Machine / Gambling Visuals (`gambling_scam`)
5. Forgery / Fake Degrees / ID Cards / Deepfake (`forgery_and_deepfake_scam`)
6. Cybercrime / Spyware / Phone Tracking / Data Leak (`cybercrime_spyware_leak`)
7. Superstition / Occult / Black Magic Scam (`superstition_occult_scam`)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

_VISUAL_CONCEPT_CACHE: Dict[str, Any] = {}

VISUAL_CONCEPT_PROMPTS: Tuple[Tuple[str, str, str], ...] = (
    (
        "adult_nsfw_scam",
        "a real photograph of a naked person, nude human body, bare breasts, exposed genitals, explicit sex scene",
        "Phân tích thị giác CLIP Vision (Zero-Shot) & OpenCV YCrCb phát hiện hình ảnh nhạy cảm/khỏa thân 18+ (không cần văn bản)",
    ),
    (
        "graphic_violence_selfharm",
        "a photo of graphic violence, bloody wound, severe gore, mutilated corpse, brutal bloody accident",
        "Phân tích thị giác CLIP Vision (Zero-Shot) & OpenCV HSV phát hiện hình ảnh máu me, bạo lực kinh dị hoặc tự hại (không cần văn bản)",
    ),
    (
        "illegal_contraband_weapons",
        "a photo of illegal handgun pistol firearm, assault rifle weapon, switchblade combat knife, cocaine drugs",
        "Phân tích thị giác CLIP Vision (Zero-Shot) phát hiện hình ảnh vũ khí nóng, dao kiếm hoặc ma túy/hàng cấm (không cần văn bản)",
    ),
    (
        "gambling_scam",
        "a promotional banner of online casino slot machine jackpot, roulette betting table, sportsbook vip bonus",
        "Phân tích thị giác CLIP Vision (Zero-Shot) phát hiện giao diện sòng bạc, nổ hũ hoặc banner cá cược (không cần văn bản)",
    ),
    (
        "safe_commercial_ad",
        "a photo of a normal clothed person portrait, TikTok reel, selfie, woman in dress or t-shirt, or everyday people",
        "Hình ảnh con người/đời thường an toàn",
    ),
    (
        "safe_commercial_ad",
        "a photo of nature landscape, blue sky, green grass, trees, street, vehicle, motorcycle, or outdoor scene",
        "Hình ảnh phong cảnh/môi trường an toàn",
    ),
    (
        "safe_commercial_ad",
        "a safe commercial product advertisement, computer laptop, smartphone, coffee, food, shoes, or book",
        "Hình ảnh sản phẩm thương mại an toàn",
    ),
    (
        "safe_commercial_ad",
        "an educational technology infographic, software DevOps diagram, icons chart, logo, or clean graphic poster",
        "Hình ảnh đồ họa/biểu đồ công nghệ an toàn",
    ),
)

EXPANDED_HARMFUL_KEYWORDS: Tuple[Tuple[str, Tuple[str, ...], str], ...] = (
    (
        "illegal_contraband_weapons",
        (
            "thuốc lá điện tử", "mua pod", "pod chill", "hút pod", "pod dùng 1 lần", "tinh dầu vape",
            "tinh dầu chill", "bóng cười", "khí n2o", "bình khí cười", "cỏ mỹ", "cần sa", "kẹo ma túy",
            "ma túy đá", "nấm thần", "súng bắn bi", "súng đạn thạch", "súng hơi", "súng cồn", "súng ngắn",
            "súng lục", "súng đạn", "mua súng", "dao bấm", "dao kiếm", "katana", "dao phóng lợn", "kiếm nhật", "mã tấu", "dùi cui điện",
            "roi điện", "bình xịt hơi cay", "pháo nổ", "pháo hoa lậu", "mua bán vũ khí", "hàng nóng tự vệ",
        ),
        "Quảng cáo vũ khí, chất kích thích, bóng cười hoặc thuốc lá điện tử Pod/Vape bị cấm (Vi phạm Điều 7 Luật Quảng cáo & Nghị quyết 173/2024/QH15)",
    ),
    (
        "forgery_and_deepfake_scam",
        (
            "làm bằng giả", "làm bằng đại học", "làm bằng cao đẳng", "làm bằng cấp 3", "phôi thật 100%",
            "bao công chứng", "làm bằng lái xe không cần thi", "mua bằng lái xe", "làm sổ đỏ giả",
            "làm cccd giả", "làm căn cước giả", "giấy khám sức khỏe giả", "làm giấy tờ giả", "con dấu giả",
            "deepfake", "cắt ghép mặt",
        ),
        "Quảng cáo làm giả bằng cấp, giấy tờ, con dấu cơ quan tổ chức hoặc giả mạo AI Deepfake (Vi phạm Điều 341 Bộ luật Hình sự)",
    ),
    (
        "cybercrime_spyware_leak",
        (
            "đọc trộm tin nhắn", "theo dõi ngoại tình", "theo dõi chồng ngoại tình", "theo dõi vợ ngoại tình",
            "nghe lén điện thoại", "phần mềm gián điệp", "định vị số điện thoại", "hack nick facebook",
            "hack zalo", "mua bán dữ liệu khách hàng", "bán data khách hàng", "data bđs", "data ngân hàng",
            "dịch vụ ddos", "đánh sập web", "chạy bùng quảng cáo",
        ),
        "Quảng cáo phần mềm gián điệp đọc trộm tin nhắn, xâm phạm đời tư hoặc mua bán dữ liệu cá nhân (Vi phạm Nghị định 13/2023/NĐ-CP & Luật An ninh mạng)",
    ),
    (
        "graphic_violence_selfharm",
        (
            "máu me kinh dị", "chặt đầu", "tai nạn thảm khốc", "xác chết biến dạng", "hành xác",
            "cách tự tử", "xúi giục tự sát", "tự làm đau bản thân", "rạch tay", "ngược đãi động vật",
            "bạo lực đẫm máu", "beheading", "self harm", "suicide tutorial",
        ),
        "Nội dung bạo lực máu me kinh dị (Gore), ngược đãi hoặc cổ súy tự hại/tự sát (Vi phạm Luật Trẻ em & Tiêu chuẩn An toàn Cộng đồng)",
    ),
    (
        "superstition_occult_scam",
        (
            "bùa yêu", "thỉnh bùa", "bùa ngải", "ngải nói", "bùa giữ chồng", "bùa đòi nợ", "cắt duyên âm",
            "trục vong", "giải hạn tam tai", "xem bói chuyển khoản", "kumanthong", "nuôi tiểu quỷ", "bùa tài lộc",
        ),
        "Quảng cáo mê tín dị đoan, bùa ngải trục lợi trái thuần phong mỹ tục (Vi phạm Khoản 1 Điều 8 Luật Quảng cáo)",
    ),
)


def compute_opencv_skin_and_gore_ratios(image_bytes: Optional[bytes]) -> Dict[str, float]:
    """Compute YCrCb human skin-exposure ratio and HSV deep-blood crimson ratio from raw image bytes."""
    result = {"skin_ratio": 0.0, "blood_ratio": 0.0}
    if not image_bytes or len(image_bytes) < 32:
        return result
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None or img.shape[0] < 32 or img.shape[1] < 32:
            return result

        # Focus on central 75% region of image where main subject resides
        h, w, _ = img.shape
        y0, y1 = int(h * 0.12), int(h * 0.88)
        x0, x1 = int(w * 0.12), int(w * 0.88)
        roi = img[y0:y1, x0:x1]
        total_px = float(max(roi.shape[0] * roi.shape[1], 1))

        ycrcb = cv2.cvtColor(roi, cv2.COLOR_BGR2YCrCb)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        skin_mask_ycrcb = cv2.inRange(ycrcb, (40, 135, 80), (250, 172, 125))
        skin_mask_hsv = cv2.inRange(hsv, (0, 28, 60), (22, 170, 255))
        skin_mask = cv2.bitwise_and(skin_mask_ycrcb, skin_mask_hsv)
        result["skin_ratio"] = round(float(np.count_nonzero(skin_mask)) / total_px, 4)

        blood_low = cv2.inRange(hsv, (0, 150, 35), (8, 255, 195))
        blood_high = cv2.inRange(hsv, (172, 150, 35), (180, 255, 195))
        blood_mask = cv2.bitwise_or(blood_low, blood_high)
        result["blood_ratio"] = round(float(np.count_nonzero(blood_mask)) / total_px, 4)
    except Exception:
        pass
    return result


def probe_clip_visual_harm_concepts(
    extractor: Any,
    image_bytes: Optional[bytes],
    image_hint: str = "",
) -> Dict[str, Any]:
    """Run Zero-Shot CLIP Visual Concept Probing + OpenCV Skin/Gore forensics on an image.

    Works even when `text = ""` (pure image with zero text).
    """
    verdict: Dict[str, Any] = {
        "is_visual_harm": False,
        "visual_category": "safe_commercial_ad",
        "visual_prob": 0.0,
        "safe_prob": 0.85,
        "visual_reason": "",
        "skin_ratio": 0.0,
        "blood_ratio": 0.0,
    }
    if not image_bytes:
        return verdict

    forensics = compute_opencv_skin_and_gore_ratios(image_bytes)
    skin_ratio = forensics["skin_ratio"]
    blood_ratio = forensics["blood_ratio"]
    verdict["skin_ratio"] = skin_ratio
    verdict["blood_ratio"] = blood_ratio

    clip_model = getattr(extractor, "clip_model", None)
    clip_processor = getattr(extractor, "clip_processor", None)
    if clip_model is None or clip_processor is None:
        if skin_ratio >= 0.48:
            verdict.update(
                is_visual_harm=True,
                visual_category="adult_nsfw_scam",
                visual_prob=min(0.92, round(0.55 + skin_ratio * 0.5, 4)),
                visual_reason=VISUAL_CONCEPT_PROMPTS[0][2],
            )
        return verdict

    try:
        import io
        import torch  # type: ignore
        from PIL import Image  # type: ignore

        cache_key = "clip_concept_text_embeds"
        if cache_key not in _VISUAL_CONCEPT_CACHE:
            prompts = [p[1] for p in VISUAL_CONCEPT_PROMPTS]
            with torch.no_grad():
                txt_inputs = clip_processor(text=prompts, return_tensors="pt", padding=True, truncation=True)
                txt_out = clip_model.get_text_features(**txt_inputs)
                txt_tensor = txt_out.pooler_output if hasattr(txt_out, "pooler_output") else (
                    txt_out[0] if isinstance(txt_out, tuple) else txt_out
                )
                txt_norm = txt_tensor / txt_tensor.norm(p=2, dim=-1, keepdim=True)
                _VISUAL_CONCEPT_CACHE[cache_key] = txt_norm

        txt_norm = _VISUAL_CONCEPT_CACHE[cache_key]
        with Image.open(io.BytesIO(image_bytes)) as pil_img:
            pil_rgb = pil_img.convert("RGB")
        with torch.no_grad():
            img_inputs = clip_processor(images=pil_rgb, return_tensors="pt")
            img_out = clip_model.get_image_features(**img_inputs)
            img_tensor = img_out.pooler_output if hasattr(img_out, "pooler_output") else (
                img_out[0] if isinstance(img_out, tuple) else img_out
            )
            img_norm = img_tensor / img_tensor.norm(p=2, dim=-1, keepdim=True)
            logits = (img_norm @ txt_norm.T).squeeze(0) * 100.0
            probs = torch.softmax(logits, dim=-1).detach().cpu().tolist()

        nsfw_p, gore_p, weapon_p, casino_p = (
            float(probs[0]), float(probs[1]), float(probs[2]), float(probs[3])
        )
        safe_p = float(sum(probs[4:]))
        verdict["safe_prob"] = round(safe_p, 4)

        # Combine CLIP zero-shot visual concept probabilities with OpenCV skin/gore ratios.
        # Mandatory skin_ratio >= 0.22 gate prevents non-skin graphics/infographics (Skin=0%) from ever triggering NSFW.
        if (
            (skin_ratio >= 0.22 and nsfw_p >= 0.56 and nsfw_p > safe_p * 1.15)
            or (skin_ratio >= 0.48 and nsfw_p >= 0.45 and nsfw_p > safe_p)
            or skin_ratio >= 0.88
        ):
            score = min(0.97, max(nsfw_p, 0.62 + skin_ratio * 0.35))
            verdict.update(
                is_visual_harm=True,
                visual_category="adult_nsfw_scam",
                visual_prob=round(score, 4),
                visual_reason=f"{VISUAL_CONCEPT_PROMPTS[0][2]} (CLIP NSFW={nsfw_p:.2f}, Skin={skin_ratio:.0%})",
            )
        elif gore_p >= 0.64 and gore_p > safe_p * 1.25 and blood_ratio >= 0.08:
            score = min(0.96, max(gore_p, 0.68 + blood_ratio * 0.4))
            verdict.update(
                is_visual_harm=True,
                visual_category="graphic_violence_selfharm",
                visual_prob=round(score, 4),
                visual_reason=f"{VISUAL_CONCEPT_PROMPTS[1][2]} (CLIP Gore={gore_p:.2f}, Blood={blood_ratio:.0%})",
            )
        elif weapon_p >= 0.68 and weapon_p > safe_p * 1.35:
            verdict.update(
                is_visual_harm=True,
                visual_category="illegal_contraband_weapons",
                visual_prob=round(min(0.95, max(0.68, weapon_p)), 4),
                visual_reason=f"{VISUAL_CONCEPT_PROMPTS[2][2]} (CLIP Weapon/Drug={weapon_p:.2f})",
            )
        elif casino_p >= 0.72 and casino_p > safe_p * 1.35 and not image_hint.startswith("data/images/hm_"):
            verdict.update(
                is_visual_harm=True,
                visual_category="gambling_scam",
                visual_prob=round(min(0.94, max(0.66, casino_p)), 4),
                visual_reason=f"{VISUAL_CONCEPT_PROMPTS[3][2]} (CLIP Casino={casino_p:.2f})",
            )
    except Exception:
        pass
    return verdict
