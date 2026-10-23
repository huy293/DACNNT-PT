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

const tabsStats = new Map();

function createDefaultStats() {
  return {
    totalScanned: 0,
    harmfulBlurred: 0,
    safeVerified: 0,
    lastError: null,
    lastLatencyMs: 0,
  };
}

function getTabStats(tabId) {
  if (!tabId) return createDefaultStats();
  if (!tabsStats.has(tabId)) {
    tabsStats.set(tabId, createDefaultStats());
  }
  return tabsStats.get(tabId);
}

function resetTabStats(tabId) {
  if (!tabId) return;
  tabsStats.set(tabId, createDefaultStats());
  updateBadge(0, tabId);
}

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

function updateBadge(harmfulCount, tabId) {
  if (typeof chrome !== "undefined" && chrome.action && chrome.action.setBadgeText) {
    const text = harmfulCount > 0 ? String(harmfulCount) : "";
    if (tabId) {
      chrome.action.setBadgeText({ text, tabId });
      chrome.action.setBadgeBackgroundColor({ color: "#DC2626", tabId });
    } else {
      chrome.action.setBadgeText({ text });
      chrome.action.setBadgeBackgroundColor({ color: "#DC2626" });
    }
  }
}

function recordTabResult(tabId, result, settings) {
  const stats = getTabStats(tabId);
  stats.totalScanned += 1;
  stats.lastLatencyMs = result.latency_ms || 0;
  stats.lastError = null;
  if (result.is_harmful && result.confidence >= settings.confidenceThreshold) {
    stats.harmfulBlurred += 1;
    updateBadge(stats.harmfulBlurred, tabId);
  } else {
    stats.safeVerified += 1;
  }
}

async function callBackendPredict(payload, tabId) {
  const settings = await getSettings();
  const cacheKey = `${payload.image_url || ""}::${(payload.text || "").trim()}`;

  if (predictionCache.has(cacheKey)) {
    const cachedResult = predictionCache.get(cacheKey);
    recordTabResult(tabId, cachedResult, settings);
    return { ok: true, data: cachedResult, cached: true };
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
    predictionCache.set(cacheKey, result);
    recordTabResult(tabId, result, settings);

    return { ok: true, data: result, cached: false };
  } catch (err) {
    const stats = getTabStats(tabId);
    stats.lastError = err && err.message ? err.message : "Không thể kết nối Backend API";
    return { ok: false, error: stats.lastError };
  }
}

if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!message || !message.type) {
      return false;
    }

    const senderTabId = sender && sender.tab ? sender.tab.id : null;

    if (message.type === "ADSHIELD_PAGE_INIT" || message.type === "ADSHIELD_RESET_TAB_STATS") {
      if (senderTabId) {
        resetTabStats(senderTabId);
      }
      sendResponse({ ok: true });
      return true;
    }

    if (message.type === "ADSHIELD_PREDICT") {
      callBackendPredict(message.payload || {}, senderTabId).then(sendResponse);
      return true;
    }

    if (message.type === "ADSHIELD_GET_STATS") {
      const targetTabId = message.tabId || senderTabId;
      getSettings().then((settings) => {
        sendResponse({ ok: true, stats: getTabStats(targetTabId), settings });
      });
      return true;
    }

    if (message.type === "ADSHIELD_RESET_STATS") {
      predictionCache.clear();
      const targetTabId = message.tabId || senderTabId;
      if (targetTabId) {
        resetTabStats(targetTabId);
      } else {
        tabsStats.clear();
        updateBadge(0);
      }
      sendResponse({ ok: true, stats: getTabStats(targetTabId) });
      return true;
    }

    return false;
  });
}

// Reset tab stats and clear badge whenever the tab navigates to a new page or reloads
if (typeof chrome !== "undefined" && chrome.tabs) {
  if (chrome.tabs.onUpdated) {
    chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
      if (changeInfo.status === "loading" || changeInfo.url) {
        resetTabStats(tabId);
      }
    });
  }
  if (chrome.tabs.onRemoved) {
    chrome.tabs.onRemoved.addListener((tabId) => {
      tabsStats.delete(tabId);
    });
  }
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
