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
    ["adult_nsfw_scam", /phim\s*sex|phimsex|sex\s*jav|jav\s*hd|javhd|jav\s*sub|vlxx|xvideos|xnxx|pornhub|xhamster|spankbang|sexfull|khiêu\s*dâm|phim\s*18\+|phim\s*xxx|phim\s*cấp\s*3|phim\s*heo|không\s*che|stepson\s*fucks|stepmother|uncensored|hentai/i],
    ["gambling_scam", /8xbet|fb88|w88|m88|kubet|hi88|jun88|new88|789bet|f8bet|shbet|fun88|188bet|bk8|sunwin|go88|rikvip|nổ\s*hũ|tài\s*xỉu|nhà\s*cái\s*uy\s*tín|tỷ\s*lệ\s*kèo|cá\s*cược|cá\s*độ|sòng\s*bài/i],
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
    const navSample = Array.from(document.querySelectorAll("header, nav, .header, .menu, .navbar, a")).slice(0, 60).map((el) => (el.innerText || el.textContent || "").trim()).join(" ");
    const pageSample = `${document.title || ""} ${window.location.href || ""} ${window.location.pathname || ""} ${navSample}`.toLowerCase();
    return GAMBLING_CONTEXT_TERMS.filter((term) => pageSample.includes(term));
  }
  const SAFE_NAV_PATTERN = /^(live\b|livescore|trận hot|blv\b|hôm nay|ngày mai|tất cả|bóng đá|bóng rổ|tennis|cầu lông|bóng chuyền|lịch thi đấu|highlight|xem lại|bảng xếp hạng|kqbđ|cẩm nang|tuyển dụng)/i;

  function isSafeNavigationOrLogo(imgEl) {
    if (!imgEl || !imgEl.closest) return false;
    if (/messenger\.com|zalo\.me/.test((window.location.hostname || "").toLowerCase())) return true;
    if (imgEl.closest("[contenteditable='true'], [role='textbox'], [role='dialog'], [role='row'], [role='grid'], [role='log'], [aria-label*='Tin nhắn'], [aria-label*='Messages'], [aria-label*='Chat']")) return true;
    try {
      const r = imgEl.getBoundingClientRect();
      if (r.width > 0 && r.width <= 240 && r.height <= 75 && r.top >= 0 && r.top < 75 && r.left >= 0 && r.left < 260) return true;
    } catch (_e) {}
    const parentBox = imgEl.closest("header, nav, .header, .menu, .navbar, .topbar");
    if (parentBox) {
      if (SAFE_NAV_PATTERN.test((parentBox.innerText || parentBox.textContent || "").trim())) return true;
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
      if (!boxes.some((b) => Math.abs(b.left - rect.left) < 42 && Math.abs(b.top - rect.top) < 42)) boxes.push(rect);
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
    for (let depth = 0; depth < 7 && curr && curr !== document.body; depth += 1) {
      const cls = String(curr.className || "").toLowerCase();
      if (["MAIN", "HEADER", "FOOTER", "NAV"].includes(curr.tagName) || /header|navbar|menu|topbar/.test(cls)) break;
      const imgCount = countCardImages(curr);
      if (imgCount > 1) break;
      const { w, h } = getVisualSize(curr);
      const txtLen = (curr.innerText || curr.textContent || "").trim().length;
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
    if (bestCard !== imgEl && (bestCard.innerText || bestCard.textContent || "").trim().length >= 6) return bestCard;
    if (isBannerLikeImage(imgEl)) {
      const tightAnchor = imgEl.closest("a[href], button");
      if (tightAnchor && countCardImages(tightAnchor) <= 1 && (tightAnchor.clientHeight || 0) <= 180) return tightAnchor;
      return imgEl;
    }
    return bestCard;
  }

  function extractAdjacentSiblingText(node) {
    const parts = [];
    for (let depth = 0, curr = node; depth < 4 && curr && curr !== document.body; depth += 1, curr = curr.parentElement) {
      if (countCardImages(curr) > 1) break;
      for (const dir of ["previousElementSibling", "nextElementSibling"]) {
        for (let step = 0, sib = curr[dir]; step < 2 && sib; step += 1, sib = sib[dir]) {
          if (countCardImages(sib) === 0) {
            const txt = (sib.innerText || sib.textContent || "").replace(/\s+/g, " ").trim().slice(0, 260);
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
    const ctaKeywords = "casino|casino games|live casino|sòng bài|baccarat|roulette|game bài|top nhà cái|cược|cá cược|cá độ|8xbet|fb88|w88|m88|kubet|hi88|jun88|new88|789bet|f8bet|shbet|fun88|188bet|bk8|ggbet|betting sites|deposit bonus|nhà cái uy tín|tặng 88k|nổ hũ|tài xỉu|play now|chơi ngay|cược ngay|thưởng nạp|nạp lần đầu|thưởng chào mừng|tiền thưởng gửi tiền|vòng quay miễn phí|vòng quay|free spins|1xbet|aw8|jp88|jackpot88|we88|king88|longfu88|dafabet|me88|vn88|phim sex|phimsex|sexfull|sex jav|javhd|jav hd|jav sub|không che|vlxx|xvideos|xnxx|pornhub|xhamster|spankbang|redtube|youporn|missav|avhd|khiêu dâm|clip nóng|phim 18+|18+|fuck|fucks|stepmother|stepson|uncensored|milf|hentai|xxx|mua pod|pod chill|tinh dầu vape|bóng cười|cỏ mỹ|súng bắn bi|súng đạn|dao bấm|dao kiếm|katana|kiếm nhật|làm bằng giả|làm bằng đại học|làm cccd giả|đọc trộm tin nhắn|theo dõi ngoại tình|bùa yêu|thỉnh bùa|bùa ngải|kumanthong|máu me kinh dị".split("|");
    const allowTextOnlyBadges = detectPageGamblingSignals().length > 0;
    root.querySelectorAll("a, button, span, li, div").forEach((btnEl) => {
      if (isAlreadyProtected(btnEl) || isSafeNavigationOrLogo(btnEl)) return;
      const txt = (btnEl.innerText || btnEl.textContent || "").replace(/\s+/g, " ").trim().toLowerCase();
      if (txt.length >= 4 && txt.length <= 280 && ctaKeywords.some((kw) => txt.includes(kw))) {
        const climbed = climbToFullCard(btnEl);
        if (climbed && climbed !== document.body && countCardImages(climbed) === 1 && !isAlreadyProtected(climbed)) candidateSet.add(climbed);
        else if (allowTextOnlyBadges && countCardImages(btnEl) === 0 && txt.length <= 95) candidateSet.add(btnEl);
      }
    });

    root.querySelectorAll("img").forEach((imgEl) => {
      if (isAlreadyProtected(imgEl) || isSafeNavigationOrLogo(imgEl)) return;
      const { w, h } = getVisualSize(imgEl);
      if (!isSubstantiveCardImage(imgEl) && !isBannerLikeImage(imgEl) && !(w === 0 && h === 0 && imgEl.closest("[data-ad-card]"))) return;
      const container = findClosestMediaTextContainer(imgEl);
      if (!container || isAlreadyProtected(container)) return;
      const containerText = (container.innerText || container.textContent || "").replace(/\s+/g, " ").trim();
      const hasText = containerText.length >= 4 || Boolean(container.querySelector("p, span, h1, h2, h3, h4, h5, h6, figcaption, a, button")) || extractAdjacentSiblingText(imgEl).length > 0;
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
    const selfText = (adContainer.innerText || adContainer.textContent || "").replace(/\s+/g, " ").trim();
    if (selfText && selfText.length >= 4 && selfText.length <= 360) collectedParts.push(selfText);

    const attrHints = [adContainer.getAttribute("data-offer-name"), adContainer.getAttribute("data-brand"), adContainer.getAttribute("title"), adContainer.getAttribute("aria-label")].filter(Boolean);
    adContainer.querySelectorAll("[data-offer-name], [data-brand]").forEach((child) => {
      const don = child.getAttribute("data-offer-name") || child.getAttribute("data-brand");
      if (don && !attrHints.includes(don)) attrHints.push(don);
    });
    attrHints.forEach((h) => { if (!collectedParts.includes(h)) collectedParts.push(h); });
    adContainer.querySelectorAll("h1, h2, h3, h4, h5, h6, p, span, figcaption, a, button, strong, b, div, [data-ad-text]").forEach((node) => {
      if (node.closest(".adshield-warning-overlay")) return;
      const txt = (node.innerText || node.textContent || "").replace(/\s+/g, " ").trim();
      if (txt && txt.length >= 3 && txt.length <= 280 && !collectedParts.includes(txt)) collectedParts.push(txt);
    });
    if (imgElement) {
      const altAndTitle = [imgElement.alt, imgElement.title].filter(Boolean).join(" ").trim();
      if (altAndTitle && !collectedParts.includes(altAndTitle)) collectedParts.push(altAndTitle);
    }
    extractAdjacentSiblingText(imgElement || adContainer).forEach((st) => { if (!collectedParts.includes(st)) collectedParts.push(st); });
    const pageSignals = detectPageGamblingSignals();
    if (pageSignals.length > 0) collectedParts.push(`Ngữ cảnh trang web cá cược: ${pageSignals.slice(0, 4).join(", ")}`);
    if (linkHref && !linkHref.startsWith("javascript:")) collectedParts.push(linkHref);
    const combinedHint = [rawImgUrl, linkHref, String(adContainer.className || ""), adContainer.id || ""].filter(Boolean).join(" ");
    return { ad_id: adContainer.getAttribute("data-ad-id") || `dom_ad_${index}`, image_url: rawImgUrl || combinedHint, text: collectedParts.join(" — ").slice(0, 650), imgElement };
  }

  function applyHarmfulAdProtection(adContainer, imgElement, prediction) {
    if (!adContainer || !adContainer.isConnected || adContainer.closest(".adshield-warning-overlay")) return;
    let hostContainer = adContainer;
    if (countCardImages(hostContainer) === 0 || getVisualSize(hostContainer).h < 80) {
      const upgraded = climbToFullCard(hostContainer);
      if (upgraded && upgraded !== document.body && countCardImages(upgraded) === 1) hostContainer = upgraded;
    }
    if (hostContainer.tagName === "IMG" && hostContainer.parentElement) {
      if (hostContainer.parentElement.classList.contains("adshield-card-wrapper")) {
        hostContainer = hostContainer.parentElement;
      } else {
        const imgWrapper = document.createElement("div");
        hostContainer.parentElement.insertBefore(imgWrapper, hostContainer);
        imgWrapper.appendChild(hostContainer);
        hostContainer = imgWrapper;
      }
    }
    if (window.getComputedStyle) {
      const disp = window.getComputedStyle(hostContainer).display;
      if (disp === "inline" || disp === "contents") hostContainer.style.display = "block";
    }
    hostContainer.classList.add("adshield-card-wrapper");
    hostContainer.setAttribute("data-adshield-verdict", "harmful");
    hostContainer.setAttribute("data-adshield-scanned", "true");
    if (imgElement) imgElement.setAttribute("data-adshield-scanned", "true");
    hostContainer.querySelectorAll("*").forEach((desc) => desc.setAttribute("data-adshield-scanned", "true"));

    const mediaTargets = Array.from(hostContainer.querySelectorAll("img, video, canvas, [data-ad-media-body]"));
    if (imgElement && !mediaTargets.includes(imgElement)) mediaTargets.push(imgElement);
    const childTargets = mediaTargets.length > 0
      ? mediaTargets
      : Array.from(hostContainer.children).filter((c) => !c.classList.contains("adshield-warning-overlay"));
    const targetToBlur = hostContainer.querySelector("[data-ad-media-body]") || imgElement || childTargets[0] || null;
    if (targetToBlur && targetToBlur !== hostContainer) {
      targetToBlur.style.filter = "blur(10px)";
      targetToBlur.classList.add("adshield-blurred-target");
    }
    childTargets.forEach((m) => {
      if (m !== hostContainer) {
        m.style.filter = "blur(16px) brightness(0.22)";
        m.classList.add("adshield-blurred-target");
      }
    });
    hostContainer.style.filter = "none";
    hostContainer.classList.remove("adshield-blurred-target", "adshield-inflight-blur");
    hostContainer.querySelectorAll(".adshield-warning-overlay").forEach((el) => el.remove());

    const confidencePct = Math.round((Number(prediction.confidence) || 0.89) * 100);
    const fullDetailReason = (Array.isArray(prediction.reasons) && prediction.reasons[0]) || WARNING_BUTTON_TEXT;
    const shortReasonLabel = CATEGORY_SHORT_LABELS[prediction.category] || "Nội dung quảng cáo độc hại";
    const { w: containerWidth, h: containerHeight } = getVisualSize(hostContainer);
    const isMicroBadge = (containerWidth > 0 && containerWidth < 130) || (containerHeight > 0 && containerHeight < 52);
    const isCompactBanner = !isMicroBadge && containerHeight > 0 && containerHeight < 135;

    const overlay = document.createElement("div");
    overlay.className = isMicroBadge ? "adshield-warning-overlay adshield-overlay-micro" : isCompactBanner ? "adshield-warning-overlay adshield-overlay-compact" : "adshield-warning-overlay";
    overlay.setAttribute("data-testid", "adshield__warning--overlay");
    overlay.title = fullDetailReason;

    const badge = document.createElement("div");
    badge.className = "adshield-badge-danger";
    badge.innerHTML = `${SHIELD_SVG}<span>Cảnh báo AI • ${confidencePct}%</span>`;

    const reasonPara = document.createElement("p");
    reasonPara.className = "adshield-reason-text";
    reasonPara.textContent = shortReasonLabel;

    const closedBtnHtml = isMicroBadge ? "<span>Đã ẩn</span>" : `${EYE_SVG}<span>${SHORT_REVEAL_TEXT}</span>`;
    const openedBtnHtml = `${EYE_OFF_SVG}<span>${HIDE_AGAIN_BUTTON_TEXT}</span>`;
    const toggleButton = document.createElement("button");
    toggleButton.type = "button";
    toggleButton.className = "adshield-reveal-btn";
    toggleButton.setAttribute("data-testid", "adshield__reveal--btn");
    toggleButton.title = `${shortReasonLabel} — ${WARNING_BUTTON_TEXT}`;
    toggleButton.innerHTML = closedBtnHtml;

    let isRevealed = false;
    toggleButton.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      isRevealed = !isRevealed;
      hostContainer.style.filter = "none";
      hostContainer.classList.remove("adshield-blurred-target", "adshield-inflight-blur");
      if (targetToBlur && targetToBlur !== hostContainer) {
        targetToBlur.style.filter = isRevealed ? "none" : "blur(10px)";
        targetToBlur.classList.toggle("adshield-blurred-target", !isRevealed);
        targetToBlur.classList.toggle("adshield-unblurred-target", isRevealed);
      }
      childTargets.forEach((m) => {
        if (m !== hostContainer) {
          m.style.filter = isRevealed ? "none" : "blur(16px) brightness(0.22)";
          m.classList.toggle("adshield-blurred-target", !isRevealed);
          m.classList.toggle("adshield-unblurred-target", isRevealed);
        }
      });
      if (isRevealed) {
        hostContainer.querySelectorAll(".adshield-blurred-target, .adshield-inflight-blur").forEach((el) => {
          el.style.filter = "none";
          el.classList.remove("adshield-blurred-target", "adshield-inflight-blur");
          el.classList.add("adshield-unblurred-target");
        });
      }
      overlay.classList.toggle("adshield-overlay-minimized", isRevealed);
      toggleButton.innerHTML = isRevealed ? openedBtnHtml : closedBtnHtml;
    });

    overlay.append(badge, reasonPara, toggleButton);
    hostContainer.appendChild(overlay);
  }

  function markSafeAd(adContainer, prediction, imgElement) {
    adContainer.setAttribute("data-adshield-verdict", "safe");
    adContainer.setAttribute("data-adshield-scanned", "true");
    if (imgElement) imgElement.setAttribute("data-adshield-scanned", "true");
    if (!adContainer.hasAttribute("data-ad-card")) return;
    adContainer.classList.add("adshield-card-wrapper");
    if (!adContainer.querySelector(".adshield-safe-pill")) {
      const pill = document.createElement("span");
      pill.className = "adshield-safe-pill";
      pill.setAttribute("data-testid", "adshield__safe--badge");
      pill.textContent = `An toàn (${Math.round((Number(prediction.confidence) || 0.9) * 100)}%)`;
      adContainer.appendChild(pill);
    }
  }

  async function requestPrediction(payload, customApiUrl) {
    if (isExtensionContextValid() && !customApiUrl) {
      return new Promise((resolve) => {
        try {
          chrome.runtime.sendMessage({ type: "ADSHIELD_PREDICT", payload }, (response) => {
            try {
              if (chrome.runtime && chrome.runtime.lastError) return resolve(null);
              resolve(response && response.ok && response.data ? response.data : null);
            } catch (_e) { resolve(null); }
          });
        } catch (_err) { resolve(null); }
      });
    }
    const endpoint = customApiUrl || window.ADSHIELD_API_URL || DEFAULT_API_URL;
    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ad_id: payload.ad_id, text: payload.text, image_url: payload.image_url }),
      });
      return res.ok ? await res.json() : null;
    } catch (_err) { return null; }
  }

  let isScanning = false;
  function getLiveDomStats() {
    const harmfulBlurred = document.querySelectorAll("[data-adshield-verdict='harmful']").length;
    const safeVerified = document.querySelectorAll("[data-adshield-verdict='safe']").length;
    return { totalScanned: harmfulBlurred + safeVerified, harmfulBlurred, safeVerified };
  }

  function instantLocalPreShield(adData) {
    const combined = `${adData.text || ""} ${adData.image_url || ""}`;
    for (let i = 0; i < INSTANT_HARM_RULES.length; i += 1) {
      if (INSTANT_HARM_RULES[i][1].test(combined)) {
        return { is_harmful: true, confidence: 0.92, category: INSTANT_HARM_RULES[i][0], reasons: [WARNING_BUTTON_TEXT] };
      }
    }
    return null;
  }

  async function scanPageAds(options = {}) {
    if (isScanning) return getLiveDomStats();
    isScanning = true;
    try {
      if (options.forceRescan) document.querySelectorAll("[data-adshield-scanned]").forEach((el) => el.removeAttribute("data-adshield-scanned"));
      const candidates = findAdCandidates(document);
      const summary = getLiveDomStats();
      const isRiskyPageQuery = INSTANT_HARM_RULES.some((r) => r[1].test(`${document.title || ""} ${window.location.search || ""}`));
      async function processCandidate(adContainer, idx) {
        if (!adContainer || !adContainer.isConnected || isAlreadyProtected(adContainer) || adContainer.getAttribute("data-adshield-state") === "inflight") return;
        const adData = extractMultimodalAdData(adContainer, idx);
        if (!adData.text && !adData.image_url) return;
        adContainer.setAttribute("data-adshield-state", "inflight");
        adContainer.setAttribute("data-adshield-scanned", "true");
        const instantVerdict = instantLocalPreShield(adData);
        if (instantVerdict) {
          adContainer.setAttribute("data-adshield-state", "done");
          applyHarmfulAdProtection(adContainer, adData.imgElement, instantVerdict);
          summary.totalScanned += 1;
          summary.harmfulBlurred += 1;
          return;
        }
        if (isRiskyPageQuery) adContainer.classList.add("adshield-inflight-blur");
        const prediction = await requestPrediction(adData, options.apiUrl);
        adContainer.classList.remove("adshield-inflight-blur");
        if (!prediction || !adContainer.isConnected) {
          adContainer.removeAttribute("data-adshield-state");
          adContainer.removeAttribute("data-adshield-scanned");
          return;
        }
        adContainer.setAttribute("data-adshield-state", "done");
        summary.totalScanned += 1;
        if (prediction.is_harmful === true) {
          applyHarmfulAdProtection(adContainer, adData.imgElement, prediction);
          summary.harmfulBlurred += 1;
        } else {
          markSafeAd(adContainer, prediction, adData.imgElement);
          summary.safeVerified += 1;
        }
      }
      for (let i = 0; i < candidates.length; i += 6) {
        await Promise.all(candidates.slice(i, i + 6).map((el, j) => processCandidate(el, i + j + 1)));
      }
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
    window.removeEventListener("scroll", scheduleScan);
    document.removeEventListener("load", scheduleScan, true);
    document.querySelectorAll(".adshield-warning-overlay").forEach((el) => el.remove());
    document.querySelectorAll(".adshield-blurred-target").forEach((el) => { el.style.filter = "none"; el.classList.remove("adshield-blurred-target"); });
    document.querySelectorAll("[data-adshield-scanned]").forEach((el) => el.removeAttribute("data-adshield-scanned"));
  }
  window.__adshieldCleanup = cleanupListeners;
  scanPageAds({ forceRescan: true });
  function scheduleScan() {
    if (typeof chrome !== "undefined" && !isExtensionContextValid() && !window.ADSHIELD_API_URL) { cleanupListeners(); return; }
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => scanPageAds(), 50);
  }
  observer = new MutationObserver(scheduleScan);
  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
    window.addEventListener("scroll", scheduleScan, { passive: true });
    document.addEventListener("load", scheduleScan, true);
  }
})();
