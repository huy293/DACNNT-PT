/**
 * Stage 4 (Week 6 & 7): Content Script (`content.js`).
 *
 * Scans the current webpage for advertisement blocks containing `<img>` paired with
 * `<p>` or `<span>`, sends `{ text, image_url }` to the FastAPI Backend (`POST /predict`),
 * and when `is_harmful === true`:
 *   1. Sets `element.style.filter = "blur(10px)"` (exact CSS requirement from Stage 4 plan).
 *   2. Wraps a protective button outside: "Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem".
 */

(function initAdShieldContentScript() {
  if (typeof window.__adshieldCleanup === "function") {
    try {
      window.__adshieldCleanup();
    } catch (_e) {}
  }

  function isExtensionContextValid() {
    try {
      return Boolean(typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.id);
    } catch (_e) {
      return false;
    }
  }

  const DEFAULT_API_URL = "http://127.0.0.1:8000/predict";
  const WARNING_BUTTON_TEXT = "Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem";
  const HIDE_AGAIN_BUTTON_TEXT = "Ẩn lại quảng cáo độc hại";

  /**
   * Discover candidate advertisement containers on the webpage.
   * Supports explicit ad cards (`[data-ad-card]`, `.ad-card`, `.sponsored-post`) as well as
   * generic containers containing `<img>` accompanied by `<p>` or `<span>`.
   */
  const GAMBLING_CONTEXT_TERMS = [
    "top nhà cái", "nhà cái", "tỷ lệ kèo", "kèo nhà cái", "soi kèo", "cược ngay",
    "cá cược", "cá độ", "nổ hũ", "tài xỉu", "casino", "xoilac", "cakhia", "8xbet",
    "fb88", "w88", "m88", "kubet", "hi88", "jun88", "new88", "789bet", "f8bet", "shbet", "fun88",
  ];

  function detectPageGamblingSignals() {
    const pageSample = (
      (document.title || "") +
      " " +
      (window.location.hostname || "") +
      " " +
      Array.from(document.querySelectorAll("header, nav, .header, .menu, .navbar, a"))
        .slice(0, 60)
        .map((el) => (el.innerText || el.textContent || "").trim())
        .join(" ")
    ).toLowerCase();

    return GAMBLING_CONTEXT_TERMS.filter((term) => pageSample.includes(term));
  }

  function isBannerLikeImage(imgEl) {
    const w = imgEl.naturalWidth || imgEl.width || imgEl.clientWidth || 0;
    const h = imgEl.naturalHeight || imgEl.height || imgEl.clientHeight || 0;
    const src = (imgEl.currentSrc || imgEl.src || "").toLowerCase();
    const aspect = h > 0 ? w / h : 1;
    const inAnchor = Boolean(imgEl.closest("a[href]"));
    const inBannerBox = Boolean(
      imgEl.closest('[class*="banner"], [class*="ads"], [id*="ads"], [class*="qc"], [class*="sponsor"], [class*="bet"], [class*="nhacai"]')
    );
    const isGifBanner = src.includes(".gif") && w >= 120;
    const isWideLeaderboard = w >= 240 && h >= 28 && aspect >= 2.4;
    return isGifBanner || isWideLeaderboard || (inAnchor && w >= 130 && h >= 30) || (inBannerBox && w >= 100);
  }

  function findClosestMediaTextContainer(imgEl) {
    const explicitCard = imgEl.closest(
      "[data-ad-card], .ad-card, .sponsored-post, [data-testid*='ad-card']"
    );
    if (explicitCard) {
      return explicitCard;
    }

    const feedCard = imgEl.closest(
      "article, .feed-card, .item-news, .box-category-item, .MjjYud, .g, .isv-r"
    );
    // Only use feedCard if it represents a single-image card (not a long multi-image article)
    if (feedCard && feedCard.querySelectorAll("img").length <= 1 && (feedCard.clientHeight || 0) <= 800) {
      return feedCard;
    }

    const figureOrAnchor = imgEl.closest("figure, a[href]");
    if (figureOrAnchor && figureOrAnchor.querySelectorAll("img").length <= 2) {
      return figureOrAnchor;
    }

    let current = imgEl.parentElement;
    for (let depth = 0; depth < 3 && current && current !== document.body; depth += 1) {
      const imgCount = current.querySelectorAll("img").length;
      if (imgCount > 1) {
        break;
      }
      if (current.querySelector("p, span, h2, h3, h4, figcaption, a")) {
        return current;
      }
      current = current.parentElement;
    }
    return imgEl.parentElement || imgEl;
  }

  function extractAdjacentSiblingText(node) {
    const parts = [];
    let anchor = node;
    if (anchor && anchor.parentElement && anchor.parentElement.querySelectorAll("img").length === 1) {
      if (["P", "FIGURE", "A", "DIV"].includes(anchor.parentElement.tagName)) {
        anchor = anchor.parentElement;
      }
    }
    if (!anchor) {
      return parts;
    }
    let prev = anchor.previousElementSibling;
    for (let step = 0; step < 3 && prev; step += 1) {
      if (!prev.querySelector("img")) {
        const txt = (prev.innerText || prev.textContent || "").trim();
        if (txt && txt.length >= 4) {
          parts.unshift(txt.slice(0, 260));
        }
      }
      prev = prev.previousElementSibling;
    }
    const next = anchor.nextElementSibling;
    if (next && !next.querySelector("img")) {
      const txt = (next.innerText || next.textContent || "").trim();
      if (txt && txt.length >= 4) {
        parts.push(txt.slice(0, 220));
      }
    }
    return parts;
  }

  function findAdCandidates(root = document) {
    const explicitSelectors = [
      "[data-ad-card]",
      ".ad-card",
      ".sponsored-post",
      '[data-testid*="ad-card"]',
      '[aria-label*="Sponsored"]',
      '[aria-label*="Được tài trợ"]',
    ];
    const candidates = new Set();

    explicitSelectors.forEach((sel) => {
      root.querySelectorAll(sel).forEach((el) => {
        if (el.getAttribute("data-adshield-scanned") !== "true") {
          candidates.add(el);
        }
      });
    });

    // Also catch explicit gambling CTA buttons/links in headers (e.g. "TOP NHÀ CÁI", "CƯỢC NGAY")
    root.querySelectorAll("a, button").forEach((btnEl) => {
      if (btnEl.getAttribute("data-adshield-scanned") === "true") {
        return;
      }
      const txt = (btnEl.innerText || btnEl.textContent || "").trim().toLowerCase();
      if (
        txt.length >= 6 &&
        txt.length <= 45 &&
        ("top nhà cái|cược ngay|nhà cái uy tín|tặng 88k|nổ hũ".split("|").some((kw) => txt.includes(kw)))
      ) {
        candidates.add(btnEl);
      }
    });

    // General heuristic: scan every content/banner <img> (including multiple images inside long articles)
    root.querySelectorAll("img").forEach((imgEl) => {
      if (imgEl.getAttribute("data-adshield-scanned") === "true") {
        return;
      }
      const container = findClosestMediaTextContainer(imgEl);
      if (!container || container.getAttribute("data-adshield-scanned") === "true") {
        return;
      }
      const width = imgEl.naturalWidth || imgEl.width || imgEl.clientWidth || container.clientWidth || 0;
      const hasLocalOrSiblingText =
        Boolean(container.querySelector("p, span, h2, h3, h4, figcaption, a, button")) ||
        extractAdjacentSiblingText(imgEl).length > 0;
      if ((hasLocalOrSiblingText && width >= 60) || isBannerLikeImage(imgEl)) {
        candidates.add(container);
      }
    });

    return Array.from(candidates);
  }

  /**
   * Extract multimodal pair `{ image_url, text, imgElement }` from an ad DOM container.
   */
  function extractMultimodalAdData(adContainer, index) {
    const imgElement = adContainer.tagName === "IMG" ? adContainer : adContainer.querySelector("img");
    const rawImgUrl = imgElement
      ? imgElement.currentSrc || imgElement.src || imgElement.getAttribute("data-src") || ""
      : adContainer.getAttribute("data-image-hint") || "";

    const anchorEl =
      adContainer.tagName === "A"
        ? adContainer
        : adContainer.querySelector("a[href]") || adContainer.closest("a[href]");
    const linkHref = anchorEl ? anchorEl.getAttribute("href") || anchorEl.href || "" : "";

    const textNodes = adContainer.querySelectorAll("p, span, h2, h3, h4, figcaption, a, button, [data-ad-text]");
    const collectedParts = [];

    const selfText = (adContainer.innerText || adContainer.textContent || "").trim();
    if (selfText && selfText.length >= 4 && selfText.length <= 160) {
      collectedParts.push(selfText);
    }

    textNodes.forEach((node) => {
      if (node.closest(".adshield-warning-overlay")) {
        return;
      }
      const txt = (node.innerText || node.textContent || "").trim();
      if (txt && txt.length >= 3 && !collectedParts.includes(txt)) {
        collectedParts.push(txt);
      }
    });

    if (imgElement) {
      const altAndTitle = [imgElement.alt, imgElement.title].filter(Boolean).join(" ").trim();
      if (altAndTitle && !collectedParts.includes(altAndTitle)) {
        collectedParts.push(altAndTitle);
      }
    }

    // If the image sits inside a multi-paragraph article (e.g. "NHÀ CÁI BK8..." heading + <p> above/below),
    // include the adjacent sibling paragraphs/headings so the multimodal classifier sees its caption/context.
    if (collectedParts.join(" ").length < 40) {
      const siblingTexts = extractAdjacentSiblingText(imgElement || adContainer);
      siblingTexts.forEach((st) => {
        if (!collectedParts.includes(st)) {
          collectedParts.push(st);
        }
      });
    }

    // If this is a pure-image banner (e.g., 8Xbet GIF/WebP banner with text baked into the image),
    // include link destination and page-level gambling banner context for multimodal inference.
    if (imgElement && isBannerLikeImage(imgElement)) {
      const pageSignals = detectPageGamblingSignals();
      if (pageSignals.length > 0 && collectedParts.join(" ").length < 35) {
        collectedParts.push(
          `Banner quảng cáo nhà cái cá cược trực tuyến (${pageSignals.slice(0, 4).join(", ")})`
        );
      }
    }

    if (linkHref && !linkHref.startsWith("javascript:")) {
      collectedParts.push(linkHref);
    }

    const combinedHint = [rawImgUrl, linkHref, String(adContainer.className || ""), adContainer.id || ""]
      .filter(Boolean)
      .join(" ");

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
    if (imgElement) {
      imgElement.setAttribute("data-adshield-scanned", "true");
    }

    let targetToBlur =
      hostContainer.querySelector("[data-ad-media-body]") || imgElement;
    if (!targetToBlur) {
      const innerWrap = document.createElement("div");
      innerWrap.setAttribute("data-ad-media-body", "true");
      while (hostContainer.firstChild) {
        innerWrap.appendChild(hostContainer.firstChild);
      }
      hostContainer.appendChild(innerWrap);
      targetToBlur = innerWrap;
    }

    // Exact Stage 4 Week 7 requirement:
    targetToBlur.style.filter = "blur(10px)";
    targetToBlur.classList.add("adshield-blurred-target");
    if (imgElement && imgElement !== targetToBlur) {
      imgElement.style.filter = "blur(10px)";
    }

    const existingOverlay = hostContainer.querySelector(".adshield-warning-overlay");
    if (existingOverlay) {
      existingOverlay.remove();
    }

    const confidencePct = Math.round((Number(prediction.confidence) || 0.89) * 100);
    const reasonText =
      Array.isArray(prediction.reasons) && prediction.reasons.length > 0
        ? prediction.reasons[0]
        : "Mô hình CLIP + Classifier phát hiện dấu hiệu quảng cáo gây hại.";

    const containerHeight =
      hostContainer.clientHeight || (imgElement ? imgElement.clientHeight || imgElement.height : 0) || 0;
    const isCompactBanner = containerHeight > 0 && containerHeight < 135;

    const overlay = document.createElement("div");
    overlay.className = isCompactBanner
      ? "adshield-warning-overlay adshield-overlay-compact"
      : "adshield-warning-overlay";
    overlay.setAttribute("data-testid", "adshield__warning--overlay");

    const badge = document.createElement("div");
    badge.className = "adshield-badge-danger";
    badge.textContent = `Cảnh báo AI Đa phương thức • Độ tin cậy ${confidencePct}%`;

    const reasonPara = document.createElement("p");
    reasonPara.className = "adshield-reason-text";
    reasonPara.textContent = reasonText;

    const toggleButton = document.createElement("button");
    toggleButton.type = "button";
    toggleButton.className = "adshield-reveal-btn";
    toggleButton.setAttribute("data-testid", "adshield__reveal--btn");
    toggleButton.textContent = WARNING_BUTTON_TEXT;

    let isRevealed = false;
    toggleButton.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      isRevealed = !isRevealed;

      if (isRevealed) {
        targetToBlur.style.filter = "none";
        targetToBlur.classList.remove("adshield-blurred-target");
        targetToBlur.classList.add("adshield-unblurred-target");
        if (imgElement) {
          imgElement.style.filter = "none";
        }
        overlay.classList.add("adshield-overlay-minimized");
        toggleButton.textContent = HIDE_AGAIN_BUTTON_TEXT;
      } else {
        targetToBlur.style.filter = "blur(10px)";
        targetToBlur.classList.remove("adshield-unblurred-target");
        targetToBlur.classList.add("adshield-blurred-target");
        if (imgElement) {
          imgElement.style.filter = "blur(10px)";
        }
        overlay.classList.remove("adshield-overlay-minimized");
        toggleButton.textContent = WARNING_BUTTON_TEXT;
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
        body: JSON.stringify({
          ad_id: payload.ad_id,
          text: payload.text,
          image_url: payload.image_url,
        }),
      });
      return res.ok ? await res.json() : null;
    } catch (_err) {
      return null;
    }
  }

  async function scanPageAds(options = {}) {
    if (options.forceRescan) {
      document.querySelectorAll("[data-adshield-scanned]").forEach((el) => {
        el.removeAttribute("data-adshield-scanned");
      });
    }

    const candidates = findAdCandidates(document);
    const summary = { totalScanned: 0, harmfulBlurred: 0, safeVerified: 0 };

    for (let i = 0; i < candidates.length; i += 1) {
      const adContainer = candidates[i];
      if (!adContainer || !adContainer.isConnected) continue;
      const adData = extractMultimodalAdData(adContainer, i + 1);
      if (!adData.text && !adData.image_url) continue;

      adContainer.setAttribute("data-adshield-scanned", "true");
      const prediction = await requestPrediction(adData, options.apiUrl);
      if (!prediction) {
        adContainer.removeAttribute("data-adshield-scanned");
        continue;
      }

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
  }

  window.AdShieldContentScanner = {
    scanPageAds,
    applyHarmfulAdProtection,
    WARNING_BUTTON_TEXT,
  };

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

  scanPageAds();

  let debounceTimer = null;
  let observer = null;

  function cleanupListeners() {
    if (debounceTimer) clearTimeout(debounceTimer);
    if (observer) observer.disconnect();
    window.removeEventListener("scroll", scheduleScan);
    document.removeEventListener("load", scheduleScan, true);
  }
  window.__adshieldCleanup = cleanupListeners;

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
