/**
 * Stage 4: Extension Popup Controller (`popup.js`).
 * Manages the 4 UI states (`Loading`, `Error`, `Empty`, `Success`), triggers active tab
 * ad scanning, and persists the `/predict` API URL configuration.
 */

(function initPopup() {
  const elLoading = document.getElementById("state-loading");
  const elError = document.getElementById("state-error");
  const elEmpty = document.getElementById("state-empty");
  const elSuccess = document.getElementById("state-success");
  const elErrorText = document.getElementById("error-message-text");

  const elStatTotal = document.getElementById("stat-total");
  const elStatHarmful = document.getElementById("stat-harmful");
  const elStatSafe = document.getElementById("stat-safe");
  const elInputUrl = document.getElementById("input-api-url");
  const elSaveToast = document.getElementById("save-toast");

  function showOnlyState(activeEl) {
    [elLoading, elError, elEmpty, elSuccess].forEach((section) => {
      if (section === activeEl) {
        section.classList.remove("hidden");
      } else {
        section.classList.add("hidden");
      }
    });
  }

  function renderStats(stats) {
    const total = Number(stats && stats.totalScanned) || 0;
    const harmful = Number(stats && stats.harmfulBlurred) || 0;
    const safe = Number(stats && stats.safeVerified) || 0;

    elStatTotal.textContent = String(total);
    elStatHarmful.textContent = String(harmful);
    elStatSafe.textContent = String(safe);

    if (stats && stats.lastError) {
      elErrorText.textContent = stats.lastError;
      showOnlyState(elError);
    } else if (total === 0) {
      showOnlyState(elEmpty);
    } else {
      showOnlyState(elSuccess);
    }
  }

  async function checkApiHealth(predictUrl) {
    try {
      const healthUrl = predictUrl.replace(/\/predict\/?$/, "/healthz");
      const res = await fetch(healthUrl, { method: "GET" });
      return res.ok;
    } catch (_err) {
      return false;
    }
  }

  async function refreshPopupState() {
    showOnlyState(elLoading);
    const apiUrl = elInputUrl.value.trim() || "http://127.0.0.1:8000/predict";
    const healthy = await checkApiHealth(apiUrl);

    if (!healthy) {
      elErrorText.textContent = `Không thể kết nối tới ${apiUrl}. Hãy chạy lệnh: python -m src.app.main`;
      showOnlyState(elError);
      return;
    }

    if (typeof chrome !== "undefined" && chrome.tabs && chrome.tabs.query) {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const activeTab = tabs && tabs[0];
        if (activeTab && activeTab.id && activeTab.url && activeTab.url.startsWith("http")) {
          chrome.tabs.sendMessage(activeTab.id, { type: "ADSHIELD_GET_TAB_STATUS" }, (tabRes) => {
            if (chrome.runtime && chrome.runtime.lastError) {
              triggerTabScan();
              return;
            }
            if (tabRes && tabRes.ok && tabRes.summary && tabRes.summary.totalScanned > 0) {
              renderStats(tabRes.summary);
            } else {
              triggerTabScan();
            }
          });
          return;
        }
        if (chrome.runtime && chrome.runtime.sendMessage) {
          chrome.runtime.sendMessage({ type: "ADSHIELD_GET_STATS" }, (response) => {
            if (chrome.runtime && chrome.runtime.lastError) {
              showOnlyState(elEmpty);
              return;
            }
            if (response && response.ok) {
              if (response.settings && response.settings.apiEndpoint) {
                elInputUrl.value = response.settings.apiEndpoint;
              }
              renderStats(response.stats);
            } else {
              showOnlyState(elEmpty);
            }
          });
        }
      });
    } else {
      showOnlyState(elEmpty);
    }
  }

  function triggerTabScan() {
    showOnlyState(elLoading);
    if (typeof chrome !== "undefined" && chrome.tabs && chrome.tabs.query) {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const activeTab = tabs && tabs[0];
        if (!activeTab || !activeTab.id || !activeTab.url || !activeTab.url.startsWith("http")) {
          refreshPopupState();
          return;
        }
        chrome.tabs.sendMessage(activeTab.id, { type: "ADSHIELD_SCAN_NOW" }, (res) => {
          if (chrome.runtime && chrome.runtime.lastError) {
            if (chrome.scripting && chrome.scripting.executeScript) {
              if (chrome.scripting.insertCSS) {
                chrome.scripting.insertCSS({ target: { tabId: activeTab.id }, files: ["content.css"] }, () => {
                  void (chrome.runtime && chrome.runtime.lastError);
                });
              }
              chrome.scripting.executeScript(
                { target: { tabId: activeTab.id }, files: ["content.js"] },
                () => {
                  void (chrome.runtime && chrome.runtime.lastError);
                  setTimeout(() => {
                    chrome.tabs.sendMessage(activeTab.id, { type: "ADSHIELD_SCAN_NOW" }, (res2) => {
                      void (chrome.runtime && chrome.runtime.lastError);
                      if (res2 && res2.ok && res2.summary) renderStats(res2.summary);
                    });
                  }, 700);
                }
              );
            } else {
              showOnlyState(elEmpty);
            }
            return;
          }
          if (res && res.ok && res.summary) {
            renderStats(res.summary);
          } else {
            showOnlyState(elEmpty);
          }
        });
      });
    } else {
      refreshPopupState();
    }
  }

  document.getElementById("btn-retry").addEventListener("click", refreshPopupState);
  document.getElementById("btn-scan-empty").addEventListener("click", triggerTabScan);
  document.getElementById("btn-rescan").addEventListener("click", triggerTabScan);

  document.getElementById("btn-open-demo").addEventListener("click", () => {
    const demoUrl = "http://127.0.0.1:8000/demo";
    if (typeof chrome !== "undefined" && chrome.tabs && chrome.tabs.create) {
      chrome.tabs.create({ url: demoUrl });
    } else {
      window.open(demoUrl, "_blank");
    }
  });

  document.getElementById("btn-save-config").addEventListener("click", () => {
    const newUrl = elInputUrl.value.trim() || "http://127.0.0.1:8000/predict";
    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({ apiEndpoint: newUrl }, () => {
        elSaveToast.classList.remove("hidden");
        setTimeout(() => elSaveToast.classList.add("hidden"), 2200);
        refreshPopupState();
      });
    }
  });

  refreshPopupState();
})();
