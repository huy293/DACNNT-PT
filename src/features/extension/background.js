/**
 * Stage 4 (Week 6 & 7): Chrome/Edge Extension Background Service Worker (`background.js`).
 *
 * Responsibilities:
 * 1. Proxies multimodal ad prediction requests (`POST /predict`) from `content.js` to the
 *    FastAPI Backend (Localhost, HuggingFace Spaces, or Render) to avoid CORS / Mixed-Content blocks.
 * 2. Caches predictions by `(image_url + text)` key to avoid redundant API calls during scrolling.
 * 3. Maintains scan statistics (total scanned, harmful blurred, safe verified) for the Popup UI.
 */

const DEFAULT_SETTINGS = {
  apiEndpoint: "http://127.0.0.1:8000/predict",
  enabled: true,
  confidenceThreshold: 0.5,
};

const predictionCache = new Map();
const MAX_CACHE_ENTRIES = 500;
let consecutiveFailures = 0;
let circuitOpenUntil = 0;

const tabStats = {
  totalScanned: 0,
  harmfulBlurred: 0,
  safeVerified: 0,
  lastError: null,
  lastLatencyMs: 0,
};

async function getSettings() {
  return new Promise((resolve) => {
    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.get(DEFAULT_SETTINGS, (items) => {
        resolve({ ...DEFAULT_SETTINGS, ...items });
      });
    } else {
      resolve({ ...DEFAULT_SETTINGS });
    }
  });
}

function updateBadge(harmfulCount) {
  if (typeof chrome !== "undefined" && chrome.action && chrome.action.setBadgeText) {
    const text = harmfulCount > 0 ? String(harmfulCount) : "";
    chrome.action.setBadgeText({ text });
    chrome.action.setBadgeBackgroundColor({ color: "#DC2626" });
  }
}

async function callBackendPredict(payload) {
  const settings = await getSettings();
  const cacheKey = `${payload.image_url || ""}::${(payload.text || "").trim()}`;

  if (predictionCache.has(cacheKey)) {
    return { ok: true, data: predictionCache.get(cacheKey), cached: true };
  }

  if (Date.now() < circuitOpenUntil) {
    return { ok: false, error: "Circuit Breaker: Tạm ngắt kết nối 5s do Backend không phản hồi" };
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(settings.apiEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: payload.text || "",
        image_url: payload.image_url || null,
        ad_id: payload.ad_id || null,
      }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: Máy chủ trả về lỗi`);
    }

    const result = await response.json();
    consecutiveFailures = 0;
    circuitOpenUntil = 0;
    predictionCache.set(cacheKey, result);
    if (predictionCache.size > MAX_CACHE_ENTRIES) {
      const oldestKey = predictionCache.keys().next().value;
      predictionCache.delete(oldestKey);
    }

    tabStats.totalScanned += 1;
    tabStats.lastLatencyMs = result.latency_ms || 0;
    tabStats.lastError = null;
    if (result.is_harmful && result.confidence >= settings.confidenceThreshold) {
      tabStats.harmfulBlurred += 1;
      updateBadge(tabStats.harmfulBlurred);
    } else {
      tabStats.safeVerified += 1;
    }

    return { ok: true, data: result, cached: false };
  } catch (err) {
    consecutiveFailures += 1;
    if (consecutiveFailures >= 5) {
      circuitOpenUntil = Date.now() + 1000;
    }
    tabStats.lastError = err && err.message ? err.message : "Không thể kết nối Backend API";
    return { ok: false, error: tabStats.lastError };
  }
}

if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (!message || !message.type) {
      return false;
    }

    if (message.type === "ADSHIELD_PREDICT") {
      callBackendPredict(message.payload || {}).then(sendResponse);
      return true;
    }

    if (message.type === "ADSHIELD_GET_STATS") {
      getSettings().then((settings) => {
        sendResponse({ ok: true, stats: tabStats, settings });
      });
      return true;
    }

    if (message.type === "ADSHIELD_RESET_STATS") {
      predictionCache.clear();
      tabStats.totalScanned = 0;
      tabStats.harmfulBlurred = 0;
      tabStats.safeVerified = 0;
      tabStats.lastError = null;
      updateBadge(0);
      sendResponse({ ok: true, stats: tabStats });
      return true;
    }

    return false;
  });
}

// Automatically re-inject content script into open tabs when Extension is reloaded in chrome://extensions
if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onInstalled) {
  chrome.runtime.onInstalled.addListener(() => {
    if (!chrome.tabs || !chrome.scripting) return;
    chrome.tabs.query({ url: ["http://*/*", "https://*/*"] }, (tabs) => {
      if (chrome.runtime && chrome.runtime.lastError) return;
      (tabs || []).forEach((tab) => {
        if (!tab || !tab.id) return;
        chrome.scripting.insertCSS({ target: { tabId: tab.id }, files: ["content.css"] }, () => {
          void (chrome.runtime && chrome.runtime.lastError);
        });
        chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] }, () => {
          void (chrome.runtime && chrome.runtime.lastError);
        });
      });
    });
  });
}
