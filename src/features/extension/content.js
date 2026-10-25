/**
 * Stage 4 (Week 6 & 7): Content Script (`content.js`).
 */
(function initAdShieldContentScript() {
  if (typeof window.__adshieldCleanup === "function") {
    try { window.__adshieldCleanup(); } catch (_e) {}
  }

  function isExtensionContextValid() {
    try { return Boolean(typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.id); } catch (_e) { return false; }
  }

  const DEFAULT_API_URL = "http://127.0.0.1:8000/predict";
  const WARNING_BUTTON_TEXT = "Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem";
  const HIDE_AGAIN_BUTTON_TEXT = "Ẩn lại quảng cáo độc hại";
  const GAMBLING_CONTEXT_TERMS = [
    "top nhà cái", "nhà cái", "tỷ lệ kèo", "kèo nhà cái", "soi kèo", "cược ngay",
    "cá cược", "cá độ", "nổ hũ", "tài xỉu", "casino", "xoilac", "cakhia", "8xbet",
    "fb88", "w88", "m88", "kubet", "hi88", "jun88", "new88", "789bet", "f8bet", "shbet", "fun88",
  ];

  function detectPageGamblingSignals() {
    const navSample = Array.from(document.querySelectorAll("header, nav, .header, .menu, .navbar, a"))
      .slice(0, 60)
      .map((el) => (el.innerText || el.textContent || "").trim())
      .join(" ");
    const pageSample = `${document.title || ""} ${window.location.href || ""} ${window.location.pathname || ""} ${navSample}`.toLowerCase();
    return GAMBLING_CONTEXT_TERMS.filter((term) => pageSample.includes(term));
  }

  const SAFE_NAV_PATTERN =
    /^(live\b|livescore|trận hot|blv\b|hôm nay|ngày mai|tất cả|bóng đá|bóng rổ|tennis|cầu lông|bóng chuyền|lịch thi đấu|highlight|xem lại|bảng xếp hạng|kqbđ|cẩm nang|tuyển dụng)/i;

  function isSafeNavigationOrLogo(imgEl) {
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

  function countCardImages(el) {
    if (!el || !el.querySelectorAll) return 0;
    let count = 0;
    const imgs = el.querySelectorAll("img");
    for (let i = 0; i < imgs.length; i += 1) {
      const im = imgs[i];
      const cls = String(im.className || "").toLowerCase();
      const alt = String(im.alt || "").toLowerCase();
      const src = String(im.currentSrc || im.src || "").toLowerCase();
      if (
        cls.includes("star") || alt.includes("star") || src.includes("star") ||
        cls.includes("icon") || alt.includes("icon") || src.includes("icon") ||
        cls.includes("badge") || alt.includes("badge") || src.includes("badge") ||
        cls.includes("rank") || alt.includes("rank") || cls.includes("flag") || alt.includes("flag")
      ) continue;
      const w = im.naturalWidth || im.width || im.clientWidth || 0;
      const h = im.naturalHeight || im.height || im.clientHeight || 0;
      if (h > 0 && h <= 32) continue;
      if ((w === 0 && h === 0) || w >= 44 || h >= 44) count += 1;
    }
    return count;
  }

  function isAlreadyProtected(el) {
    if (!el || !el.closest) return false;
    return Boolean(
      el.closest(".adshield-card-wrapper, .adshield-warning-overlay, .adshield-safe-pill, [data-adshield-verdict], [data-adshield-scanned='true']") ||
      el.getAttribute("data-adshield-scanned") === "true"
    );
  }

  function findClosestMediaTextContainer(imgEl) {
    const explicitCard = imgEl.closest(
      "[data-ad-card], .ad-card, .sponsored-post, [data-testid*='ad-card'], [data-offer-name], [data-deal-id], [class*='ranking'], [class*='offer'], [class*='casino'], [class*='bookmaker'], [class*='review-item'], [class*='item-casino']"
    );
    if (explicitCard) return explicitCard;

    let bestCard = imgEl, curr = imgEl.parentElement;
    for (let depth = 0; depth < 6 && curr && curr !== document.body; depth += 1) {
      const cls = String(curr.className || "").toLowerCase();
      if (["MAIN", "HEADER", "FOOTER", "NAV"].includes(curr.tagName) || /header|navbar|menu|topbar/.test(cls)) break;
      if (countCardImages(curr) > 1) break;
      const ch = curr.clientHeight || 0, txtLen = (curr.innerText || curr.textContent || "").trim().length;
      if (ch > 750 || txtLen > 950) break;
      bestCard = curr;
      if (curr.hasAttribute("data-offer-name") || (cls.includes("offer") && cls.includes("item"))) return curr;
      curr = curr.parentElement;
    }

    const bestText = (bestCard.innerText || bestCard.textContent || "").trim();
    if (bestCard !== imgEl && bestText.length >= 20) return bestCard;

    if (isBannerLikeImage(imgEl)) {
      const tightAnchor = imgEl.closest("a[href], button");
      if (tightAnchor && countCardImages(tightAnchor) <= 1 && (tightAnchor.clientHeight || 0) <= 180) return tightAnchor;
      return imgEl;
    }
    return bestCard;
  }

  function extractAdjacentSiblingText(node) {
    const parts = [];
    let curr = node;
    for (let depth = 0; depth < 4 && curr && curr !== document.body; depth += 1) {
      if (countCardImages(curr) > 1) break;
      for (const dir of ["previousElementSibling", "nextElementSibling"]) {
        let sib = curr[dir];
        for (let step = 0; step < 2 && sib; step += 1) {
          if (countCardImages(sib) === 0) {
            const txt = (sib.innerText || sib.textContent || "").replace(/\s+/g, " ").trim().slice(0, 260);
            if (txt.length >= 4 && !parts.includes(txt)) {
              if (dir === "previousElementSibling") parts.unshift(txt); else parts.push(txt);
            }
          }
          sib = sib[dir];
        }
      }
      curr = curr.parentElement;
    }
    return parts;
  }

  function findAdCandidates(root = document) {
    const explicitSelectors = [
      "[data-ad-card]", ".ad-card", ".sponsored-post", '[data-testid*="ad-card"]',
      '[aria-label*="Sponsored"]', '[aria-label*="Được tài trợ"]', "[data-offer-name]",
    ];
    const candidateSet = new Set();
    explicitSelectors.forEach((sel) => {
      root.querySelectorAll(sel).forEach((el) => { if (!isAlreadyProtected(el)) candidateSet.add(el); });
    });

    const ctaKeywords =
      "casino|casino games|live casino|sòng bài|baccarat|roulette|game bài|top nhà cái|cược|cá cược|cá độ|8xbet|fb88|w88|m88|kubet|hi88|jun88|new88|789bet|f8bet|shbet|fun88|188bet|bk8|ggbet|betting sites|deposit bonus|nhà cái uy tín|tặng 88k|nổ hũ|tài xỉu|play now|chơi ngay|cược ngay|thưởng nạp|nạp lần đầu|thưởng chào mừng|tiền thưởng gửi tiền|vòng quay miễn phí|vòng quay|free spins|1xbet|aw8|jp88|jackpot88|we88|king88|longfu88|dafabet|me88|vn88".split("|");
    root.querySelectorAll("a, button, span, li, div").forEach((btnEl) => {
      if (isAlreadyProtected(btnEl)) return;
      const txt = (btnEl.innerText || btnEl.textContent || "").replace(/\s+/g, " ").trim().toLowerCase();
      if (txt.length >= 4 && txt.length <= 65 && ctaKeywords.some((kw) => txt.includes(kw))) {
        const fullCard = btnEl.closest("[data-offer-name], [class*='ranking'], [class*='offer'], [class*='casino'], [class*='card'], [class*='item'], tr, li, article");
        if (fullCard && fullCard !== document.body && (fullCard.clientHeight || 0) <= 750 && !isAlreadyProtected(fullCard)) candidateSet.add(fullCard);
        else if (countCardImages(btnEl) === 0) candidateSet.add(btnEl);
      }
    });

    root.querySelectorAll("img").forEach((imgEl) => {
      if (isAlreadyProtected(imgEl) || isSafeNavigationOrLogo(imgEl)) return;
      const container = findClosestMediaTextContainer(imgEl);
      if (!container || isAlreadyProtected(container)) return;
      const width = imgEl.naturalWidth || imgEl.width || imgEl.clientWidth || container.clientWidth || 0;
      const containerText = (container.innerText || container.textContent || "").replace(/\s+/g, " ").trim();
      const hasText = containerText.length >= 4 || Boolean(container.querySelector("p, span, h1, h2, h3, h4, h5, h6, figcaption, a, button, div")) || extractAdjacentSiblingText(imgEl).length > 0;
      if ((hasText && (width >= 44 || width === 0)) || isBannerLikeImage(imgEl)) candidateSet.add(container);
    });

    const list = Array.from(candidateSet).filter((el) => el.isConnected && !isAlreadyProtected(el));
    return list.filter((el) => !list.some((other) => other !== el && other.contains(el)));
  }

  function resolveImageSource(imgEl, container) {
    if (!imgEl) return container.getAttribute("data-image-hint") || "";
    const candidates = [
      imgEl.getAttribute("data-src"), imgEl.getAttribute("data-lazy-src"),
      imgEl.getAttribute("data-original"), imgEl.currentSrc, imgEl.src,
    ].filter((s) => s && !s.startsWith("data:image/gif"));
    let url = candidates[0] || imgEl.src || "";
    if (!url && imgEl.srcset) url = imgEl.srcset.split(",")[0].trim().split(" ")[0];
    if (url.startsWith("blob:")) {
      try {
        const cv = document.createElement("canvas");
        cv.width = 224; cv.height = 224;
        cv.getContext("2d").drawImage(imgEl, 0, 0, 224, 224);
        return cv.toDataURL("image/jpeg", 0.78);
      } catch (_e) { return url; }
    }
    return url;
  }

  function extractMultimodalAdData(adContainer, index) {
    const imgElement = adContainer.tagName === "IMG" ? adContainer : adContainer.querySelector("img");
    const rawImgUrl = resolveImageSource(imgElement, adContainer);

    const anchorEl = adContainer.tagName === "A" ? adContainer : adContainer.querySelector("a[href]") || adContainer.closest("a[href]");
    const linkHref = anchorEl ? anchorEl.getAttribute("href") || anchorEl.href || "" : "";
    const collectedParts = [];

    const selfText = (adContainer.innerText || adContainer.textContent || "").replace(/\s+/g, " ").trim();
    if (selfText && selfText.length >= 4 && selfText.length <= 360) collectedParts.push(selfText);

    const attrHints = [
      adContainer.getAttribute("data-offer-name"), adContainer.getAttribute("data-brand"),
      adContainer.getAttribute("title"), adContainer.getAttribute("aria-label"),
    ].filter(Boolean);
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

    extractAdjacentSiblingText(imgElement || adContainer).forEach((st) => {
      if (!collectedParts.includes(st)) collectedParts.push(st);
    });

    const pageSignals = detectPageGamblingSignals();
    if (pageSignals.length > 0) {
      collectedParts.push(`Ngữ cảnh trang web cá cược: ${pageSignals.slice(0, 4).join(", ")}`);
    }
    if (linkHref && !linkHref.startsWith("javascript:")) collectedParts.push(linkHref);

    const combinedHint = [rawImgUrl, linkHref, String(adContainer.className || ""), adContainer.id || ""].filter(Boolean).join(" ");
    return {
      ad_id: adContainer.getAttribute("data-ad-id") || `dom_ad_${index}`,
      image_url: rawImgUrl || combinedHint,
      text: collectedParts.join(" — ").slice(0, 650),
      imgElement,
    };
  }

  /**
   * Apply `element.style.filter = "blur(10px)"` and inject the interactive warning button.
   */
  function applyHarmfulAdProtection(adContainer, imgElement, prediction) {
    if (!adContainer || !adContainer.isConnected) return;
    if (adContainer.closest(".adshield-warning-overlay")) return;

    let hostContainer = adContainer;
    if (hostContainer.tagName === "IMG" && hostContainer.parentElement) {
      const imgWrapper = document.createElement("div");
      hostContainer.parentElement.insertBefore(imgWrapper, hostContainer);
      imgWrapper.appendChild(hostContainer);
      hostContainer = imgWrapper;
    }

    if (window.getComputedStyle && window.getComputedStyle(hostContainer).display === "inline") {
      hostContainer.style.display = "inline-block";
    }
    hostContainer.classList.add("adshield-card-wrapper");
    hostContainer.setAttribute("data-adshield-verdict", "harmful");
    hostContainer.setAttribute("data-adshield-scanned", "true");
    if (imgElement) {
      imgElement.setAttribute("data-adshield-scanned", "true");
    }
    hostContainer.querySelectorAll("*").forEach((desc) => desc.setAttribute("data-adshield-scanned", "true"));

    let targetToBlur = hostContainer.querySelector("[data-ad-media-body]") || imgElement;
    if (!targetToBlur) {
      const innerWrap = document.createElement("div");
      innerWrap.setAttribute("data-ad-media-body", "true");
      const children = Array.from(hostContainer.childNodes).filter(
        (node) => !node.classList || !node.classList.contains("adshield-warning-overlay")
      );
      children.forEach((child) => innerWrap.appendChild(child));
      hostContainer.appendChild(innerWrap);
      targetToBlur = innerWrap;
    }

    // Exact Stage 4 Week 7 requirement:
    targetToBlur.style.filter = "blur(10px)";
    targetToBlur.classList.add("adshield-blurred-target");
    if (imgElement && imgElement !== targetToBlur) {
      imgElement.style.filter = "blur(10px)";
    }

    hostContainer.querySelectorAll(".adshield-warning-overlay").forEach((el) => el.remove());

    const confidencePct = Math.round((Number(prediction.confidence) || 0.89) * 100);
    const reasonText = (Array.isArray(prediction.reasons) && prediction.reasons[0]) || "Mô hình CLIP + Classifier phát hiện dấu hiệu quảng cáo gây hại.";
    const containerWidth = hostContainer.clientWidth || (imgElement ? imgElement.clientWidth || imgElement.width : 0) || 0;
    const containerHeight = hostContainer.clientHeight || (imgElement ? imgElement.clientHeight || imgElement.height : 0) || 0;
    const isMicroBadge = (containerWidth > 0 && containerWidth < 220) || (containerHeight > 0 && containerHeight < 48);
    const isCompactBanner = !isMicroBadge && containerHeight > 0 && containerHeight < 135;

    const overlay = document.createElement("div");
    overlay.className = isMicroBadge ? "adshield-warning-overlay adshield-overlay-micro" : isCompactBanner ? "adshield-warning-overlay adshield-overlay-compact" : "adshield-warning-overlay";
    overlay.setAttribute("data-testid", "adshield__warning--overlay");

    const badge = document.createElement("div");
    badge.className = "adshield-badge-danger";
    badge.textContent = `Cảnh báo AI Đa phương thức • Độ tin cậy ${confidencePct}%`;

    const reasonPara = document.createElement("p");
    reasonPara.className = "adshield-reason-text";
    reasonPara.textContent = reasonText;

    const closedBtnLabel = isMicroBadge ? "Quảng cáo độc hại" : WARNING_BUTTON_TEXT;
    const openedBtnLabel = isMicroBadge ? "Ẩn lại" : HIDE_AGAIN_BUTTON_TEXT;

    const toggleButton = document.createElement("button");
    toggleButton.type = "button";
    toggleButton.className = "adshield-reveal-btn";
    toggleButton.setAttribute("data-testid", "adshield__reveal--btn");
    toggleButton.title = WARNING_BUTTON_TEXT;
    toggleButton.textContent = closedBtnLabel;

    let isRevealed = false;
    toggleButton.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      isRevealed = !isRevealed;

      targetToBlur.style.filter = isRevealed ? "none" : "blur(10px)";
      targetToBlur.classList.toggle("adshield-blurred-target", !isRevealed);
      targetToBlur.classList.toggle("adshield-unblurred-target", isRevealed);
      if (imgElement) imgElement.style.filter = isRevealed ? "none" : "blur(10px)";
      overlay.classList.toggle("adshield-overlay-minimized", isRevealed);
      toggleButton.textContent = isRevealed ? openedBtnLabel : closedBtnLabel;

      if (isRevealed) {
        hostContainer.querySelectorAll(".adshield-warning-overlay").forEach((ov) => {
          if (ov !== overlay) ov.remove();
        });
        hostContainer.querySelectorAll(".adshield-blurred-target").forEach((bt) => {
          bt.style.filter = "none";
          bt.classList.remove("adshield-blurred-target");
          bt.classList.add("adshield-unblurred-target");
        });
      }
    });

    overlay.appendChild(badge);
    overlay.appendChild(reasonPara);
    overlay.appendChild(toggleButton);
    hostContainer.appendChild(overlay);
  }

  function markSafeAd(adContainer, prediction) {
    adContainer.setAttribute("data-adshield-verdict", "safe");
    if (!adContainer.hasAttribute("data-ad-card")) return;
    adContainer.classList.add("adshield-card-wrapper");
    if (!adContainer.querySelector(".adshield-safe-pill")) {
      const pill = document.createElement("span");
      pill.className = "adshield-safe-pill";
      pill.setAttribute("data-testid", "adshield__safe--badge");
      const confPct = Math.round((Number(prediction.confidence) || 0.9) * 100);
      pill.textContent = `An toàn (${confPct}%)`;
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
            } catch (_e) {
              resolve(null);
            }
          });
        } catch (_err) {
          resolve(null);
        }
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
    } catch (_err) {
      return null;
    }
  }

  let isScanning = false;

  async function scanPageAds(options = {}) {
    if (isScanning) return { totalScanned: 0, harmfulBlurred: 0, safeVerified: 0 };
    isScanning = true;
    try {
      if (options.forceRescan) {
        document.querySelectorAll("[data-adshield-scanned]").forEach((el) => el.removeAttribute("data-adshield-scanned"));
      }

      const candidates = findAdCandidates(document);
      const summary = { totalScanned: 0, harmfulBlurred: 0, safeVerified: 0 };

      for (let i = 0; i < candidates.length; i += 1) {
        const adContainer = candidates[i];
        if (!adContainer || !adContainer.isConnected || isAlreadyProtected(adContainer)) continue;
        if (adContainer.getAttribute("data-adshield-state") === "inflight") continue;
        const adData = extractMultimodalAdData(adContainer, i + 1);
        if (!adData.text && !adData.image_url) continue;

        adContainer.setAttribute("data-adshield-state", "inflight");
        adContainer.setAttribute("data-adshield-scanned", "true");
        const prediction = await requestPrediction(adData, options.apiUrl);
        if (!prediction || !adContainer.isConnected) {
          adContainer.removeAttribute("data-adshield-state");
          adContainer.removeAttribute("data-adshield-scanned");
          continue;
        }
        adContainer.setAttribute("data-adshield-state", "done");

        summary.totalScanned += 1;
        if (prediction.is_harmful === true) {
          applyHarmfulAdProtection(adContainer, adData.imgElement, prediction);
          summary.harmfulBlurred += 1;
        } else {
          markSafeAd(adContainer, prediction);
          summary.safeVerified += 1;
        }
      }

      return summary;
    } finally {
      isScanning = false;
    }
  }

  window.AdShieldContentScanner = { scanPageAds, applyHarmfulAdProtection, WARNING_BUTTON_TEXT };

  if (isExtensionContextValid()) {
    try {
      chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
        if (msg && msg.type === "ADSHIELD_SCAN_NOW") {
          scanPageAds({ forceRescan: true }).then((summary) => sendResponse({ ok: true, summary }));
          return true;
        }
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
    document.querySelectorAll(".adshield-blurred-target").forEach((el) => {
      el.style.filter = "none";
      el.classList.remove("adshield-blurred-target");
    });
    document.querySelectorAll("[data-adshield-scanned]").forEach((el) => el.removeAttribute("data-adshield-scanned"));
  }
  window.__adshieldCleanup = cleanupListeners;

  scanPageAds({ forceRescan: true });

  function scheduleScan() {
    if (typeof chrome !== "undefined" && !isExtensionContextValid() && !window.ADSHIELD_API_URL) {
      cleanupListeners();
      return;
    }
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => scanPageAds(), 400);
  }

  observer = new MutationObserver(scheduleScan);
  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
    window.addEventListener("scroll", scheduleScan, { passive: true });
    document.addEventListener("load", scheduleScan, true);
  }
})();
