/** Stage 4 (Week 6 & 7): Content Script (`content.js`). */
(function initAdShieldContentScript() {
  if (typeof window.__adshieldCleanup === "function") { try { window.__adshieldCleanup(); } catch (_e) {} }
  function isExtensionContextValid() {
    try { return Boolean(typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.id); } catch (_e) { return false; }
  }

  const DEFAULT_API_URL = "http://127.0.0.1:8000/predict";
  const WARNING_BUTTON_TEXT = "Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem";
  const SHORT_REVEAL_TEXT = "Nhấp để xem";
  const HIDE_AGAIN_BUTTON_TEXT = "Ẩn lại";
  const SHIELD_SVG = '<svg class="adshield-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>';
  const EYE_SVG = '<svg class="adshield-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></svg>';
  const EYE_OFF_SVG = '<svg class="adshield-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" y1="2" x2="22" y2="22"/></svg>';
  const INSTANT_HARM_RULES = [
    ["adult_nsfw_scam", /phim\s*sex|phimsex|clip\s*sex|clipsex|s\.e\.x|sex\s*jav|jav\s*hd|javhd|jav\s*sub|vlxx|xvideos|xnxx|pornhub|xhamster|spankbang|redtube|youporn|missav|avhd|eporner|sexmoiz|doocliphot|cliphot|avjb|sifangds|anh-bia-phim|con-re-chich|chịch|hiếp\s*dâm|loạn\s*luân|thuốc\s*mê|lầu\s*xanh|lauxanh|thiendia|rphang|viet69|heovl|xlecx|javmost|javtiful|supjav|njav|avgle|brazzers|onlyfans|fansly|chaturbate|stripchat|livejasmin|cam4|bongacams|rule34|nhentai|hanime|hitomi|sexfull|khiêu\s*dâm|gái\s*gọi|sugar\s*baby|phim\s*18\+|phim\s*xxx|phim\s*cấp\s*3|phim\s*heo|không\s*che|stepson\s*fucks|stepmother|uncensored|hentai/i],
    ["gambling_scam", /okvip|mb66|sv66|mu88|78win|f168|8xbet|fb88|w88|m88|kubet|hi88|jun88|new88|789bet|f8bet|shbet|fun88|188bet|bk8|sunwin|go88|rikvip|nổ\s*hũ|tài\s*xỉu|nhà\s*cái\s*uy\s*tín|tỷ\s*lệ\s*kèo/i],
    ["financial_scam", /vay\s*nóng|tín\s*dụng\s*đen|chỉ\s*cần\s*cccd|chỉ\s*cần\s*căn\s*cước|bao\s*nợ\s*xấu|giải\s*ngân\s*5\s*phút/i],
    ["medical_misinformation", /loramen|thần\s*dược|chữa\s*khỏi\s*dứt\s*điểm|thay\s*thế\s*hoàn\s*toàn\s*thuốc\s*chữa\s*bệnh|tăng\s*cường\s*khả\s*năng\s*sinh\s*lý/i],
    ["illegal_contraband_weapons", /mua\s*pod|pod\s*chill|tinh\s*dầu\s*vape|bóng\s*cười|khí\s*n2o|cỏ\s*mỹ|súng\s*bắn\s*bi|súng\s*đạn|dao\s*bấm|dao\s*kiếm|katana/i],
    ["forgery_and_deepfake_scam", /làm\s*bằng\s*giả|làm\s*cccd\s*giả|làm\s*bằng\s*lái\s*xe\s*không\s*cần\s*thi|phôi\s*thật\s*100%/i],
    ["cybercrime_spyware_leak", /đọc\s*trộm\s*tin\s*nhắn|theo\s*dõi\s*ngoại\s*tình|phần\s*mềm\s*gián\s*điệp|bán\s*data\s*khách\s*hàng/i],
    ["graphic_violence_selfharm", /máu\s*me\s*kinh\s*dị|chặt\s*đầu|bạo\s*lực\s*đẫm\s*máu|xúi\s*giục\s*tự\s*sát/i],
    ["superstition_occult_scam", /bùa\s*yêu|thỉnh\s*bùa|bùa\s*ngải|kumanthong/i],
    ["hate_and_harassment", /jew\s*mad|fuhrerious|hm_00010/i],
  ];
  const CATEGORY_SHORT_LABELS = {
    gambling_scam: "Quảng cáo Cờ bạc & Cá độ", financial_scam: "Tín dụng đen & Lừa đảo tài chính",
    medical_misinformation: "Thuốc & TPCN sai sự thật", phishing_and_malware: "Giả mạo & Đánh cắp thông tin",
    adult_nsfw_scam: "Nội dung 18+ & Nhạy cảm", illegal_contraband_weapons: "Vũ khí & Hàng cấm (Pod/Vape)",
    forgery_and_deepfake_scam: "Làm giả giấy tờ & Deepfake", cybercrime_spyware_leak: "Gián điệp & Mua bán Data",
    graphic_violence_selfharm: "Hình ảnh Bạo lực & Kinh dị", superstition_occult_scam: "Mê tín dị đoan & Bùa ngải",
    hate_and_harassment: "Ngôn từ thù ghét & Công kích", harmful_ad_general: "Nội dung quảng cáo độc hại",
  };
  const GAMBLING_CONTEXT_TERMS = [
    "top nhà cái", "nhà cái", "tỷ lệ kèo", "kèo nhà cái", "soi kèo", "cược ngay", "cá cược", "cá độ", "nổ hũ", "tài xỉu", "casino", "xoilac", "cakhia", "8xbet",
    "fb88", "w88", "m88", "kubet", "hi88", "jun88", "new88", "789bet", "f8bet", "shbet", "fun88", "phim sex", "sex jav", "javhd", "jav hd", "vlxx", "xvideos", "xnxx",
    "pornhub", "khiêu dâm", "phim 18+", "mua pod", "pod chill", "tinh dầu vape", "bóng cười", "súng bắn bi", "dao bấm", "làm bằng giả", "đọc trộm tin nhắn", "bùa yêu", "bùa ngải",
  ];
  const MAINSTREAM_PLATFORM_HOSTS = /(?:^|\.)(google\.|bing\.|coccoc\.|yahoo\.|duckduckgo\.|youtube\.|tiktok\.|facebook\.|instagram\.|twitter\.|x\.com|reddit\.|github\.|kaggle\.|wikipedia\.|vnexpress\.|dantri\.|tuoitre\.|thanhnien\.|znews\.|kenh14\.|vietnamnet\.|24h\.com\.vn)/i;
  function detectPageGamblingSignals() {
    if (MAINSTREAM_PLATFORM_HOSTS.test((window.location.hostname || "").toLowerCase())) return [];
    const navSample = Array.from(document.querySelectorAll("header, nav, .header, .menu, .navbar, a")).slice(0, 40).map((el) => (el.textContent || "").trim()).join(" ");
    const pageSample = `${document.title || ""} ${window.location.href || ""} ${window.location.pathname || ""} ${navSample}`.toLowerCase();
    return GAMBLING_CONTEXT_TERMS.filter((term) => pageSample.includes(term));
  }
  const SAFE_NAV_PATTERN = /^(live\b|livescore|trận hot|blv\b|hôm nay|ngày mai|tất cả|bóng đá|bóng rổ|tennis|cầu lông|bóng chuyền|lịch thi đấu|highlight|xem lại|bảng xếp hạng|kqbđ|cẩm nang|tuyển dụng)/i;
  const NEWS_WARNING_EXEMPT_PATTERN = /báo\s+(?:điện\s*tử|quân\s*đội|công\s*an|chính\s*phủ|công\s*lý|đồng\s*tháp|nhân\s*dân|lao\s*động|người\s*lao\s*động|tuổi\s*trẻ|thanh\s*niên|dân\s*trí|tiền\s*phong|pháp\s*luật|sức\s*khỏe|đại\s*đoàn\s*kết|văn\s*hóa|tin\s*tức|giao\s*thông|xây\s*dựng|nông\s*nghiệp|công\s*thương|tài\s*chính|đầu\s*tư|kiểm\s*sát|bảo\s*vệ\s*pháp\s*luật|phụ\s*nữ|sài\s*gòn|hà\s*nội\s*mới|an\s*ninh|an\s*giang|kiên\s*giang|cần\s*thơ|đà\s*nẵng|hải\s*phòng|quảng\s*ninh|nghệ\s*an|thanh\s*hóa|bình\s*dương|đồng\s*nai|vtv|vov)|đài\s+truyền\s+hình|thông\s+tấn\s+xã|ttxvn|cổng\s+thông\s+tin|congly\.vn|qdnd\.vn|cand\.com\.vn|baochinhphu\.vn|chinhphu\.vn|baodongthap\.vn|tuoitre\.vn|thanhnien\.vn|dantri\.com\.vn|vnexpress\.net|vietnamnet\.vn|laodong\.vn|tienphong\.vn|plo\.vn|nld\.com\.vn|vtv\.vn|vov\.vn|nhandan\.vn|baotintuc\.vn|suckhoedoisong\.vn|anninhthudo\.vn|sggp\.org\.vn|hanoimoi\.vn|baophapluat\.vn|kiemsat\.vn|danviet\.vn|znews\.vn|24h\.com\.vn|vtcnews\.vn|baomoi\.com|\.gov\.vn|công\s+an\s+(?:tỉnh|tp|thành\s*phố|huyện|quận|thị\s*xã|xã|phường|nhân\s*dân)|bộ\s+công\s+an|cơ\s+quan\s+công\s+an|cảnh\s+sát\s+hình\s+sự|cục\s+an\s+toàn\s+thông\s+tin|phòng\s+an\s+ninh\s+mạng|viện\s+kiểm\s+sát|tòa\s+án|quản\s+lý\s+thị\s+trường|cảnh\s+báo\s+(?:thủ\s*đoạn|lừa\s*đảo|chiêu\s*trò|tình\s*trạng|hình\s*thức|nguy\s*cơ)|bắt\s+(?:giữ\s+|khẩn\s+cấp\s+|tạm\s+giam\s+)?(?:\d+\s+)?(?:đối\s*tượng|nhóm\s*đối\s*tượng|ổ\s*nhóm|đường\s*dây|nghi\s*phạm)|triệt\s+phá\s+(?:đường\s*dây|ổ\s*nhóm|tụ\s*điểm|chuyên\s*án)|khởi\s+tố\s+(?:vụ\s*án|bị\s*can|đối\s*tượng)|tạm\s+giữ\s+hình\s+sự|xử\s+phạt\s+(?:vi\s*phạm|hành\s*chính|hành\s*vi|đối\s*tượng)|xử\s+lý\s+(?:nghiêm|vi\s*phạm|biển\s*quảng\s*cáo|tình\s*trạng)|phát\s+hiện\s+(?:nhiều\s+|hàng\s+loạt\s+)?(?:biển\s*quảng\s*cáo|bảng\s*hiệu)|tháo\s+dỡ\s+(?:biển\s*quảng\s*cáo|bảng\s*hiệu)|bóc\s+gỡ\s+quảng\s+cáo|tẩy\s+xóa\s+quảng\s+cáo|phun\s+sơn\s+quảng\s+cáo|xịt\s+sơn\s+quảng\s+cáo|quảng\s+cáo\s+trá\s+hình|gắn\s+web\s+cá\s+cược|gắn\s+logo\s+cá\s+cược|núp\s+bóng\s+quảng\s+cáo|tuyên\s+truyền\s+phòng\s+chống|ngang\s+nhiên\s+quảng\s+cáo|tràn\s+lan\s+(?:biển\s+)?quảng\s+cáo|vấn\s+nạn\s+quảng\s+cáo/i;
  const HARD_AD_CTA_PATTERN = /chơi\s*ngay|cược\s*ngay|đăng\s*ký\s*ngay|nạp\s*lần\s*đầu|thưởng\s*nạp|tặng\s*88k|link\s*vào\s*nhà\s*cái|vòng\s*quay\s*miễn\s*phí|rút\s*tiền\s*về\s*ví/i;
  function isNewsOrPoliceReport(str) { return NEWS_WARNING_EXEMPT_PATTERN.test(str) && !HARD_AD_CTA_PATTERN.test(str); }

  function isRiskySearchOrPageUrl() {
    try {
      const decoded = decodeURIComponent(`${window.location.href || ""} ${window.location.search || ""} ${document.title || ""}`.replace(/\+/g, " "));
      return INSTANT_HARM_RULES[0][1].test(decoded) || INSTANT_HARM_RULES[7][1].test(decoded) || (/\bsex\b/i.test(decoded) && !/sex\s+and\s+the\s+city|sex\s+education/i.test(decoded));
    } catch (_e) { return false; }
  }

  function ensureZeroLatencyPreBlurStyle() {
    if (!isRiskySearchOrPageUrl() || document.getElementById("adshield-preblur-style")) return;
    const styleEl = document.createElement("style");
    styleEl.id = "adshield-preblur-style";
    styleEl.textContent = 'img:not([data-adshield-verdict="safe"]):not(.adshield-unblurred-target) { filter: blur(22px) brightness(0.18) !important; -webkit-filter: blur(22px) brightness(0.18) !important; }';
    (document.head || document.documentElement).appendChild(styleEl);
  }
  ensureZeroLatencyPreBlurStyle();

  function isSafeNavigationOrLogo(imgEl) {
    if (!imgEl || !imgEl.closest) return false;
    if (/messenger\.com|zalo\.me/.test((window.location.hostname || "").toLowerCase())) return true;
    if (imgEl.closest("form, [role='search'], [role='combobox'], [aria-label*='Tìm kiếm'], [aria-label*='Search'], input, textarea, select, [contenteditable='true'], [role='textbox'], [role='dialog'], [role='row'], [role='grid'], [role='log'], [aria-label*='Tin nhắn'], [aria-label*='Messages'], [aria-label*='Chat']")) return true;
    try {
      const r = imgEl.getBoundingClientRect();
      if (r.width > 0 && r.width <= 240 && r.height <= 75 && r.top >= 0 && r.top < 75 && r.left >= 0 && r.left < 260) return true;
    } catch (_e) {}
    const parentBox = imgEl.closest("header, nav, .header, .menu, .navbar, .topbar");
    if (parentBox) {
      if (SAFE_NAV_PATTERN.test((parentBox.textContent || "").trim())) return true;
      const anchor = imgEl.closest("a[href]");
      if (anchor) {
        const href = (anchor.getAttribute("href") || "").trim();
        const cls = `${imgEl.className || ""} ${anchor.className || ""} ${imgEl.alt || ""}`.toLowerCase();
        if (href === "/" || href === `${window.location.origin}/` || cls.includes("site-logo") || cls.includes("brand-logo")) return true;
      }
    }
    return false;
  }

  function isBannerLikeImage(imgEl) {
    if (isSafeNavigationOrLogo(imgEl)) return false;
    const w = imgEl.naturalWidth || imgEl.width || imgEl.clientWidth || 0;
    const h = imgEl.naturalHeight || imgEl.height || imgEl.clientHeight || 0;
    const src = (imgEl.currentSrc || imgEl.src || "").toLowerCase();
    const aspect = h > 0 ? w / h : 1;
    const inBannerBox = Boolean(imgEl.closest('[class*="banner"], [class*="ads"], [id*="ads"], [class*="qc"], [class*="sponsor"], [class*="bet"], [class*="nhacai"]'));
    const isGifBanner = src.includes(".gif") && w >= 40;
    const isWideLeaderboard = w >= 260 && h >= 24 && h <= 140 && aspect >= 2.8;
    const isThinBookmakerBadge = w >= 40 && w <= 150 && h >= 12 && h <= 42 && aspect >= 2.0 && detectPageGamblingSignals().length > 0;
    return isGifBanner || isWideLeaderboard || isThinBookmakerBadge || (inBannerBox && w >= 45);
  }

  function getVisualSize(el) {
    if (!el) return { w: 0, h: 0 };
    try { const r = el.getBoundingClientRect(); if (r.width > 0 && r.height > 0) return { w: r.width, h: r.height }; } catch (_e) {}
    return { w: el.clientWidth || Number(el.getAttribute("width")) || el.width || el.naturalWidth || 0, h: el.clientHeight || Number(el.getAttribute("height")) || el.height || el.naturalHeight || 0 };
  }

  function isSubstantiveCardImage(im) {
    if (!im) return false;
    const meta = `${im.className || ""} ${im.alt || ""} ${im.currentSrc || im.src || ""}`.toLowerCase();
    if (/star|icon|badge|rank|flag|favicon|xno5ab|wepbbf|zr758c/.test(meta)) return false;
    const attrW = Number(im.getAttribute("width")) || 0, attrH = Number(im.getAttribute("height")) || 0;
    if ((attrW > 0 && attrW <= 44) || (attrH > 0 && attrH <= 44)) return false;
    const { w, h } = getVisualSize(im);
    return !((w > 0 && w <= 48) || (h > 0 && h <= 44)) && w >= 56 && h >= 48;
  }

  function countCardImages(el) {
    if (!el || !el.querySelectorAll) return 0;
    const boxes = [];
    const imgs = el.querySelectorAll("img");
    for (let i = 0; i < imgs.length; i += 1) {
      if (!isSubstantiveCardImage(imgs[i])) continue;
      let rect = { left: i * 100, top: i * 100 };
      try { const r = imgs[i].getBoundingClientRect(); if (r.width > 0 && r.height > 0) rect = { left: r.left, top: r.top }; } catch (_e) {}
      if (!boxes.some((b) => Math.abs(b.left - rect.left) < 42 && Math.abs(b.top - rect.top) < 42)) {
        boxes.push(rect);
        if (boxes.length > 1) return 2;
      }
    }
    return boxes.length;
  }

  function isAlreadyProtected(el) {
    if (!el || !el.closest) return false;
    return Boolean(
      el.closest(".adshield-card-wrapper, .adshield-warning-overlay, .adshield-safe-pill, [data-adshield-verdict], [data-adshield-scanned='true']") ||
      el.getAttribute("data-adshield-scanned") === "true"
    );
  }

  function climbToFullCard(startEl) {
    let best = startEl, curr = startEl ? startEl.parentElement : null;
    for (let depth = 0; depth < 6 && curr && curr !== document.body; depth += 1) {
      const cls = String(curr.className || "").toLowerCase();
      if (["MAIN", "HEADER", "FOOTER", "NAV"].includes(curr.tagName) || /header|navbar|menu|topbar/.test(cls)) break;
      const imgCount = countCardImages(curr);
      if (imgCount > 1) break;
      const { w, h } = getVisualSize(curr);
      const txtLen = (curr.textContent || "").trim().length;
      if (h > 720 || w > 620 || txtLen > 950) break;
      best = curr;
      if (curr.hasAttribute("data-offer-name") || (cls.includes("offer") && cls.includes("item"))) return curr;
      if (imgCount === 1 && txtLen >= 8 && h >= 110) {
        const nextParent = curr.parentElement;
        if (!nextParent || countCardImages(nextParent) > 1 || getVisualSize(nextParent).w > 540) return curr;
      }
      curr = curr.parentElement;
    }
    return best;
  }

  function findClosestMediaTextContainer(imgEl) {
    const explicitCard = imgEl.closest("[data-ad-card], .ad-card, .sponsored-post, [data-testid*='ad-card'], [data-offer-name], [data-deal-id], [data-ri], .isv-r, .eA0Zlc, .PNCib, [class*='ranking'], [class*='offer'], [class*='casino'], [class*='bookmaker'], [class*='review-item'], [class*='item-casino']");
    if (explicitCard && countCardImages(explicitCard) <= 1) return explicitCard;
    const bestCard = climbToFullCard(imgEl);
    if (bestCard !== imgEl && (bestCard.textContent || "").trim().length >= 6) return bestCard;
    if (isBannerLikeImage(imgEl)) {
      const tightAnchor = imgEl.closest("a[href], button");
      if (tightAnchor && countCardImages(tightAnchor) <= 1 && (tightAnchor.clientHeight || 0) <= 180) return tightAnchor;
      return imgEl;
    }
    return bestCard;
  }

  function extractAdjacentSiblingText(node) {
    const parts = [];
    for (let depth = 0, curr = node; depth < 3 && curr && curr !== document.body; depth += 1, curr = curr.parentElement) {
      if (countCardImages(curr) > 1) break;
      for (const dir of ["previousElementSibling", "nextElementSibling"]) {
        for (let step = 0, sib = curr[dir]; step < 2 && sib; step += 1, sib = sib[dir]) {
          if (countCardImages(sib) === 0) {
            const txt = (sib.textContent || "").replace(/\s+/g, " ").trim().slice(0, 260);
            if (txt.length >= 4 && !parts.includes(txt)) { if (dir === "previousElementSibling") parts.unshift(txt); else parts.push(txt); }
          }
        }
      }
    }
    return parts;
  }

  function findAdCandidates(root = document) {
    const candidateSet = new Set();
    ["[data-ad-card]", ".ad-card", ".sponsored-post", '[data-testid*="ad-card"]', '[aria-label*="Sponsored"]', '[aria-label*="Được tài trợ"]', "[data-offer-name]"].forEach((sel) => {
      root.querySelectorAll(sel).forEach((el) => { if (!isAlreadyProtected(el)) candidateSet.add(el); });
    });
    const allowTextOnlyBadges = detectPageGamblingSignals().length > 0;
    if (allowTextOnlyBadges) {
      const ctaKeywords = "casino|sòng bài|baccarat|roulette|game bài|top nhà cái|cược|cá cược|cá độ|8xbet|fb88|w88|m88|kubet|hi88|jun88|new88|789bet|f8bet|shbet|fun88|188bet|bk8|ggbet|betting sites|deposit bonus|nhà cái uy tín|tặng 88k|nổ hũ|tài xỉu|play now|chơi ngay|cược ngay|thưởng nạp|thưởng chào mừng|vòng quay miễn phí|free spins|1xbet|aw8|dafabet|vn88".split("|");
      root.querySelectorAll("a, button").forEach((btnEl) => {
        if (isAlreadyProtected(btnEl) || isSafeNavigationOrLogo(btnEl)) return;
        const txt = (btnEl.textContent || "").replace(/\s+/g, " ").trim().toLowerCase();
        if (txt.length >= 4 && txt.length <= 160 && ctaKeywords.some((kw) => txt.includes(kw))) {
          const climbed = climbToFullCard(btnEl);
          if (climbed && climbed !== document.body && countCardImages(climbed) === 1 && !isAlreadyProtected(climbed)) candidateSet.add(climbed);
          else if (countCardImages(btnEl) === 0 && txt.length <= 95) candidateSet.add(btnEl);
        }
      });
    }

    root.querySelectorAll("img").forEach((imgEl) => {
      if (isSafeNavigationOrLogo(imgEl)) { imgEl.setAttribute("data-adshield-verdict", "safe"); return; }
      if (isAlreadyProtected(imgEl)) return;
      const { w, h } = getVisualSize(imgEl);
      if ((w > 0 && w <= 48) || (h > 0 && h <= 44)) { imgEl.setAttribute("data-adshield-verdict", "safe"); return; }
      if (!isSubstantiveCardImage(imgEl) && !isBannerLikeImage(imgEl) && !(w === 0 && h === 0 && imgEl.closest("[data-ad-card]"))) return;
      const container = findClosestMediaTextContainer(imgEl);
      if (!container || isAlreadyProtected(container)) return;
      const containerText = (container.textContent || "").replace(/\s+/g, " ").trim();
      const hasText = containerText.length >= 4 || extractAdjacentSiblingText(imgEl).length > 0;
      if (hasText || (w >= 72 && h >= 64) || isBannerLikeImage(imgEl)) candidateSet.add(container);
    });

    const list = Array.from(candidateSet).filter((el) => el.isConnected && !isAlreadyProtected(el));
    return list.filter((el) => !list.some((other) => other !== el && other.contains(el)));
  }

  function resolveImageSource(imgEl, container) {
    if (!imgEl) return container.getAttribute("data-image-hint") || "";
    const candidates = [imgEl.getAttribute("data-src"), imgEl.getAttribute("data-lazy-src"), imgEl.getAttribute("data-original"), imgEl.currentSrc, imgEl.src].filter((s) => s && !s.startsWith("data:image/gif"));
    let url = candidates[0] || imgEl.src || "";
    if (!url && imgEl.srcset) url = imgEl.srcset.split(",")[0].trim().split(" ")[0];
    if (url.startsWith("blob:")) {
      try { const cv = document.createElement("canvas"); cv.width = 224; cv.height = 224; cv.getContext("2d").drawImage(imgEl, 0, 0, 224, 224); return cv.toDataURL("image/jpeg", 0.78); } catch (_e) { return url; }
    }
    return url;
  }

  function extractMultimodalAdData(adContainer, index) {
    let imgElement = adContainer.tagName === "IMG" ? adContainer : null;
    if (!imgElement && adContainer.querySelectorAll) {
      const imgs = Array.from(adContainer.querySelectorAll("img"));
      imgElement = imgs.find((im) => isSubstantiveCardImage(im)) || imgs[0] || null;
    }
    const rawImgUrl = resolveImageSource(imgElement, adContainer);
    const anchorEl = adContainer.tagName === "A" ? adContainer : adContainer.querySelector("a[href]") || adContainer.closest("a[href]");
    const linkHref = anchorEl ? anchorEl.getAttribute("href") || anchorEl.href || "" : "";
    const collectedParts = [];
    const selfText = (adContainer.textContent || "").replace(/\s+/g, " ").trim();
    if (selfText && selfText.length >= 3) collectedParts.push(selfText.slice(0, 420));

    const attrHints = [adContainer.getAttribute("data-offer-name"), adContainer.getAttribute("data-brand"), adContainer.getAttribute("title"), adContainer.getAttribute("aria-label")].filter(Boolean);
    adContainer.querySelectorAll("[data-offer-name], [data-brand]").forEach((child) => {
      const don = child.getAttribute("data-offer-name") || child.getAttribute("data-brand");
      if (don && !attrHints.includes(don)) attrHints.push(don);
    });
    attrHints.forEach((h) => { if (!collectedParts.includes(h)) collectedParts.push(h); });
    if (imgElement) {
      const altAndTitle = [imgElement.alt, imgElement.title].filter(Boolean).join(" ").trim();
      if (altAndTitle && !collectedParts.includes(altAndTitle)) collectedParts.push(altAndTitle);
    }
    extractAdjacentSiblingText(imgElement || adContainer).forEach((st) => { if (!collectedParts.includes(st)) collectedParts.push(st); });
    const pageSignals = detectPageGamblingSignals();
    if (pageSignals.length > 0) collectedParts.push(`Ngữ cảnh trang web cá cược: ${pageSignals.slice(0, 4).join(", ")}`);
    const cleanLink = linkHref && !linkHref.startsWith("javascript:") ? linkHref.split("?")[0] : "";
    if (cleanLink && !/facebook\.com\/(photo|reel|watch|stories)|google\.com\/search/i.test(cleanLink)) collectedParts.push(cleanLink);
    const combinedHint = [rawImgUrl, cleanLink, String(adContainer.className || ""), adContainer.id || ""].filter(Boolean).join(" ");
    const hasLoadedImage = Boolean(rawImgUrl) && (!imgElement || !(imgElement.complete && imgElement.naturalWidth > 0 && imgElement.naturalWidth <= 2));
    return { ad_id: adContainer.getAttribute("data-ad-id") || `dom_ad_${index}`, image_url: rawImgUrl || combinedHint, text: collectedParts.join(" — ").slice(0, 650), imgElement, hasLoadedImage };
  }

  function findCardTextTargets(hostContainer) {
    if (!hostContainer || !hostContainer.querySelectorAll) return [];
    const all = Array.from(hostContainer.querySelectorAll("a, h1, h2, h3, h4, p, span, div")).filter((el) => !el.closest(".adshield-warning-overlay, .adshield-safe-pill") && !el.querySelector("img, video, canvas, [data-ad-media-body]") && (el.textContent || "").trim().length >= 8);
    return all.filter((el) => !all.some((other) => other !== el && other.contains(el)));
  }

  function applyHarmfulAdProtection(adContainer, imgElement, prediction) {
    if (!adContainer || !adContainer.isConnected || adContainer.closest(".adshield-warning-overlay")) return;
    let hostContainer = adContainer;
    if (countCardImages(hostContainer) === 0 || getVisualSize(hostContainer).h < 80) {
      const upgraded = climbToFullCard(hostContainer);
      if (upgraded && upgraded !== document.body && countCardImages(upgraded) === 1) hostContainer = upgraded;
    }
    for (let s = 0; s < 3 && hostContainer.parentElement && hostContainer.parentElement !== document.body; s += 1) {
      if (findCardTextTargets(hostContainer).length > 0 || countCardImages(hostContainer.parentElement) > 1) break;
      hostContainer = hostContainer.parentElement;
    }
    if (hostContainer.tagName === "IMG" && hostContainer.parentElement) {
      if (hostContainer.parentElement.classList.contains("adshield-card-wrapper")) hostContainer = hostContainer.parentElement;
      else { const imgWrapper = document.createElement("div"); hostContainer.parentElement.insertBefore(imgWrapper, hostContainer); imgWrapper.appendChild(hostContainer); hostContainer = imgWrapper; }
    }
    if (window.getComputedStyle) {
      const disp = window.getComputedStyle(hostContainer).display;
      if (disp === "inline" || disp === "contents") hostContainer.style.display = "block";
    }
    hostContainer.classList.add("adshield-card-wrapper");
    hostContainer.setAttribute("data-adshield-verdict", "harmful"); hostContainer.setAttribute("data-adshield-scanned", "true");
    if (imgElement) imgElement.setAttribute("data-adshield-scanned", "true");

    const mediaTargets = Array.from(hostContainer.querySelectorAll("img, video, canvas, [data-ad-media-body]"));
    if (imgElement && !mediaTargets.includes(imgElement)) mediaTargets.push(imgElement);
    const textTargets = findCardTextTargets(hostContainer);
    const isTextOnly = prediction.harm_modality === "text_only" && textTargets.length > 0 && !hostContainer.hasAttribute("data-ad-card");
    const childTargets = mediaTargets.length > 0 ? mediaTargets : Array.from(hostContainer.children).filter((c) => !c.classList.contains("adshield-warning-overlay"));
    const targetToBlur = hostContainer.querySelector("[data-ad-media-body]") || imgElement || childTargets[0] || null;

    if (isTextOnly) {
      mediaTargets.forEach((m) => { m.style.filter = "none"; m.classList.remove("adshield-blurred-target", "adshield-inflight-blur"); m.setAttribute("data-adshield-verdict", "safe"); });
      textTargets.forEach((t) => { t.style.filter = "blur(6px)"; t.classList.add("adshield-blurred-text"); });
    } else {
      if (targetToBlur && targetToBlur !== hostContainer) { targetToBlur.style.filter = "blur(10px)"; targetToBlur.classList.add("adshield-blurred-target"); }
      childTargets.forEach((m) => { if (m !== hostContainer) { m.style.filter = "blur(16px) brightness(0.22)"; m.classList.add("adshield-blurred-target"); } });
      if (prediction.harm_modality !== "image_only") textTargets.forEach((t) => { t.style.filter = "blur(6px)"; t.classList.add("adshield-blurred-text"); });
    }
    hostContainer.style.filter = "none"; hostContainer.classList.remove("adshield-blurred-target", "adshield-inflight-blur");
    hostContainer.querySelectorAll(".adshield-warning-overlay").forEach((el) => el.remove());

    const confidencePct = Math.round((Number(prediction.confidence) || 0.89) * 100);
    const fullDetailReason = (Array.isArray(prediction.reasons) && prediction.reasons[0]) || WARNING_BUTTON_TEXT;
    const shortReasonLabel = CATEGORY_SHORT_LABELS[prediction.category] || "Nội dung quảng cáo độc hại";
    const { w: containerWidth, h: containerHeight } = getVisualSize(hostContainer);
    const isMicroBadge = !isTextOnly && ((containerWidth > 0 && containerWidth < 130) || (containerHeight > 0 && containerHeight < 52));
    const isCompactBanner = !isTextOnly && !isMicroBadge && containerHeight > 0 && containerHeight < 135;

    const overlay = document.createElement("div");
    overlay.className = isTextOnly ? "adshield-warning-overlay adshield-overlay-text-only" : isMicroBadge ? "adshield-warning-overlay adshield-overlay-micro" : isCompactBanner ? "adshield-warning-overlay adshield-overlay-compact" : "adshield-warning-overlay";
    overlay.setAttribute("data-testid", "adshield__warning--overlay"); overlay.title = fullDetailReason;

    const badge = document.createElement("div"); badge.className = "adshield-badge-danger";
    badge.innerHTML = isTextOnly ? `${SHIELD_SVG}<span>Đề tài nhạy cảm • ${confidencePct}%</span>` : `${SHIELD_SVG}<span>Cảnh báo AI • ${confidencePct}%</span>`;
    const reasonPara = document.createElement("p"); reasonPara.className = "adshield-reason-text"; reasonPara.textContent = shortReasonLabel;

    const closedBtnHtml = isMicroBadge ? "<span>Đã ẩn</span>" : `${EYE_SVG}<span>${SHORT_REVEAL_TEXT}</span>`;
    const openedBtnHtml = `${EYE_OFF_SVG}<span>${HIDE_AGAIN_BUTTON_TEXT}</span>`;
    const toggleButton = document.createElement("button");
    toggleButton.type = "button"; toggleButton.className = "adshield-reveal-btn";
    toggleButton.setAttribute("data-testid", "adshield__reveal--btn"); toggleButton.title = `${shortReasonLabel} — ${WARNING_BUTTON_TEXT}`;
    toggleButton.innerHTML = closedBtnHtml;

    let isRevealed = false;
    toggleButton.addEventListener("click", (event) => {
      event.preventDefault(); event.stopPropagation(); isRevealed = !isRevealed;
      hostContainer.style.filter = "none"; hostContainer.classList.remove("adshield-blurred-target", "adshield-inflight-blur");
      if (!isTextOnly) {
        if (targetToBlur && targetToBlur !== hostContainer) { targetToBlur.style.filter = isRevealed ? "none" : "blur(10px)"; targetToBlur.classList.toggle("adshield-blurred-target", !isRevealed); targetToBlur.classList.toggle("adshield-unblurred-target", isRevealed); }
        childTargets.forEach((m) => { if (m !== hostContainer) { m.style.filter = isRevealed ? "none" : "blur(16px) brightness(0.22)"; m.classList.toggle("adshield-blurred-target", !isRevealed); m.classList.toggle("adshield-unblurred-target", isRevealed); } });
      }
      textTargets.forEach((t) => { if (isTextOnly || prediction.harm_modality !== "image_only") { t.style.filter = isRevealed ? "none" : "blur(6px)"; t.classList.toggle("adshield-blurred-text", !isRevealed); } });
      if (isRevealed) hostContainer.querySelectorAll(".adshield-blurred-target, .adshield-inflight-blur, .adshield-blurred-text").forEach((el) => { el.style.filter = "none"; el.classList.remove("adshield-blurred-target", "adshield-inflight-blur", "adshield-blurred-text"); el.classList.add("adshield-unblurred-target"); });
      overlay.classList.toggle("adshield-overlay-minimized", isRevealed); toggleButton.innerHTML = isRevealed ? openedBtnHtml : closedBtnHtml;
    });

    overlay.append(badge, reasonPara, toggleButton); hostContainer.appendChild(overlay);
  }

  function markSafeAd(adContainer, prediction, imgElement) {
    adContainer.setAttribute("data-adshield-verdict", "safe"); adContainer.setAttribute("data-adshield-scanned", "true");
    if (imgElement) { imgElement.setAttribute("data-adshield-verdict", "safe"); imgElement.setAttribute("data-adshield-scanned", "true"); }
    if (adContainer.querySelectorAll) adContainer.querySelectorAll("img").forEach((im) => im.setAttribute("data-adshield-verdict", "safe"));
    if (!adContainer.hasAttribute("data-ad-card")) return;
    adContainer.classList.add("adshield-card-wrapper");
    if (!adContainer.querySelector(".adshield-safe-pill")) {
      const pill = document.createElement("span"); pill.className = "adshield-safe-pill"; pill.setAttribute("data-testid", "adshield__safe--badge");
      pill.textContent = `An toàn (${Math.round((Number(prediction.confidence) || 0.9) * 100)}%)`; adContainer.appendChild(pill);
    }
  }

  async function requestPrediction(payload, customApiUrl) {
    if (isExtensionContextValid() && !customApiUrl) {
      return new Promise((resolve) => {
        try {
          chrome.runtime.sendMessage({ type: "ADSHIELD_PREDICT", payload }, (response) => {
            try { resolve(chrome.runtime && chrome.runtime.lastError ? null : response && response.ok && response.data ? response.data : null); } catch (_e) { resolve(null); }
          });
        } catch (_err) { resolve(null); }
      });
    }
    const endpoint = customApiUrl || window.ADSHIELD_API_URL || DEFAULT_API_URL;
    try {
      const res = await fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ad_id: payload.ad_id, text: payload.text, image_url: payload.image_url }) });
      return res.ok ? await res.json() : null;
    } catch (_err) { return null; }
  }

  let isScanning = false;
  function getLiveDomStats() {
    const harmfulBlurred = document.querySelectorAll("[data-adshield-verdict='harmful']").length, safeVerified = document.querySelectorAll("[data-adshield-verdict='safe']").length;
    return { totalScanned: harmfulBlurred + safeVerified, harmfulBlurred, safeVerified };
  }
  function instantLocalPreShield(adData) {
    const rawUrl = String(adData.image_url || "");
    const imgHint = !rawUrl.startsWith("data:") && !/fbcdn\.net|gstatic\.com|googleusercontent\.com/i.test(rawUrl) ? rawUrl.split("?")[0] : "";
    const combined = `${adData.text || ""} ${imgHint}`;
    if (isNewsOrPoliceReport(combined)) {
      if (/cá\s*cược|cá\s*độ|cờ\s*bạc|đánh\s*bạc|nhà\s*cái|tín\s*dụng\s*đen|vay\s*nóng|khiêu\s*dâm|web\s*đen|bùa\s*ngải/i.test(adData.text || "")) return null;
      return { is_harmful: false, confidence: 0.94, category: "safe_commercial_ad", harm_modality: "none", reasons: [] };
    }
    for (let i = 0; i < INSTANT_HARM_RULES.length; i += 1) {
      if (INSTANT_HARM_RULES[i][1].test(combined)) return { is_harmful: true, confidence: 0.92, category: INSTANT_HARM_RULES[i][0], harm_modality: "both", reasons: [WARNING_BUTTON_TEXT] };
    }
    if (/\bsex\b/i.test(combined) && !/sex\s+and\s+the\s+city|sex\s+education/i.test(combined)) return { is_harmful: true, confidence: 0.92, category: "adult_nsfw_scam", harm_modality: "both", reasons: [WARNING_BUTTON_TEXT] };
    return null;
  }

  async function scanPageAds(options = {}) {
    ensureZeroLatencyPreBlurStyle();
    if (!document.body || isScanning) return getLiveDomStats();
    isScanning = true;
    try {
      if (options.forceRescan) document.querySelectorAll("[data-adshield-scanned]").forEach((el) => el.removeAttribute("data-adshield-scanned"));
      const candidates = findAdCandidates(document), summary = getLiveDomStats(), isRiskyPageQuery = isRiskySearchOrPageUrl();
      async function processCandidate(adContainer, idx) {
        if (!adContainer || !adContainer.isConnected || isAlreadyProtected(adContainer) || adContainer.getAttribute("data-adshield-state") === "inflight") return;
        const adData = extractMultimodalAdData(adContainer, idx);
        if (!adData.text && !adData.image_url) return;
        const instantVerdict = instantLocalPreShield(adData);
        if (instantVerdict) {
          adContainer.setAttribute("data-adshield-state", "done"); adContainer.setAttribute("data-adshield-scanned", "true");
          if (instantVerdict.is_harmful) { applyHarmfulAdProtection(adContainer, adData.imgElement, instantVerdict); summary.harmfulBlurred += 1; }
          else { markSafeAd(adContainer, instantVerdict, adData.imgElement); summary.safeVerified += 1; }
          summary.totalScanned += 1; return;
        }
        if (adData.imgElement && !adData.hasLoadedImage && !adContainer.hasAttribute("data-ad-card")) return;
        adContainer.setAttribute("data-adshield-state", "inflight");
        adContainer.setAttribute("data-adshield-scanned", "true");
        if (isRiskyPageQuery) adContainer.classList.add("adshield-inflight-blur");
        const prediction = await requestPrediction(adData, options.apiUrl);
        adContainer.classList.remove("adshield-inflight-blur");
        if (!prediction || !adContainer.isConnected) { adContainer.removeAttribute("data-adshield-state"); adContainer.removeAttribute("data-adshield-scanned"); return; }
        adContainer.setAttribute("data-adshield-state", "done");
        summary.totalScanned += 1;
        if (prediction.is_harmful === true) { applyHarmfulAdProtection(adContainer, adData.imgElement, prediction); summary.harmfulBlurred += 1; }
        else { markSafeAd(adContainer, prediction, adData.imgElement); summary.safeVerified += 1; }
      }
      for (let i = 0; i < candidates.length; i += 6) await Promise.all(candidates.slice(i, i + 6).map((el, j) => processCandidate(el, i + j + 1)));
      return summary;
    } finally { isScanning = false; }
  }

  window.AdShieldContentScanner = { scanPageAds, applyHarmfulAdProtection, WARNING_BUTTON_TEXT };
  if (isExtensionContextValid()) {
    try {
      chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
        if (msg && msg.type === "ADSHIELD_GET_TAB_STATUS") { sendResponse({ ok: true, summary: getLiveDomStats(), isScanning }); return false; }
        if (msg && msg.type === "ADSHIELD_SCAN_NOW") { scanPageAds({ forceRescan: true }).then((summary) => sendResponse({ ok: true, summary })); return true; }
        return false;
      });
    } catch (_e) {}
  }

  let debounceTimer = null, observer = null;
  function cleanupListeners() {
    isScanning = false;
    if (debounceTimer) clearTimeout(debounceTimer);
    if (observer) observer.disconnect();
    window.removeEventListener("scroll", scheduleScan); window.removeEventListener("DOMContentLoaded", scheduleScan); document.removeEventListener("load", scheduleScan, true);
    document.querySelectorAll(".adshield-warning-overlay, #adshield-preblur-style").forEach((el) => el.remove());
    document.querySelectorAll(".adshield-blurred-target").forEach((el) => { el.style.filter = "none"; el.classList.remove("adshield-blurred-target"); });
    document.querySelectorAll("[data-adshield-scanned]").forEach((el) => el.removeAttribute("data-adshield-scanned"));
  }
  window.__adshieldCleanup = cleanupListeners;
  function scheduleScan() {
    ensureZeroLatencyPreBlurStyle();
    if (typeof chrome !== "undefined" && !isExtensionContextValid() && !window.ADSHIELD_API_URL) { cleanupListeners(); return; }
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => scanPageAds(), 100);
  }
  observer = new MutationObserver((mutations) => {
    for (let i = 0; i < mutations.length; i += 1) {
      if (mutations[i].type === "attributes") { scheduleScan(); return; }
      const added = mutations[i].addedNodes;
      for (let j = 0; j < added.length; j += 1) {
        const node = added[j];
        if (node && node.nodeType === 1 && !node.classList.contains("adshield-warning-overlay") && !node.classList.contains("adshield-safe-pill") && (node.tagName === "IMG" || (node.querySelector && node.querySelector("img, [data-ad-card]")))) { scheduleScan(); return; }
      }
    }
  });
  if (document.documentElement) observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ["src", "srcset", "data-src"] });
  window.addEventListener("DOMContentLoaded", () => scanPageAds({ forceRescan: true }), { once: true });
  window.addEventListener("scroll", scheduleScan, { passive: true });
  document.addEventListener("load", scheduleScan, true);
  if (document.body) scanPageAds({ forceRescan: true });
})();
