/**
 * AIKTC Chatbot Launcher — Self‑Contained Embeddable Widget
 * ============================================================
 * Drop this script into any HTML page to add a cute robot icon
 * at the bottom‑right corner. On first visit (per session) it
 * shows a greeting popup. Clicking the icon or "Chat now" opens
 * the full chatbot page in a new tab.
 *
 * Usage:
 *   <script src="/chatbot-launcher.js"
 *           data-chatbot-url="https://your-deployment.com/chat"
 *           data-message="Hey! 👋 I'm your AIKTC assistant..."
 *           defer></script>
 *
 * Configuration (via data-* attributes on the script tag):
 *   data-chatbot-url  — URL to open when the user clicks (default: /chat)
 *   data-message      — Custom greeting message
 */
(function () {
  'use strict';

  // ── Configuration ─────────────────────────────────────────
  const script = document.currentScript;
  const CHATBOT_URL = (script && script.getAttribute('data-chatbot-url')) || '/chat';
  const MESSAGE = (script && script.getAttribute('data-message')) ||
    "Hey! 👋 I'm your AIKTC admission assistant. Ask me anything about cutoffs, fees, hostels, placements…";
  const POPUP_KEY = 'aiktc_chatbot_popup_shown';
  const POPUP_DELAY = 2000;     // ms before popup appears
  const POPUP_AUTO_DISMISS = 15000; // ms before popup auto‑hides

  // ── Inline CSS ────────────────────────────────────────────
  const STYLE = `
    /* ── Launcher Container ─────────────────────────────── */
    #aiktc-launcher-wrap {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 99999;
      font-family: 'Poppins', 'Segoe UI', system-ui, -apple-system, sans-serif;
    }

    /* ── Robot Button ───────────────────────────────────── */
    #aiktc-robot-btn {
      width: 64px;
      height: 64px;
      border-radius: 50%;
      border: none;
      cursor: pointer;
      background: linear-gradient(135deg, #1a6b3c 0%, #238b4e 50%, #2ca85e 100%);
      box-shadow: 0 4px 20px rgba(26, 107, 60, 0.4),
                  0 0 0 0 rgba(26, 107, 60, 0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
                  box-shadow 0.3s ease;
      animation: aiktc-pulse 2.5s infinite;
      position: relative;
      overflow: visible;
    }
    #aiktc-robot-btn:hover {
      transform: scale(1.12);
      box-shadow: 0 6px 28px rgba(26, 107, 60, 0.55),
                  0 0 0 0 rgba(26, 107, 60, 0);
      animation: none;
    }
    #aiktc-robot-btn:active {
      transform: scale(0.95);
    }
    #aiktc-robot-btn svg {
      width: 36px;
      height: 36px;
      filter: drop-shadow(0 1px 2px rgba(0,0,0,0.15));
    }
    @keyframes aiktc-pulse {
      0%   { box-shadow: 0 4px 20px rgba(26,107,60,0.4), 0 0 0 0 rgba(26,107,60,0.35); }
      70%  { box-shadow: 0 4px 20px rgba(26,107,60,0.4), 0 0 0 14px rgba(26,107,60,0); }
      100% { box-shadow: 0 4px 20px rgba(26,107,60,0.4), 0 0 0 0 rgba(26,107,60,0); }
    }

    /* ── Notification dot ───────────────────────────────── */
    #aiktc-robot-btn::after {
      content: '';
      position: absolute;
      top: 2px;
      right: 2px;
      width: 14px;
      height: 14px;
      background: #ef4444;
      border: 2px solid #fff;
      border-radius: 50%;
      animation: aiktc-dot-bounce 1.5s infinite;
    }
    #aiktc-robot-btn.aiktc-seen::after {
      display: none;
    }
    @keyframes aiktc-dot-bounce {
      0%, 100% { transform: scale(1); }
      50%      { transform: scale(1.25); }
    }

    /* ── Greeting Popup ─────────────────────────────────── */
    #aiktc-popup {
      position: absolute;
      bottom: 78px;
      right: 0;
      width: 300px;
      background: #ffffff;
      border-radius: 16px;
      box-shadow: 0 12px 40px rgba(0,0,0,0.15),
                  0 4px 12px rgba(0,0,0,0.08);
      padding: 0;
      opacity: 0;
      transform: translateY(12px) scale(0.95);
      transition: opacity 0.35s ease, transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
      pointer-events: none;
      overflow: hidden;
    }
    #aiktc-popup.aiktc-visible {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: auto;
    }

    /* Popup arrow */
    #aiktc-popup::after {
      content: '';
      position: absolute;
      bottom: -8px;
      right: 22px;
      width: 16px;
      height: 16px;
      background: #fff;
      transform: rotate(45deg);
      box-shadow: 4px 4px 8px rgba(0,0,0,0.06);
    }

    /* Popup header strip */
    .aiktc-popup-header {
      background: linear-gradient(135deg, #1a6b3c, #2ca85e);
      padding: 14px 16px 12px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .aiktc-popup-header svg {
      width: 28px;
      height: 28px;
      flex-shrink: 0;
    }
    .aiktc-popup-header span {
      color: #fff;
      font-weight: 600;
      font-size: 14px;
      line-height: 1.3;
    }

    /* Popup body */
    .aiktc-popup-body {
      padding: 16px;
    }
    .aiktc-popup-body p {
      margin: 0 0 14px;
      font-size: 13.5px;
      color: #374151;
      line-height: 1.55;
    }

    /* Chat now button */
    .aiktc-chat-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: linear-gradient(135deg, #1a6b3c, #238b4e);
      color: #fff;
      border: none;
      padding: 10px 20px;
      border-radius: 24px;
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.25s ease;
      box-shadow: 0 2px 8px rgba(26, 107, 60, 0.3);
    }
    .aiktc-chat-btn:hover {
      background: linear-gradient(135deg, #155a32, #1a6b3c);
      box-shadow: 0 4px 14px rgba(26, 107, 60, 0.45);
      transform: translateY(-1px);
    }
    .aiktc-chat-btn svg {
      width: 16px;
      height: 16px;
    }

    /* Close button */
    .aiktc-close-btn {
      position: absolute;
      top: 10px;
      right: 10px;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      border: none;
      background: rgba(255,255,255,0.25);
      color: #fff;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: 700;
      transition: background 0.2s;
      line-height: 1;
      padding: 0;
    }
    .aiktc-close-btn:hover {
      background: rgba(255,255,255,0.45);
    }

    /* ── Responsive ─────────────────────────────────────── */
    @media (max-width: 420px) {
      #aiktc-launcher-wrap {
        bottom: 16px;
        right: 16px;
      }
      #aiktc-popup {
        width: 260px;
        right: -8px;
      }
      #aiktc-robot-btn {
        width: 56px;
        height: 56px;
      }
      #aiktc-robot-btn svg {
        width: 30px;
        height: 30px;
      }
    }
  `;

  // ── Robot SVG (cute face) ─────────────────────────────────
  const ROBOT_SVG = `
    <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <!-- Antenna -->
      <line x1="50" y1="12" x2="50" y2="24" stroke="#fff" stroke-width="3" stroke-linecap="round"/>
      <circle cx="50" cy="10" r="4" fill="#FFD93D"/>
      <!-- Head -->
      <rect x="20" y="24" width="60" height="50" rx="14" fill="#fff"/>
      <!-- Eyes -->
      <circle cx="38" cy="46" r="7" fill="#1a6b3c">
        <animate attributeName="ry" values="7;1;7" dur="3.5s" repeatCount="indefinite" begin="2s"/>
      </circle>
      <circle cx="62" cy="46" r="7" fill="#1a6b3c">
        <animate attributeName="ry" values="7;1;7" dur="3.5s" repeatCount="indefinite" begin="2s"/>
      </circle>
      <!-- Eye shine -->
      <circle cx="35" cy="43" r="2.5" fill="#fff" opacity="0.85"/>
      <circle cx="59" cy="43" r="2.5" fill="#fff" opacity="0.85"/>
      <!-- Smile -->
      <path d="M38 58 Q50 68 62 58" stroke="#1a6b3c" stroke-width="2.5" stroke-linecap="round" fill="none"/>
      <!-- Cheeks -->
      <circle cx="28" cy="55" r="4" fill="#FFD93D" opacity="0.5"/>
      <circle cx="72" cy="55" r="4" fill="#FFD93D" opacity="0.5"/>
      <!-- Ears -->
      <rect x="12" y="40" width="8" height="16" rx="4" fill="#fff" opacity="0.7"/>
      <rect x="80" y="40" width="8" height="16" rx="4" fill="#fff" opacity="0.7"/>
      <!-- Body hint -->
      <rect x="35" y="74" width="30" height="14" rx="7" fill="#fff" opacity="0.6"/>
    </svg>`;

  // ── Small robot for popup header ──────────────────────────
  const ROBOT_SMALL = `
    <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="10" r="4" fill="#FFD93D"/>
      <line x1="50" y1="12" x2="50" y2="24" stroke="#fff" stroke-width="3" stroke-linecap="round"/>
      <rect x="20" y="24" width="60" height="50" rx="14" fill="#fff"/>
      <circle cx="38" cy="46" r="7" fill="#1a6b3c"/>
      <circle cx="62" cy="46" r="7" fill="#1a6b3c"/>
      <circle cx="35" cy="43" r="2.5" fill="#fff" opacity="0.85"/>
      <circle cx="59" cy="43" r="2.5" fill="#fff" opacity="0.85"/>
      <path d="M38 58 Q50 68 62 58" stroke="#1a6b3c" stroke-width="2.5" stroke-linecap="round" fill="none"/>
    </svg>`;

  // ── Arrow icon for chat button ────────────────────────────
  const ARROW_SVG = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>`;

  // ── Build DOM ─────────────────────────────────────────────
  function init() {
    // Inject styles
    const styleEl = document.createElement('style');
    styleEl.textContent = STYLE;
    document.head.appendChild(styleEl);

    // Wrapper
    const wrap = document.createElement('div');
    wrap.id = 'aiktc-launcher-wrap';

    // Popup
    const popup = document.createElement('div');
    popup.id = 'aiktc-popup';
    popup.innerHTML = `
      <div class="aiktc-popup-header">
        ${ROBOT_SMALL}
        <span>AIKTC Assistant</span>
        <button class="aiktc-close-btn" aria-label="Close" title="Close">✕</button>
      </div>
      <div class="aiktc-popup-body">
        <p>${MESSAGE}</p>
        <button class="aiktc-chat-btn" id="aiktc-chat-now">
          Chat now ${ARROW_SVG}
        </button>
      </div>
    `;

    // Robot button
    const btn = document.createElement('button');
    btn.id = 'aiktc-robot-btn';
    btn.setAttribute('aria-label', 'Open AIKTC Chatbot');
    btn.setAttribute('title', 'Chat with AIKTC Assistant');
    btn.innerHTML = ROBOT_SVG;

    wrap.appendChild(popup);
    wrap.appendChild(btn);
    document.body.appendChild(wrap);

    // ── Event Handlers ────────────────────────────────────
    // Robot icon click → open chatbot
    btn.addEventListener('click', function () {
      window.open(CHATBOT_URL, '_blank');
    });

    // "Chat now" button click → open chatbot
    popup.querySelector('#aiktc-chat-now').addEventListener('click', function (e) {
      e.stopPropagation();
      window.open(CHATBOT_URL, '_blank');
      hidePopup();
    });

    // Close button
    popup.querySelector('.aiktc-close-btn').addEventListener('click', function (e) {
      e.stopPropagation();
      hidePopup();
    });

    // ── Popup Logic (session‑based) ───────────────────────
    let autoDismissTimer = null;

    function showPopup() {
      popup.classList.add('aiktc-visible');
      btn.classList.add('aiktc-seen');
      autoDismissTimer = setTimeout(hidePopup, POPUP_AUTO_DISMISS);
    }

    function hidePopup() {
      popup.classList.remove('aiktc-visible');
      if (autoDismissTimer) {
        clearTimeout(autoDismissTimer);
        autoDismissTimer = null;
      }
    }

    // Show popup only once per session
    if (!sessionStorage.getItem(POPUP_KEY)) {
      setTimeout(showPopup, POPUP_DELAY);
      sessionStorage.setItem(POPUP_KEY, '1');
    } else {
      btn.classList.add('aiktc-seen');
    }

    // ── Public API ────────────────────────────────────────
    window.ChatbotLauncher = {
      show: showPopup,
      hide: hidePopup,
      open: function () { window.open(CHATBOT_URL, '_blank'); }
    };
  }

  // ── Bootstrap ─────────────────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
