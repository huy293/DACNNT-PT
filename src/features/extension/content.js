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
  const DEFAULT_API_URL = "http://127.0.0.1:8000/predict";
  const WARNING_BUTTON_TEXT = "Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem";
  const HIDE_AGAIN_BUTTON_TEXT = "Ẩn lại quảng cáo độc hại";

  /**
   * Discover candidate advertisement containers on the webpage.
   * Supports explicit ad cards (`[data-ad-card]`, `.ad-card`, `.sponsored-post`) as well as
   * generic containers containing `<img>` accompanied by `<p>` or `<span>`.
   */
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

    // General heuristic from Stage 4 Week 6 plan: <img> accompanied by <p> or <span>
    root.querySelectorAll("img").forEach((imgEl) => {
      const container =
        imgEl.closest("[data-ad-card], .ad-card, .sponsored-post, article, .feed-card") ||
        imgEl.parentElement;
      if (!container || container.getAttribute("data-adshield-scanned") === "true") {
        return;
      }
      const hasTextCompanion = Boolean(container.querySelector("p, span"));
      const width = imgEl.naturalWidth || imgEl.width || container.clientWidth || 0;
      if (hasTextCompanion && width >= 120) {
        candidates.add(container);
      }
    });

    return Array.from(candidates);
  }

  /**
   * Extract multimodal pair `{ image_url, text, imgElement }` from an ad DOM container.
   */
  function extractMultimodalAdData(adContainer, index) {
    const imgElement = adContainer.querySelector("img");
    const imageUrl = imgElement
      ? imgElement.currentSrc || imgElement.src || imgElement.getAttribute("data-src") || ""
      : adContainer.getAttribute("data-image-hint") || "";

    const textNodes = adContainer.querySelectorAll("p, span, h3, h4, [data-ad-text]");
    const collectedParts = [];
    textNodes.forEach((node) => {
      if (node.closest(".adshield-warning-overlay")) {
        return;
      }
      const txt = (node.innerText || node.textContent || "").trim();
      if (txt && txt.length >= 4 && !collectedParts.includes(txt)) {
        collectedParts.push(txt);
      }
    });

    if (imgElement && imgElement.alt && !collectedParts.includes(imgElement.alt.trim())) {
      collectedParts.push(imgElement.alt.trim());
    }

    return {
      ad_id: adContainer.getAttribute("data-ad-id") || `dom_ad_${index}`,
      image_url: imageUrl,
      text: collectedParts.join(" — ").slice(0, 600),
      imgElement,
    };
  }

  /**
   * Apply `element.style.filter = "blur(10px)"` and inject the interactive warning button.
   */
  function applyHarmfulAdProtection(adContainer, imgElement, prediction) {
    adContainer.classList.add("adshield-card-wrapper");
    adContainer.setAttribute("data-adshield-verdict", "harmful");

    const targetToBlur =
      adContainer.querySelector("[data-ad-media-body]") || imgElement || adContainer;

    // Exact Stage 4 Week 7 requirement:
    targetToBlur.style.filter = "blur(10px)";
    targetToBlur.classList.add("adshield-blurred-target");
    if (imgElement && imgElement !== targetToBlur) {
      imgElement.style.filter = "blur(10px)";
    }

    const existingOverlay = adContainer.querySelector(".adshield-warning-overlay");
    if (existingOverlay) {
      existingOverlay.remove();
    }

    const confidencePct = Math.round((Number(prediction.confidence) || 0.89) * 100);
    const reasonText =
      Array.isArray(prediction.reasons) && prediction.reasons.length > 0
        ? prediction.reasons[0]
        : "Mô hình CLIP + Classifier phát hiện dấu hiệu quảng cáo gây hại.";

    const overlay = document.createElement("div");
    overlay.className = "adshield-warning-overlay";
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
        badge.style.display = "none";
        reasonPara.style.display = "none";
        toggleButton.textContent = HIDE_AGAIN_BUTTON_TEXT;
      } else {
        targetToBlur.style.filter = "blur(10px)";
        targetToBlur.classList.remove("adshield-unblurred-target");
        targetToBlur.classList.add("adshield-blurred-target");
        if (imgElement) {
          imgElement.style.filter = "blur(10px)";
        }
        overlay.classList.remove("adshield-overlay-minimized");
        badge.style.display = "inline-flex";
        reasonPara.style.display = "block";
        toggleButton.textContent = WARNING_BUTTON_TEXT;
      }
    });

    overlay.appendChild(badge);
    overlay.appendChild(reasonPara);
    overlay.appendChild(toggleButton);
    adContainer.appendChild(overlay);
  }

  /**
   * Mark a safe ad with a subtle verified badge on the container.
   */
  function markSafeAd(adContainer, prediction) {
    adContainer.classList.add("adshield-card-wrapper");
    adContainer.setAttribute("data-adshield-verdict", "safe");
    if (!adContainer.querySelector(".adshield-safe-pill")) {
      const pill = document.createElement("span");
      pill.className = "adshield-safe-pill";
      pill.setAttribute("data-testid", "adshield__safe--badge");
      const confPct = Math.round((Number(prediction.confidence) || 0.9) * 100);
      pill.textContent = `An toàn (${confPct}%)`;
      adContainer.appendChild(pill);
    }
  }

  /**
   * Send ad payload to Backend API via Background Service Worker (or direct fetch fallback).
   */
  async function requestPrediction(payload, customApiUrl) {
    if (
      typeof chrome !== "undefined" &&
      chrome.runtime &&
      typeof chrome.runtime.sendMessage === "function" &&
      !customApiUrl
    ) {
      return new Promise((resolve) => {
        chrome.runtime.sendMessage({ type: "ADSHIELD_PREDICT", payload }, (response) => {
          if (response && response.ok && response.data) {
            resolve(response.data);
          } else {
            resolve(null);
          }
        });
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
      if (!res.ok) {
        return null;
      }
      return await res.json();
    } catch (_err) {
      return null;
    }
  }

  /**
   * Scan all unscanned ads on the current page and apply protection.
   */
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
      const adData = extractMultimodalAdData(adContainer, i + 1);
      if (!adData.text && !adData.image_url) {
        continue;
      }

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

  // Expose helper on window for Demo Portal & automated E2E testing
  window.AdShieldContentScanner = {
    scanPageAds,
    applyHarmfulAdProtection,
    WARNING_BUTTON_TEXT,
  };

  // Listen for manual re-scan command from Extension Popup
  if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
      if (msg && msg.type === "ADSHIELD_SCAN_NOW") {
        scanPageAds({ forceRescan: true }).then((summary) => {
          sendResponse({ ok: true, summary });
        });
        return true;
      }
      return false;
    });
  }

  // Initial scan on page load + debounced MutationObserver for infinite scroll feeds
  scanPageAds();

  let debounceTimer = null;
  const observer = new MutationObserver(() => {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    debounceTimer = setTimeout(() => {
      scanPageAds();
    }, 600);
  });

  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
  }
})();
