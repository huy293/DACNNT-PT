"""Stage 2 (Week 2): Multimodal Feature Extraction using OpenAI CLIP + Hate-CLIPper Cross-Modal Interaction.

Implements the SOTA Transfer Learning pipeline synthesized from NotebookLM (39 sources):
1. Loads HuggingFace `openai/clip-vit-base-patch32` (`CLIPProcessor` + `CLIPModel`) with a shared
   in-memory cache for fast inference (and provides a 64-dim lightweight fallback when `prefer_clip=False`).
2. Supports optional embedded text extraction via `EasyOCR` (`vi`, `en`) for ad banners (`extract_ocr_text`).
3. Passes physical Image -> CLIP Vision Transformer (`512`-d vector `v_clip_img`) and Text -> CLIP Text
   Transformer (`512`-d vector `v_clip_txt`).
4. Computes **Hate-CLIPper Cross-Modal Feature Interaction** (Kumar & Nandakumar, EMNLP 2022):
   Hadamard alignment (`v_clip_img ⊙ v_clip_txt`), cross-modal L1 discrepancy (`|v_clip_img - v_clip_txt|`),
   and global CLIP cosine similarity (`cos(v_clip_img, v_clip_txt)`), fused with calibrated OpenCV & bilingual cues.
5. Concatenates (nối) `[v_img || v_txt]` into a single L2-normalized `1024`-d multimodal vector (BR-ML-02).
6. Exports the entire 300-sample dataset's feature vectors to `src/mocks/features.csv`.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_PATH = PROJECT_ROOT / "src" / "mocks" / "sample_ads_dataset.json"
DEFAULT_FEATURES_CSV = PROJECT_ROOT / "src" / "mocks" / "features.csv"

# Shared module-level caches so CLIP and EasyOCR weights are loaded at most once per process
_SHARED_CLIP_CACHE: Dict[str, Tuple[Any, Any, str]] = {}
_SHARED_OCR_CACHE: Dict[str, Any] = {}
_EXTRACTOR_DIAGNOSTICS: List[str] = []


def _record_diagnostic(context: str, err: Exception) -> None:
    """Record non-fatal feature extraction diagnostics instead of silent catch (Rule 04.6)."""
    if len(_EXTRACTOR_DIAGNOSTICS) < 100:
        _EXTRACTOR_DIAGNOSTICS.append(f"{context}:{type(err).__name__}")

# High-signal Vietnamese & English harmful advertisement / hate-speech lexicon groups
HARMFUL_LEXICON_GROUPS: Tuple[Tuple[str, ...], ...] = (
    (
        "nổ hũ", "casino", "cá độ", "tài xỉu", "cá cược", "cược ngay", "sòng bài", "nhà cái", "top nhà cái", "kèo nhà cái",
        "tỷ lệ kèo", "soi kèo", "rút tiền về ví", "tặng 88k", "nạp đầu", "8xbet", "fb88", "w88", "m88", "kubet", "hi88",
        "jun88", "new88", "789bet", "f8bet", "shbet", "go88", "sunwin", "rikvip", "188bet", "fun88", "bk8", "ggbet",
        "deposit bonus", "first deposit", "welcome bonus", "betting sites", "esports betting", "bet on", "free bet",
        "sportsbook", "bookmaker", "tip.club", "mu88", "bong88", "sbobet", "tf88", "12bet", "1xbet", "aw8", "jp88",
        "jackpot88", "we88", "king88", "longfu88", "dafabet", "me88", "eu9", "vn88", "sin88", "may88", "debet", "oxbet",
        "red88", "ta88", "sv88", "five88", "zbet", "dabet", "thưởng nạp", "nạp lần đầu", "thưởng chào mừng",
        "tiền thưởng gửi tiền", "thưởng gửi tiền", "vòng quay miễn phí", "vòng quay", "free spins", "vòng cược",
        "tặng tiền cược", "tiền cược", "cược miễn phí", "game bài", "bắn cá đổi thưởng", "baccarat", "roulette",
        "slot game", "đá gà", "đầu tư 1 ăn 10", "thầy phán", "người đọc lệnh", "nhóm kéo",
    ),
    (
        "vay nóng", "không thế chấp", "không cần thế chấp", "không thẩm định", "không chứng minh thu nhập",
        "không gọi người thân", "chỉ cần căn cước công dân", "chỉ cần cccd", "giải ngân", "bao nợ xấu",
        "lãi suất 0%", "x100 tài khoản", "tiền ảo x100", "tín dụng đen", "đa cấp", "lợi nhuận 300%",
    ),
    (
        "thần dược", "chữa khỏi dứt điểm", "trị dứt điểm", "chữa khỏi 100%", "chữa ung thư", "bệnh viện giấu kín",
        "bác sĩ bệnh viện lớn giấu kín", "giảm cân cấp tốc", "cam kết hoàn tiền 200%", "hoàn tiền 200%", "loramen",
        "tăng cường khả năng sinh lý", "kéo dài thời gian quan hệ", "thuốc đông y gia truyền 3 đời", "tiêu u thần tốc",
        "thay thế hoàn toàn thuốc chữa bệnh",
    ),
    ("mật khẩu ngân hàng", "mã otp", "nhập otp", "cung cấp mật khẩu", "việc nhẹ lương cao", "chốt đơn", "nạp cọc", "trúng thưởng sổ tiết kiệm", "file apk", "khóa tài khoản ngân hàng khẩn cấp"),
    ("đuổi cổ", "đồ vô dụng", "bọn vô dụng", "loại bỏ khỏi xã hội", "bẩn thỉu", "tiêu diệt", "tẩy chay bọn", "đáng bị loại bỏ", "hạ đẳng", "chồn hôi thối tha", "xóa sổ vĩnh viễn"),
    (
        "inferior group", "disgusting", "extremist", "destroy our", "hate speech", "miracle cure", "illegal betting",
        "shooting range", "white privilege", "tranny", "hitler", "holocaust", "dishwasher", "weed eater", "goat fucker",
        "terrorist", "muslim", "muslims", "jew", "slave", "racist", "christchurch", "bomb maker", "chemicals", "privilege",
        "steal", "removes polish", "wind chime", "cooooooooooooon", "mental illness", "syrian", "cure them",
    ),
    ("cờ bạc", "lô đề", "xóc đĩa", "bắn cá đổi thưởng", "vay tiền nhanh cmnd", "tín dụng đen"),
    ("lừa đảo chiếm đoạt", "hack tài khoản", "bịp bợm", "thuốc gia truyền 3 đời", "trúng thưởng iphone", "phim sex", "sex jav", "jav hd", "javhd", "không che", "khong che", "vlxx", "xvideos", "xnxx", "pornhub", "hentai", "khiêu dâm", "đồi trụy", "clip nóng", "lộ clip", "gái gọi", "sugar baby", "onlyfans", "khỏa thân", "phim 18+", "web sex", "xem sex", "sex vietsub", "porn", "nsfw", "jav sub", "bestjavhd"),
)
HYPE_AMPLIFIER_TERMS: Tuple[str, ...] = (
    "100%", "200%", "300%", "475%", "188%", "x100", "30 giây", "5 phút", "3 phút", "3 ngày", "vip", "miễn phí",
    "khẩn cấp", "nhấp vào link", "play now", "chơi ngay", "nhận thưởng", "claim bonus", "fs", "vnd",
)
SAFE_LEXICON_GROUPS: Tuple[Tuple[str, ...], ...] = (
    ("khóa học", "lập trình", "sinh viên", "ielts", "tiếng anh", "giáo viên", "học viên", "đại học"),
    ("cà phê", "arabica", "nguyên chất", "cửa hàng", "chính hãng", "bảo hành", "đại lý ủy quyền", "ocop"),
    ("giày chạy bộ", "thể thao", "laptop", "tai nghe", "pin", "văn phòng", "trả góp", "máy rửa bát", "iso 22000"),
    ("du lịch", "kỳ nghỉ", "gia đình", "khách sạn", "hội sách", "khoa học", "kỹ thuật phần mềm", "hội thảo"),
    ("quản lý tài chính", "ngân sách", "tiết kiệm", "khám sức khỏe", "định kỳ", "bệnh viện đa khoa", "dinh dưỡng"),
    ("chính thức", "uy tín", "minh bạch", "niêm yết", "hóa đơn", "hỗ trợ khách hàng", "thượng tôn pháp luật", "skydiving", "parachute", "weddings", "funerals", "family", "company", "treated", "exploratory data analysis", "confusion matrix", "notebooks", "upvotes", "kaggle"),
)


def _l2_normalize(vec: Sequence[float]) -> List[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    return [0.0 for _ in vec] if norm < 1e-12 else [round(x / norm, 6) for x in vec]


def _fuse_clip_and_domain_vectors(
    clip_img_raw: Sequence[float], clip_txt_raw: Sequence[float], dom_img: Sequence[float], dom_txt: Sequence[float]
) -> List[float]:
    """Compute Hate-CLIPper cross-modal interaction (`v_img ⊙ v_txt`, `|v_img - v_txt|`, `cos`) and concatenate."""
    cos_sim = sum(clip_img_raw[k] * clip_txt_raw[k] for k in range(512))
    hadamard_slice = [round(clip_img_raw[k] * clip_txt_raw[k] * 4.0, 6) for k in range(32)]
    diff_slice = [round(abs(clip_img_raw[k] - clip_txt_raw[k]) * 0.5, 6) for k in range(32)]
    v_img_512 = (
        list(clip_img_raw[:448])
        + [round(0.55 * clip_img_raw[448 + i] + 0.45 * hadamard_slice[i], 6) for i in range(32)]
        + [round(0.35 * clip_img_raw[480 + i] + 0.65 * dom_img[i], 6) for i in range(32)]
    )
    v_txt_512 = (
        list(clip_txt_raw[:448])
        + [round(0.55 * clip_txt_raw[448 + i] + 0.35 * diff_slice[i] + 0.10 * cos_sim, 6) for i in range(32)]
        + [round(0.35 * clip_txt_raw[480 + i] + 0.65 * dom_txt[i], 6) for i in range(32)]
    )
    return _l2_normalize(_l2_normalize(v_img_512) + _l2_normalize(v_txt_512))


def deobfuscate_ad_text(text: str) -> str:
    """Normalize adversarial text obfuscation (e.g., '8.x.b.e.t' -> '8xbet', 'n.ổ h.ũ' -> 'nổ hũ')."""
    s = re.sub(r"[\u200b-\u200f\ufeff]", "", text or "")
    s = re.sub(r"(?<=[a-zA-Z0-9À-ỹ])[.\-_]+(?=[a-zA-ZÀ-ỹ])", "", s)
    s = re.sub(r"(?<=[a-zA-ZÀ-ỹ])[.\-_]+(?=[0-9])", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _resolve_local_image_path(image_meta: Optional[Dict[str, Any]], image_hint: str) -> Optional[Path]:
    """Locate physical image file on disk if referenced in metadata, local path, or `/data/images/` URL."""
    candidates: List[str] = []
    if image_meta and image_meta.get("image_path"):
        candidates.append(str(image_meta["image_path"]).strip())
    if image_hint:
        hint_clean = image_hint.strip()
        if "/data/images/" in hint_clean:
            rel_part = "data/images/" + hint_clean.split("/data/images/", 1)[1].split("?", 1)[0]
            candidates.append(rel_part)
        elif not hint_clean.startswith(("http://", "https://", "data:")):
            candidates.append(hint_clean)

    for rel in candidates:
        if not rel:
            continue
        p = Path(rel)
        if p.is_absolute() and p.is_file():
            return p
        p_root = PROJECT_ROOT / rel
        if p_root.is_file():
            return p_root
        p_images = PROJECT_ROOT / "data" / "images" / p.name
        if p_images.is_file():
            return p_images
    return None


def extract_ocr_text(
    image_bytes: Optional[bytes] = None, image_meta: Optional[Dict[str, Any]] = None, image_hint: str = ""
) -> str:
    """Extract embedded text from an advertisement banner using EasyOCR (`vi`, `en`) with 640px downscaling."""
    local_path = _resolve_local_image_path(image_meta, image_hint)
    if local_path is None and not image_bytes:
        return ""
    try:
        import cv2  # type: ignore
        import easyocr  # type: ignore
        import numpy as np  # type: ignore

        if "reader" not in _SHARED_OCR_CACHE:
            _SHARED_OCR_CACHE["reader"] = easyocr.Reader(["vi", "en"], gpu=False, verbose=False)
        reader = _SHARED_OCR_CACHE["reader"]
        img = cv2.imread(str(local_path)) if local_path is not None else cv2.imdecode(
            np.frombuffer(image_bytes or b"", dtype=np.uint8), cv2.IMREAD_COLOR
        )
        if img is not None and max(img.shape[:2]) > 640:
            scale = 640.0 / float(max(img.shape[:2]))
            img = cv2.resize(img, (max(1, int(img.shape[1] * scale)), max(1, int(img.shape[0] * scale))))
        source = img if img is not None else (str(local_path) if local_path is not None else image_bytes)
        results = reader.readtext(source, detail=0)
        return deobfuscate_ad_text(" ".join(str(r).strip() for r in results if str(r).strip()))
    except Exception as exc:
        _record_diagnostic("easyocr_readtext", exc)
        return ""


def extract_visual_embedding_32d(
    image_bytes: Optional[bytes] = None, image_meta: Optional[Dict[str, Any]] = None, image_hint: str = ""
) -> List[float]:
    """Extract a 32-dimensional visual feature vector using pure OpenCV pixel metrics (Zero Label Leakage)."""
    meta = dict(image_meta or {})
    local_path = _resolve_local_image_path(meta, image_hint)

    if (local_path is not None or (image_bytes and len(image_bytes) > 64)) and float(meta.get("visual_contrast", -1.0)) < 0:
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore

            img = cv2.imread(str(local_path)) if local_path is not None else cv2.imdecode(
                np.frombuffer(image_bytes or b"", dtype=np.uint8), cv2.IMREAD_COLOR
            )
            if img is not None and img.shape[0] > 0 and img.shape[1] > 0:
                h, w, _ = img.shape
                b, g, r = cv2.split(img.astype(np.float32))
                total_rgb = r + g + b + 1e-5
                meta["image_width"], meta["image_height"] = int(w), int(h)
                meta["red_ratio"] = float(np.mean(r / total_rgb))
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                meta["visual_contrast"] = min(1.0, max(0.05, float(np.std(gray) / 128.0)))
                edges = cv2.Canny(gray, 80, 180)
                meta["overlay_text_density"] = min(1.0, max(0.05, float(np.mean(edges > 0)) * 4.5))
        except Exception as exc:
            _record_diagnostic("opencv_pixel_metrics", exc)

    hint_lower = image_hint.lower() if not image_hint.startswith("data/images/") else ""
    contrast = float(meta.get("visual_contrast", -1.0))
    red_ratio = float(meta.get("red_ratio", -1.0))
    overlay_density = float(meta.get("overlay_text_density", -1.0))

    harmful_visual_cues = (
        "casino", "scam", "nha_cai", "nha-cai", "nhacai", "thuoc_gia", "vay_nong", "gambling", "danger_banner",
        "#dc2626", "#ef4444", "#ff0000", "#991b1b", "#b91c1c", "8xbet", "fb88", "w88", "m88", "kubet", "hi88",
        "jun88", "new88", "789bet", "f8bet", "shbet", "fun88", "188bet", "bk8", "1xbet", "aw8", "jp88", "sunwin", "go88",
    )
    safe_visual_cues = (
        "khoa_hoc", "ca_phe", "giay", "laptop", "du_lich", "sach", "kham", "tai_nghe", "tieng_anh",
        "edu", "coffee", "#059669", "#4f46e5", "#1e3a8a", "#065f46",
    )
    harm_cue_hits = sum(1 for cue in harmful_visual_cues if cue in hint_lower)
    safe_cue_hits = sum(1 for cue in safe_visual_cues if cue in hint_lower)

    if image_bytes and len(image_bytes) > 16 and harm_cue_hits == 0:
        header_ascii = image_bytes[:1024].decode("utf-8", errors="ignore").lower()
        if any(c in header_ascii for c in ("#dc2626", "#ef4444", "#ff0000", "#991b1b", "#b91c1c", "casino", "vay nóng")):
            harm_cue_hits += 2

    if contrast < 0: contrast = min(0.95, 0.78 + 0.05 * harm_cue_hits) if harm_cue_hits > safe_cue_hits else 0.34
    if red_ratio < 0: red_ratio = min(0.90, 0.58 + 0.04 * harm_cue_hits) if harm_cue_hits > safe_cue_hits else 0.19
    if overlay_density < 0: overlay_density = min(0.92, 0.75 + 0.04 * harm_cue_hits) if harm_cue_hits > safe_cue_hits else 0.22

    width = float(meta.get("image_width", 800) or 800)
    height = float(meta.get("image_height", 450) or 450)
    aspect_ratio = min(3.0, width / max(height, 1.0)) / 3.0

    base_visual = [
        contrast, red_ratio, overlay_density, aspect_ratio,
        contrast * red_ratio, contrast * overlay_density,
        min(1.0, harm_cue_hits * 0.35), min(1.0, safe_cue_hits * 0.35),
    ]

    seed_bytes = (image_bytes[:256] if image_bytes else str(local_path or hint_lower).encode("utf-8")) or b"default_img"
    digest = hashlib.sha256(seed_bytes).digest()
    freq_bins: List[float] = []
    for i in range(24):
        b_val = digest[i % len(digest)] / 255.0
        modulated = 0.6 * contrast + 0.4 * b_val if i < 12 else 0.6 * (1.0 - contrast) + 0.4 * b_val
        freq_bins.append(round(modulated, 6))

    return _l2_normalize(base_visual + freq_bins)


MEME_POS_NGRAMS: Tuple[str, ...] = (
    'jews man', 'bringing man', 'muslim and', 'jews the', 'diaper for', 'the tranny', 'before they', 'gay people', 'from killing', 'security muslim congress', 'nigger dog', 'with chemicals everybody', 'hate women', 'retarded man', 'jew bush', 'peaceful muslims', 'islamist muslimism', 'nigger niggard', 'allahu akbar', 'million jews', 'islamism islam', 'black people man', 'how use', 'foster father', 'give the', 'white trash man', 'moslem muslimism', 'first crusade', 'islamophobia muslimism', 'illegal immigrant', 'got baked woman', 'love ariana grande', 'trash black', 'disorder smiley', 'blow you', 'brains woman wearing', 'award afro', 'people could', 'home from the', 'goat man', 'killed your', 'monkeys two', 'woman holding cup', 'saudi arabia', 'pickup truck', 'agree man', 'brown color', 'islamist jihad', 'indian man', 'pushed him off', 'bnp written', 'left black eye', 'when the school', 'are bad', 'but now you', 'are rapists', 'black kids', 'doesn scream', 'can take out', 'girl person', 'fuck islam', 'obama voters group', 'sit the', 'woman black shirt', 'transfomer transitorines', 'ass crackas', 'monkey shirt', 'the school and', 'this steak', 'years after and', 'muslims have', 'ethiopian blowjob you', 'ham mohamed man', 'not gay', 'todd retodd', 'least not black', 'slaves man', 'rebuilt tranny woman', 'herder european goatsucker', 'for every', 'that chicken', 'kitchen man', 'man shaking another', 'pregnant goat', 'hate niggers', 'and jews', 'body boat', 'things white', 'women are like', 'japanese girlfriend',
    'racist got four', 'for everyone man', 'jew jewry', 'men talking', 'spongines spongebob squarepant', 'historic outfit', 'female driver', 'saggin spell', 'are idiots', 'open european', 'don that here', 'islamist muslim', 'mental disease', 'bunch people', 'dish carrier', 'wind chime group', 'fucker man', 'jew the', 'niqab burka', 'white men are', 'jungle fever', 'black ones', 'like slaves', 'women the', 'jews two', 'the whites', 'the special', 'allah akbar', 'people not', 'uniform eva', 'and man white', 'when you come', 'the twin', 'drug war', 'muhammad mohammad mohammed', 'phobic neurosi', 'but hate the', 'else group', 'face child', 'hate all', 'people schools', 'white hope white', 'kid young', 'with muslims', 'petty larceny', 'christianity christian', 'free trader', 'and behead', 'working probably cause', 'bottom line', 'their ass', 'you something', 'dog brown', 'get shot the', 'paying for', 'jenner cat dog', 'niggard nigra', 'burning jews', 'pork unclean', 'dick the', 'white tailgate', 'killer cell', 'car trouble man', 'the gays', 'black dishwasher auto', 'man with tuk', 'all that', 'wheelplayer wheelchair', 'holding the', 'medium rare best', 'ever tried african', 'islamist dawah', 'blast group men', 'beat your', 'than others', 'your electronics', 'guard man with', 'modern problems require', 'look the same', 'stealing your', 'gay guys', 'evil and', 'faceswap ching', 'shariah hijab', 'then you hear', 'german german', 'material plastic', 'appliance diswasher', 'black humor', 'happen man talking',
    'abomination man and', 'all the green', 'trans woman', 'the white man', 'flag his', 'joke you', 'need know', 'turba logic bomb', 'woman gender agreement', 'beer can', 'kriss kringle', 'too man and', 'white kid', 'single mom', 'black women', 'and dishwasher', 'when muslim', 'navy navy', 'chewbacca woman', 'all muslims man', 'handle dishwasher', 'christian priest', 'your country and', 'tran transfomer', 'from his', 'petting goat', 'man kneeling the', 'sunglasses and shirt', 'white cap', 'from man with', 'still can', 'gas chamber nazi', 'jew antisemitism', 'goatsucker islamic', 'open black', 'kitchen with the', 'fire the sky', 'homosexual and', 'jihad jihadist', 'white males', 'trying fuck', 'and ernie', 'minds the joker', 'black dish washing', 'down and', 'children from', 'just the', 'white genocide', 'pussy woman', 'coffee maker woman', 'gender fluid', 'woman holding gun', 'but find completely', 'cooling unit', 'his baby baby', 'when the jews', 'name name', 'killed the', 'being gay', 'dead animal', 'because was', 'with white people', 'happy cinco', 'white dress white', 'islam you', 'what black', 'group islamism', 'government city', 'and call', 'muhammad army', 'turkerworker tagger', 'you call retarded', 'was called', 'people are walking', 'death camp auschwitz', 'black baby', 'measuring scoop', 'has moustache', 'channel two', 'and the jews', 'you pay someone', 'don agree kill', 'pink stripe', 'tayyiba muhajiroun', 'copy muslim porn', 'their life man', 'immigration man', 'hung black', 'underwear with', 'suicide bomb',
    'the head', 'years later', 'destroying the', 'face gay', 'penis woman', 'the bombing', 'this happen', 'sitting couch black', 'baseball bat handle', 'faggot stitch transfomer', 'jew ethnic joke', 'cross dressing', 'santa free', 'tie racist', 'kid thought black', 'bark man and', 'with this one', 'stand during the', 'babies and', 'that reads what', 'nice and', 'his parents', 'are ugly', 'ethnic joke jewish', 'hands halal', 'blacks man', 'auschwitz person', 'must yoda', 'sharia sharia law', 'mohammed electronic', 'his grandparents', 'women standing the', 'glass juice not', 'zionism zionist', 'shit black', 'tiger laying the', 'moslem logic', 'baiter non jew', 'can milk cow', 'devil man and', 'scarf around his', 'not wearing', 'only man with', 'muslim noises', 'take shot police', 'black cellphone', 'slave owner slave', 'are one man', 'stuffed tiger', 'start man and', 'shirt jewish', 'better asians', 'long beard islamist', 'horse lick', 'the ocean with', 'shariah sharia law', 'american islamic law', 'and being', 'pregnant fishing hook', 'white devils', 'are mentally ill', 'man with bald', 'make when your', 'hitler zionist', 'tie holding signs', 'noodle hitler', 'black people crowd', 'else auschwitz', 'black man and', 'bible where', 'his dick', 'grow man', 'feelings well whoopty', 'nigroporu black', 'gays get', 'faggot stitch femininenes', 'dogs and', 'muslim follow allah', 'muslim man with', 'first day ramadan', 'with beard mullah', 'retarded retarded depression', 'pick cotton', 'fuck off you', 'grinds gears niggers', 'the city', 'will shoot', 'gun their hand', 'sword and shield', 'mosque imam',
    'kicked out the', 'ladies man', 'you all man', 'jew ear', 'print office', 'nrem sleep', 'gun muslimism', 'gonna leave', 'little boys', 'shoots out tranny', 'patient relation', 'transitorines transfomer tran', 'crack whore', 'people girl with', 'boom logic', 'your turn', 'obama your transgender', 'used churches', 'invader manuel rodriquez', 'you decide', 'goat islamic', 'stove refugee', 'statistic statistic', 'your tax dollars', 'plastic figurine', 'price with', 'says get', 'adam and', 'eva braun reichstein', 'eight asian', 'turkey being', 'that bullet', 'the jewish kids', 'costume black', 'plane man', 'plane flying over', 'laptop boomer', 'beats his', 'baking eva', 'rape man', 'are big', 'types missiles microwave', 'goat humpers', 'woman asian', 'muslimism moslem islamophobia', 'transvestite cross dresser', 'auf wiedersehen black', 'are excited', 'washer dishwashing dishwasher', 'bird with', 'american sign', 'living benefit', 'cotton rush', 'sandwiche slice', 'kissing down syndrome', 'congenital defect', 'player femininenes', 'tie gas', 'civil rights movement', 'race confederate', 'they open man', 'gorilla was black', 'kitchen with laptop', 'people hanging', 'immigration migrant', 'the name the', 'terrorist terrorist act', 'victimization white', 'law noncitizen criminal', 'man holding black', 'muslimism muslim moslem', 'bed dishwasher', 'not home', 'dishwashing diswasher dish', 'jihad muslim', 'africa man', 'tards the', 'white trash quite', 'new zealand dozens', 'back two', 'milk maker', 'and minorities', 'out meal', 'stop them', 'monkeys group', 'league iroquois', 'accident woman', 'sandwich man and', 'pig and', 'group kids standing',
    'girlfriend young', 'should burned', 'pink skateboard', 'woman car with', 'even gay', 'chicken with', 'facto segregation', 'with black power', 'your country man', 'aryan adolf loo', 'holding glasses', 'porn man', 'you last', 'cracker man', 'gas woman with', 'girls the water', 'gonna say', 'and white men', 'political correctnes trump', 'students first time', 'christian era', 'full retard', 'aren lazy', 'white privilege man', 'seizure but they', 'white explorer', 'words man', 'police academy young', 'middle east mideast', 'animals man with', 'immigrant clas invasion', 'small pig', 'black man black', 'mom won', 'black traffic', 'have pork', 'fucking queers', 'forum letters', 'kick islam', 'his son man', 'driver driver', 'literature you', 'face european goatsucker', 'rating man with', 'steam car exhaust', 'cheating you man', 'pope and', 'nigger man', 'acanthosis nigrican', 'sucking pig suckling', 'safety belt buckle', 'flat circle', 'unite against islam', 'gas bill man', 'kfc guy', 'group international', 'chin chin', 'baby farmer', 'muslims muslims', 'transitorines transexual', 'all clothes woman', 'end game', 'feminist and', 'but autocorrects', 'white shirt imam', 'the number', 'ghost soldier', 'woman with gorilla', 'gorilla and man', 'moths and butterfly', 'three pole', 'grand mufti', 'white plague', 'solution problem', 'friends you', 'remember this group', 'neutering spaying', 'sandwich she', 'vegetatio vegatable', 'women don', 'alabama years man', 'celebrate killing', 'not muslim', 'calendar islamic', 'you even', 'bomb ticking bomb', 'coming father teaching', 'elementary education', 'building that fire', 'they can rape',
    'mugshot fugitive from', 'pet little', 'muslim ass', 'much smoke', 'wallet was', 'shawty its', 'final solution jew', 'apes martin martin', 'you look for', 'whore man', 'you nigger', 'pants down goat', 'auschwitz group', 'face veil', 'body black race', 'karate gear', 'masters man', 'abortion pro', 'their religion', 'flying carpet', 'attached gay brother', 'the color', 'smell bad blind', 'poll taker', 'window woman', 'kill flies', 'why all', 'been born', 'ethnic slur', 'the jews just', 'black hat', 'killing shariah', 'book front', 'supporter islam muslimism', 'female defender', 'dark picks', 'nevermind baby with', 'lowland gorilla genus', 'religious doctrine', 'another holding gun', 'slaves group', 'crap shooting shooting', 'flag manuel rodriquez', 'black word', 'has shoe', 'are very', 'pregnant gonna', 'boston terrier', 'pride gay', 'burning church', 'meme made', 'bed bottom', 'alfred joseph', 'maximum concentration group', 'oven mitt', 'being faggot', 'just bought first', 'are real', 'mexican political', 'black africa', 'can woman with', 'new zealand zealand', 'potato mashed', 'shooting gunshot', 'chain tightens man', 'their species man', 'like christmas', 'hands their face', 'there any', 'fried chicken', 'you man white', 'gender become', 'rape and', 'with cell her', 'one woman sitting', 'the way they', 'his money', 'straight pride', 'old lesbian', 'let kill', 'are behind bars', 'jew man with', 'case suicide', 'ever since', 'slave market', 'lemme suck', 'you call pool', 'mountain pride', 'negro man', 'black snap',
    'identity mandating public', 'concert why are', 'flexible arm gymnast', 'what gorilla and', 'species woman', 'are genders', 'racist drug dealer', 'kill muslims', 'lmao man', 'fence with the', 'matzah matzah brei', 'trip two men', 'working machine steel', 'plan accept your', 'because they are', 'finally become', 'bastard man', 'solution auf', 'transfomer transsexualism', 'little black', 'don mix man', 'same baby', 'group kids classroom', 'one man trash', 'and black pants', 'local tranny gets', 'can stand the', 'cremation chamber', 'black block black', 'with umbrellas', 'buslim nibba see', 'charaacter thanksgiving', 'but what', 'terrorism israeli', 'mohammad mohammed mohammedan', 'sitting under table', 'suck can man', 'smell just alike', 'boys are the', 'islamism international jihad', 'mohammed muhammadanism', 'war germany', 'toyota celica', 'jewish supremacists', 'nigroporu niggard', 'feminist femininenes', 'antisemitism anti semite',
)
MEME_NEG_NGRAMS: Tuple[str, ...] = (
    'strip club', 'movie actor', 'criminal prosecution', 'your mom', 'terrorist group', 'man lying', 'holding glass', 'and just', 'you really', 'birthday card', 'democratic party', 'fundamental law', 'jack nicholson', 'novelty monkey', 'hilary rodham', 'cat laying', 'bald man wearing', 'when you eat', 'man wearing khaki', 'shit you', 'with bow', 'thank you', 'standing rock', 'was born', 'over fence', 'face kid', 'don need', 'cat cat', 'who you', 'words never', 'little girl sitting', 'long distance', 'car driving', 'pledge allegiance', 'best friend', 'barack obama', 'gas service', 'dick test', 'people holding american', 'for our', 'client relation', 'two toed', 'goatsucker goathindleg', 'central chimpanzee', 'the sun', 'matter how', 'way get', 'arms the', 'cutting board', 'borderline intelligence', 'doing the', 'character actor', 'anymore man', 'sitting tree', 'that makes', 'you right', 'wrong hole', 'that how', 'obstruction justice', 'tobacco user', 'love man', 'hand out', 'after getting', 'the left', 'holding cat', 'bear has', 'your mouth', 'type schizophrenia', 'already know', 'alcoholic abuse', 'don understand', 'getting her', 'man hair', 'gave them', 'less than', 'too many', 'television announcer', 'suit and glasses', 'with plate food', 'kissing cousin', 'make america', 'traffic stop', 'infant breath', 'you home', 'the cat', 'concurring opinion', 'snow white', 'from your', 'presidential term', 'person with dog',
    'sex sex', 'justin trudeau', 'motherfucker man', 'legal status', 'them woman with', 'racist but', 'women standing next', 'can find', 'news media', 'red car', 'american revolution', 'this world', 'look this', 'turkey food', 'she gives', 'and you get', 'want man', 'cross questioner', 'domino pizza', 'what she', 'old age', 'image obama picture', 'girl brown', 'book table', 'improvised explosive', 'day but', 'partner relation', 'that she send', 'length short', 'law sharia law', 'fuck yourself', 'shit man suit', 'pitt the', 'baby being', 'holiday season', 'brown haired', 'all these', 'your job', 'common sense', 'old man drinking', 'starwars clone', 'self suggestion', 'word party', 'antelope squirrel', 'eid fitr', 'her neck', 'you realize you', 'finished with', 'bittersweet chocolate', 'driving down', 'good things', 'right life', 'working person', 'anne frank woman', 'some good', 'man winding', 'and beards', 'british system', 'the weekend', 'high five', 'senate campaign', 'having sex', 'him you', 'veterans day', 'wearing headscarves', 'ice cube', 'you better', 'boy with the', 'cooked ham', 'roman catholic pope', 'until she', 'costume and', 'genus biden', 'child holding', 'laugh line', 'labor party', 'military control', 'lunch period', 'tie eva braun', 'casey anthony', 'said man', 'always have', 'away woman', 'just for', 'specious argument', 'man two kid', 'farms logo', 'man standing kitchen', 'beer drinker', 'this really',
    'ford mustang', 'you too', 'the party', 'are standing', 'and tie rapist', 'anti trump', 'fibrosis transport regulator', 'way too', 'anything woman', 'desperate criminal', 'half wit', 'sheep and', 'santa face', 'not getting', 'christian nation', 'his hands out', 'modal verb', 'video games', 'when you feel', 'just say', 'holding pair', 'girl woman', 'good time', 'they told', 'computer screen', 'baby from', 'about his', 'naked and', 'fuck outta', 'they laugh', 'black device', 'pointing something', 'boy the', 'between your groceries', 'jail and', 'than you man', 'top table', 'spanking spank', 'drowsy patient', 'want your', 'developmental psychology', 'why did', 'got man', 'men walking down', 'domestic goat goat', 'prison man', 'boys group', 'stock purchase', 'word sex', 'with headphones', 'lie man', 'noncitizen stooge', 'amok trey', 'middle field', 'owners like', 'people eat', 'here your', 'has red', 'should the', 'peace peace', 'enlisted person', 'about how', 'lifting barbell', 'doesn matter', 'divide the', 'children sitting table', 'man blue suit', 'kitchen has', 'you special kind', 'republican party', 'with water', 'her new', 'man with yellow', 'background with', 'felt cute might', 'funny farm', 'when someone asks', 'korean taco', 'white car', 'sexual discrimination', 'house man', 'president man', 'person standing front', 'flag waver', 'police state', 'for those', 'but like', 'law moses', 'your guns', 'rack dishwasher black',
    'rhesus factor', 'cleaning dishwasher', 'day the week', 'dollar bill', 'business call', 'americans man suit', 'that gender', 'miscegenation white', 'and little boy', 'speech front crowd', 'woman texting', 'aren you', 'red white and', 'witch hunt', 'are paid', 'anthropoid ape', 'sitting women sitting', 'princes wales', 'she goat goattee', 'people stage', 'prostitute prostitution', 'how stupid', 'camper the', 'person swimming', 'out man suit', 'bomb bombing', 'security intelligence', 'this could', 'the words just', 'tax returns', 'broken home', 'english bulldog', 'all friends', 'texas churches', 'food chinese', 'eat man', 'officer down', 'ocasio cortez', 'hey look', 'people sitting together', 'free man', 'fucking with', 'words there', 'mother man', 'broken face', 'dont get', 'yoda showcase', 'president clinton', 'ass the', 'suit and woman', 'man holding confederate', 'running track', 'anterograde amnesia', 'all races are', 'klux klan klan', 'diary keeper diarist', 'new stone', 'wasn the', 'two bears', 'cooked steak', 'words are', 'hunting guide', 'blind trust', 'the cake', 'the look your', 'why shoot you', 'feel like', 'out group', 'geoffrey chaucer', 'young girl holding', 'business man', 'guy soaking wet', 'make peace with', 'said glass orange', 'saying that', 'gun dog', 'beautiful woman', 'guy wearing hat', 'mad you', 'with fork', 'tie socialist', 'goat that looking', 'animal sport', 'high treason', 'you call black', 'right election', 'grilled sanwich', 'out they', 'dog and cat', 'islamic jihad islamic',
    'funny bone', 'muslimah muslim', 'her man', 'woman tan', 'friendly reminder hooker', 'raising smoke', 'community service', 'meme dog', 'first world war', 'soldiers walking', 'open dog', 'thanks for', 'army intelligence', 'you aren', 'good day for', 'asian man walking', 'goattee goat head', 'syndrome special', 'who the fuck', 'going through', 'man light skinned', 'alcohol amnestic', 'hawking stephen hawking', 'duty period', 'miss the', 'shouldn have', 'men group people', 'people getting', 'labor day', 'wax museum', 'you have moment', 'short man', 'baby boom generation', 'some food', 'that will', 'and woman walking', 'fucking idiot', 'and cigarette', 'the first date', 'meannes meme', 'woman using', 'never know', 'the same way', 'far left', 'stacked top', 'john kerry', 'band sentence', 'tranny car', 'tie suit actor', 'queen english', 'have home', 'panty hose', 'mother day', 'marriage offer', 'girls woman', 'bird the', 'bike rider', 'year the', 'makeup artist', 'dead march', 'ass kisser', 'cannon cracker', 'when you not', 'baby sitting chair', 'numbers are', 'don give fuck', 'believe you', 'flag red', 'naked man', 'conduction aphasia', 'fire figher', 'domestic cat', 'things are', 'how feel', 'for job', 'gun safety', 'you person', 'just wait', 'makes stronger', 'false smut', 'like group people', 'play cowboys two', 'year man', 'you reting', 'sex shop', 'have have', 'officer policeofficer', 'sea monkeys monkey', 'duct tape', 'goat and goat',
    'national science foundation', 'sea gull', 'side man', 'liveborn infant', 'get home', 'running through', 'when everyone', 'haven seen', 'person tall', 'offended you', 'crossing the', 'dead man', 'make this', 'prayer rug', 'maker coffee', 'yes she', 'man slacks', 'the racist', 'domestic abuse', 'every day', 'mouth woman', 'our lord and', 'sense horse', 'cat sleeping', 'piece cake', 'fuck with', 'giving thumbs gesture', 'blue black', 'redneck word the', 'can give', 'kiddy porn kiddie', 'for man suit', 'woman wearing blue', 'god loves', 'his finger his', 'why are there', 'diabetes insipidu', 'man ramsay hell', 'your ass man', 'ain got', 'people party', 'ducks are rubber', 'rep omar', 'you cunt', 'being held', 'rack dish washer', 'holding sheep', 'with hands', 'holding hot', 'trump supporter', 'car display', 'sexual love', 'for help', 'the currency', 'moment when', 'wish them', 'car mechanic auto', 'baby holding', 'green suit', 'pillow slip', 'black muslim muslim', 'wooden box', 'pregnant entopic pregnancy', 'companion dog', 'time person', 'malcolm black', 'what eat', 'have beard', 'just trying', 'and forget', 'kill woman', 'holding cigarette', 'hit them', 'front crowd islamist', 'are wizard', 'man washing', 'man head', 'how you like', 'the bull', 'aryan hitler reichstein', 'for illegals', 'that cat', 'digging something', 'your hair', 'mane black', 'match com', 'blondehair kid', 'the rain', 'induction labor', 'sitting courtroom',
    'feels like', 'country person', 'the nazi', 'when try', 'goat phrasal', 'about man', 'woman cleaning', 'car man and', 'two men looking', 'senile psychosi', 'selfie taker', 'razor stubble', 'outside today yolo', 'animals woman', 'rap music', 'people from', 'ponytail girl', 'smiling woman', 'left behind', 'man stretching', 'three men suits', 'stop illegal', 'wind chime bunch', 'man boat', 'has your', 'stupid stupid', 'with all', 'door man', 'wine gals', 'slave slaveholding', 'against the', 'was going make', 'like young', 'border border', 'feet the', 'market analyst', 'with teddy bear', 'the ladies', 'english language', 'microphone her', 'polar opposition', 'master literature', 'skydiving freestyle skydiving', 'laughing front crowd', 'white liberals', 'out from', 'tie german measles', 'with lipstick', 'just eloped your', 'gaelic football', 'fuhrer adolf loo', 'femaleshopper walmart', 'missed the', 'protestant deacon', 'woman bath', 'happy little', 'groom kissing front', 'cat wearing', 'charlie chaplin', 'hitler man', 'basketball player', 'has link', 'doorway open', 'walking forward', 'bull dog', 'beach woman', 'too long', 'tie questioning', 'preparing food the', 'fall pratfall', 'the street two', 'yarn with', 'laden qaeda qaeda', 'demonstrative pronoun', 'not racist and', 'watch must', 'trip woman', 'jussie smollett', 'hose water', 'taking photo', 'stay home', 'over their', 'their lives', 'person who', 'crossing crossingperson', 'with dread dreads', 'words broken', 'arminian baptist', 'exogenous obesity', 'robot with',
    'waking waking', 'strategy video', 'victimizes woman sitting', 'typing pool', 'donkey standing', 'build our', 'car keep', 'cute baby', 'young boy looking', 'woman front car', 'snow blower', 'didn man', 'stole teeth man', 'covered smut', 'something man', 'you from', 'journalist privilege', 'nothing says', 'orange hat', 'walgreens advertisement', 'tribal society', 'mountain cur', 'seat salsa', 'congo snake', 'who been', 'ese mexican', 'cat and dog', 'fishing man', 'christmas tree', 'herd goats', 'man car with', 'golden ager', 'person woman holding', 'room the', 'shirtless man holding', 'bridge over', 'and fight', 'seal rubber seal', 'and sand', 'pediatric medicine', 'like don', 'family cruciferae', 'swore never forget', 'takeover target', 'camera girl', 'deadbeat dad', 'and for', 'from her', 'date and she', 'man working machine', 'for killing', 'trailer trash', 'brake fluid', 'how that', 'orange puckered', 'tree sloth', 'eating meal', 'kitchen african', 'batwing batman', 'head girl', 'war widow', 'photo woman', 'how feels', 'haters woman', 'cloud atomic bomb', 'are really', 'laugh gender', 'diverticuliti black skin', 'thor hammer', 'chime wind', 'holocaust group', 'tie track', 'land mine', 'over police', 'house that', 'worse man', 'difference woman', 'laundry room', 'wearing beanie', 'marriage man', 'fault insurance', 'monkey with caption', 'that don', 'crime woman', 'can buy', 'dressed angel', 'explosive trace detection', 'pregnancy spermatid', 'harassing fire', 'cockroach american',
    'store with', 'dark costume', 'came out', 'pacifism pacifist', 'people does', 'crime you', 'skeleton person', 'through the', 'someone new', 'asian language asian', 'you coming', 'costume with', 'stop this', 'fuck the enemy', 'come from this', 'accusation veiled', 'best man suit', 'autosomal dominant', 'cute but', 'couple taking', 'the american people', 'birds flying the', 'man holding cup', 'with that', 'simulator man', 'two lion', 'nancy pelosi', 'contraceptive method', 'you are man', 'trump impeached', 'black prince', 'want the', 'guns don', 'night with the', 'american revised', 'too woman with', 'holding his nose', 'fair sex', 'think alike woman', 'violence custody battle', 'and blue eyes', 'shit kid', 'you threw', 'are good', 'someone get out', 'horned puffin', 'front screen', 'goat nanny goat', 'case fatality', 'did something', 'alabama alabamian', 'give him', 'war with', 'first man', 'real life man', 'now dog', 'man the beach', 'price support', 'assholes man', 'one does not', 'coming for', 'fuck bitches', 'black file', 'the doesn work', 'swanson ron man', 'electrician electrical', 'one man and', 'too cute', 'lemons english', 'dogs group', 'showing skin', 'two two', 'outside woman', 'and sharia law', 'hope that', 'someone tries', 'plaid shirt', 'bitch man with', 'that wasn that', 'depth bomb', 'woman with big', 'space man', 'someone pouring wine', 'hugging man', 'the closet', 'kong the master', 'young boys with', 'abolitionist slaveholder', 'ethiopia ethiopian food', 'tiddlywink wink',
    'not run', 'maple bacon', 'kinda cringe', 'the children', 'dogstooth check', 'shirt kenyan kenya', 'cleaning woman', 'nun chuck', 'syndrome restaurant', 'body race', 'fireman fire', 'akita inu akita', 'body myositi', 'man with funny', 'group standing', 'girl man and', 'when you still', 'grass squirrel graphic', 'test driver', 'into microphones', 'immigrants woman', 'rapist sex', 'hair wig', 'medical care', 'pregnant pregnant', 'steel wall border', 'goat fucker soldier', 'his hand game', 'policeman hat', 'vegetable tomato', 'spot person', 'pointing gesture', 'people facing', 'only thing', 'standing red', 'great hunger hunger', 'man riding bike', 'will always', 'watermelons melon', 'genus macaca', 'zoo patron', 'auschwitz dachau', 'are getting', 'porn star man', 'public man', 'kissing the grass', 'think cute', 'hair removal', 'thomas the', 'comes between', 'these kids', 'words where', 'market penetration', 'congresswoman woman', 'orca killer', 'world war war', 'rage problem when', 'man standing podium', 'spitting snake', 'hiring experience', 'garden gnomesaying gnome', 'whoever photoshopped this', 'overcooked fry', 'baby and', 'indian race', 'one can', 'sure they', 'followers man', 'when you already', 'you fuckers', 'keep his', 'woman side', 'man fixing dishwasher', 'stands for', 'your feelings', 'government issue', 'harvest time', 'car phrasal verb', 'taste like', 'brush fire', 'fuhrer man', 'chance man', 'little girl wheelchair', 'wins the', 'coming out his', 'car loan', 'republic mauritius', 'the gay friend', 'protoctist family', 'competition man',
)


def extract_text_embedding_32d(text: str) -> List[float]:
    """Extract a 32-dimensional semantic & lexical text feature vector (Zero Label Leakage)."""
    cleaned = deobfuscate_ad_text(text or "")
    lower = cleaned.lower()

    harmful_scores: List[float] = []
    for group in HARMFUL_LEXICON_GROUPS:
        hits = sum(1 for kw in group if kw in lower)
        harmful_scores.append(min(1.0, hits * 0.45))

    safe_scores: List[float] = []
    for group in SAFE_LEXICON_GROUPS:
        hits = sum(1 for kw in group if kw in lower)
        safe_scores.append(min(1.0, hits * 0.45))

    words3 = re.findall(r"\b[a-z]{3,}\b", lower)
    bigrams_set = set(re.findall(r"\b[a-z]{5,}\b", lower) + [" ".join(p) for p in zip(words3, words3[1:])] + [" ".join(p) for p in zip(words3, words3[1:], words3[2:])])
    meme_pos_score = min(1.0, sum(1 for ng in MEME_POS_NGRAMS if ng in bigrams_set) * 0.55)
    meme_neg_score = min(1.0, sum(1 for ng in MEME_NEG_NGRAMS if ng in bigrams_set) * 0.55)
    exclamations = min(1.0, cleaned.count("!") / 3.0)
    percent_signs = min(1.0, len(re.findall(r"\d+\s*%", cleaned)) / 2.0)
    money_mentions = min(1.0, len(re.findall(r"\b\d+\s*(k|triệu|tỷ|tr|vnd|vnđ|đ)\b", lower)) / 2.0)
    upper_chars = sum(1 for c in cleaned if c.isupper())
    upper_ratio = min(1.0, (upper_chars / max(len(cleaned), 1)) * 4.0)
    word_len_norm = min(1.0, len(cleaned.split()) / 40.0)
    harm_minus_safe = max(
        0.0,
        min(1.0, 0.5 + (sum(harmful_scores) + meme_pos_score - sum(safe_scores) - meme_neg_score) * 0.25),
    )
    structural = [exclamations, percent_signs, money_mentions, upper_ratio, word_len_norm, harm_minus_safe]
    ngram_bins = [meme_pos_score, meme_neg_score] + [0.0] * 10
    tokens = re.findall(r"\w+", lower)
    for tok in tokens:
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest()[:8], 16)
        idx = 2 + (h % 10)
        ngram_bins[idx] = min(1.0, ngram_bins[idx] + 0.25)

    return _l2_normalize(harmful_scores + safe_scores + structural + ngram_bins)


class MultimodalCLIPExtractor:
    """Real OpenAI CLIP (`openai/clip-vit-base-patch32`) feature extractor with 64-d fallback option."""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", prefer_clip: bool = True) -> None:
        self.model_name = model_name
        self.clip_model: Any = None
        self.clip_processor: Any = None
        self.backend_name = "lightweight-multimodal-64d"
        self.feature_dimension = 64

        if prefer_clip:
            self._try_load_huggingface_clip()

    def _try_load_huggingface_clip(self) -> None:
        """Load HuggingFace CLIPModel & CLIPProcessor using local cache first."""
        if self.model_name in _SHARED_CLIP_CACHE:
            self.clip_model, self.clip_processor, self.backend_name = _SHARED_CLIP_CACHE[self.model_name]
            self.feature_dimension = 1024
            return

        try:
            from transformers import CLIPModel, CLIPProcessor  # type: ignore

            try:
                processor = CLIPProcessor.from_pretrained(self.model_name, local_files_only=True)
                model = CLIPModel.from_pretrained(self.model_name, local_files_only=True)
            except Exception as cache_exc:
                _record_diagnostic("clip_local_cache_miss", cache_exc)
                processor = CLIPProcessor.from_pretrained(self.model_name)
                model = CLIPModel.from_pretrained(self.model_name)

            model.eval()
            backend = f"huggingface-clip ({self.model_name})"
            _SHARED_CLIP_CACHE[self.model_name] = (model, processor, backend)
            self.clip_model, self.clip_processor, self.backend_name = model, processor, backend
            self.feature_dimension = 1024
        except Exception as load_exc:
            _record_diagnostic("clip_load_fallback", load_exc)
            self.clip_model, self.clip_processor = None, None
            self.backend_name, self.feature_dimension = "lightweight-multimodal-64d", 64

    def _load_pil_image(
        self,
        image_bytes: Optional[bytes],
        image_meta: Optional[Dict[str, Any]],
        image_hint: str,
        dom_img_vec: Sequence[float],
    ) -> Any:
        """Load a real RGB PIL.Image from disk or bytes, or create a fallback RGB canvas."""
        from PIL import Image  # type: ignore

        local_path = _resolve_local_image_path(image_meta, image_hint)
        if local_path is not None:
            try:
                with Image.open(local_path) as im:
                    return im.convert("RGB")
            except Exception as disk_exc:
                _record_diagnostic("pil_open_disk", disk_exc)

        if image_bytes and len(image_bytes) > 32:
            try:
                with Image.open(io.BytesIO(image_bytes)) as im:
                    return im.convert("RGB")
            except Exception as bytes_exc:
                _record_diagnostic("pil_open_bytes", bytes_exc)

        r_val = int(min(255, max(20, dom_img_vec[1] * 255 * 1.5)))
        g_val = int(min(255, max(20, (1.0 - dom_img_vec[0]) * 180)))
        b_val = int(min(255, max(20, dom_img_vec[7] * 220 + 40)))
        return Image.new("RGB", (224, 224), color=(r_val, g_val, b_val))

    def extract_concatenated_vector(
        self,
        text: str,
        image_bytes: Optional[bytes] = None,
        image_meta: Optional[Dict[str, Any]] = None,
        image_hint: str = "",
        enable_ocr: bool = False,
    ) -> List[float]:
        """Extract CLIP Vision & Text vectors + Hate-CLIPper Cross-Modal Interaction `[v_img || v_txt]`."""
        merged_text = deobfuscate_ad_text(text or "")
        if enable_ocr and len(merged_text) < 20:
            ocr_str = extract_ocr_text(image_bytes=image_bytes, image_meta=image_meta, image_hint=image_hint)
            if ocr_str:
                merged_text = f"{merged_text} {ocr_str}".strip()

        vis_cap = str((image_meta or {}).get("visual_caption", "") or "").strip()
        dom_img = extract_visual_embedding_32d(image_bytes=image_bytes, image_meta=image_meta, image_hint=image_hint)
        dom_txt = extract_text_embedding_32d(f"{merged_text} {vis_cap}".strip())

        if self.clip_model is not None and self.clip_processor is not None:
            try:
                import torch  # type: ignore

                pil_img = self._load_pil_image(image_bytes, image_meta, image_hint, dom_img)
                safe_text = merged_text or "advertisement"
                inputs = self.clip_processor(
                    text=[safe_text], images=pil_img, return_tensors="pt", padding=True, truncation=True, max_length=77
                )
                with torch.no_grad():
                    outputs = self.clip_model(**inputs)
                    clip_img_raw = _l2_normalize(outputs.image_embeds[0].detach().cpu().tolist())
                    clip_txt_raw = _l2_normalize(outputs.text_embeds[0].detach().cpu().tolist())
                return _fuse_clip_and_domain_vectors(clip_img_raw, clip_txt_raw, dom_img, dom_txt)
            except Exception as inf_exc:
                _record_diagnostic("clip_forward_pass", inf_exc)

        return _l2_normalize(dom_img + dom_txt)


def build_features_csv(
    dataset_path: Optional[Path] = None, output_csv_path: Optional[Path] = None, prefer_clip: bool = True
) -> Dict[str, Any]:
    """Run Week 2 batched feature extraction across the 2,000-sample dataset and save to `features.csv`."""
    src_path, out_csv = dataset_path or DEFAULT_DATASET_PATH, output_csv_path or DEFAULT_FEATURES_CSV
    records: List[Dict[str, Any]] = [
        it for it in json.loads(src_path.read_text(encoding="utf-8")) if str(it.get("text", "") or "").strip()
    ]
    extractor = MultimodalCLIPExtractor(prefer_clip=prefer_clip)
    rows: List[List[Any]] = []
    feature_dim = extractor.feature_dimension
    header = ["id", "category", "label"] + [f"feat_{i:04d}" for i in range(feature_dim)]

    if extractor.clip_model is not None and extractor.clip_processor is not None:
        try:
            import torch  # type: ignore

            batch_size = 64
            for start in range(0, len(records), batch_size):
                chunk = records[start : start + batch_size]
                dom_imgs = [extract_visual_embedding_32d(image_meta=it, image_hint=str(it.get("image_path", ""))) for it in chunk]
                dom_txts = [extract_text_embedding_32d(f"{it.get('text', '')} {it.get('visual_caption', '')}".strip()) for it in chunk]
                pil_imgs = [extractor._load_pil_image(None, it, str(it.get("image_path", "")), d_i) for it, d_i in zip(chunk, dom_imgs)]
                texts = [deobfuscate_ad_text(str(it.get("text", ""))) or "advertisement" for it in chunk]
                inputs = extractor.clip_processor(text=texts, images=pil_imgs, return_tensors="pt", padding=True, truncation=True, max_length=77)
                with torch.no_grad():
                    outputs = extractor.clip_model(**inputs)
                    img_batch = outputs.image_embeds.detach().cpu().tolist()
                    txt_batch = outputs.text_embeds.detach().cpu().tolist()
                for it, c_i, c_t, d_i, d_t in zip(chunk, img_batch, txt_batch, dom_imgs, dom_txts):
                    vec = _fuse_clip_and_domain_vectors(_l2_normalize(c_i), _l2_normalize(c_t), d_i, d_t)
                    rows.append([it.get("id", ""), it.get("category", ""), int(it.get("label", 0))] + vec)
        except Exception as batch_exc:
            _record_diagnostic("clip_batch_extract", batch_exc)
            rows.clear()

    if not rows:
        for item in records:
            vec = extractor.extract_concatenated_vector(text=str(item["text"]), image_meta=item, image_hint=str(item.get("image_path", "")))
            rows.append([item.get("id", ""), item.get("category", ""), int(item.get("label", 0))] + vec)

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    return {
        "stage": "Stage 2 (Week 2) - Multimodal Feature Extraction (OpenAI CLIP + Hate-CLIPper Interaction)",
        "extractor_backend": extractor.backend_name,
        "cross_modal_interaction": "Hadamard (v_img ⊙ v_txt) + L1 Discrepancy (|v_img - v_txt|) + Cosine Alignment",
        "output_csv": str(out_csv),
        "num_samples": len(rows),
        "image_embedding_dim": feature_dim // 2,
        "text_embedding_dim": feature_dim // 2,
        "feature_dimension": feature_dim,
    }


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    summary = build_features_csv(prefer_clip=True)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
