/* ═══════════════════════════════════════════════════════════
   J&J SOFT AROMA — MAIN JAVASCRIPT
   ═══════════════════════════════════════════════════════════ */

/* ── PAGE LOADER ────────────────────────────────────────────── */
(function () {
  const loader = document.getElementById('page-loader');
  if (!loader) return;
  window.addEventListener('load', () => {
    setTimeout(() => loader.classList.add('hidden'), 400);
  });
  // Fallback
  setTimeout(() => loader && loader.classList.add('hidden'), 2800);
})();

/* ── NAVBAR SCROLL CLASS ─────────────────────────────────────── */
(function () {
  const nav = document.getElementById('mainNav');
  if (!nav) return;
  const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 30);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();

/* ── BOTTOM NAV: ACTIVE STATE ───────────────────────────────── */
(function () {
  const path   = window.location.pathname;
  const items  = document.querySelectorAll('.bn-item[data-page]');
  items.forEach(item => {
    const page = item.getAttribute('data-page');
    if (
      (page === '/'        && (path === '/' || path === ''))    ||
      (page !== '/'        && path.startsWith(page))
    ) {
      item.classList.add('active');
    }
  });
})();

/* ── MOBILE DROPDOWN MENUS ─────────────────────────────────── */
(function () {
  // Setup a toggle for any btn/dropdown pair
  function setupDropdown(btnId, dropdownId) {
    const btn = document.getElementById(btnId);
    const dropdown = document.getElementById(dropdownId);
    if (!btn || !dropdown) return;

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.classList.toggle('open');
    });

    dropdown.querySelectorAll('.bn-dropdown-item').forEach(item => {
      item.addEventListener('click', () => dropdown.classList.remove('open'));
    });

    document.addEventListener('click', (e) => {
      if (!btn.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove('open');
      }
    });
  }

  // Top-bar hamburger menu (visible on mobile, above lg)
  setupDropdown('topMobileMenuBtn', 'topMobileMenuDropdown');
  // Bottom-nav "More" dropdown
  setupDropdown('mobileMoreBtn', 'mobileMoreDropdown');
})();

/* ── FADE-IN ON SCROLL ───────────────────────────────────────── */
(function () {
  const checkFade = () => {
    document.querySelectorAll('.fade-in:not(.visible)').forEach(el => {
      if (el.getBoundingClientRect().top < window.innerHeight - 55)
        el.classList.add('visible');
    });
  };
  window.addEventListener('scroll', checkFade, { passive: true });
  checkFade();
})();

/* ── AUTO-DISMISS FLASH ALERTS ──────────────────────────────── */
(function () {
  document.querySelectorAll('.alert-dismissible').forEach(alert => {
    setTimeout(() => {
      if (alert.parentNode) alert.remove();
    }, 5000);
  });
})();

/* ── HERO SLIDER ────────────────────────────────────────────── */
(function () {
  const slider = document.getElementById('heroSlider');
  if (!slider) return;

  const slides = slider.querySelectorAll('.slide');
  const dots   = slider.querySelectorAll('.dot');
  let current  = 0;
  let timer;

  function goTo(n) {
    slides[current].classList.remove('active');
    dots[current] && dots[current].classList.remove('active');
    current = (n + slides.length) % slides.length;
    slides[current].classList.add('active');
    dots[current] && dots[current].classList.add('active');
  }

  function next() { goTo(current + 1); }
  function prev() { goTo(current - 1); }
  function start() { timer = setInterval(next, 5200); }
  function stop()  { clearInterval(timer); }

  // Expose for inline onclick
  window.sliderNext = () => { stop(); next(); start(); };
  window.sliderPrev = () => { stop(); prev(); start(); };
  window.sliderGoTo = (n) => { stop(); goTo(n); start(); };

  // Dots
  dots.forEach((dot, i) => dot.addEventListener('click', () => window.sliderGoTo(i)));

  // Touch swipe
  let touchX = 0;
  slider.addEventListener('touchstart', e => { touchX = e.touches[0].clientX; }, { passive: true });
  slider.addEventListener('touchend',   e => {
    const dx = e.changedTouches[0].clientX - touchX;
    if (Math.abs(dx) > 50) dx < 0 ? window.sliderNext() : window.sliderPrev();
  });

  start();
})();

/* ── QTY INPUT (product detail) ─────────────────────────────── */
function changeQty(delta) {
  const input = document.getElementById('qty');
  if (!input) return;
  const max = parseInt(input.max) || 999;
  let val = parseInt(input.value) + delta;
  if (val < 1)   val = 1;
  if (val > max) val = max;
  input.value = val;
}

/* ── PAYMENT OPTION SELECTOR ────────────────────────────────── */
document.addEventListener('click', e => {
  const opt = e.target.closest('.payment-option');
  if (!opt) return;
  const group = opt.closest('.payment-group') || opt.parentElement;
  group.querySelectorAll('.payment-option').forEach(o => o.classList.remove('active'));
  opt.classList.add('active');
  const radio = opt.querySelector('input[type=radio]');
  if (radio) radio.checked = true;
});

/* ── PRICE RANGE LABEL UPDATE ───────────────────────────────── */
function updatePrice(el) {
  const label = document.getElementById('priceMax');
  if (label) label.textContent = 'UGX ' + parseInt(el.value).toLocaleString();
}

/* ── NEWSLETTER ─────────────────────────────────────────────── */
function subscribeNewsletter() {
  const input = document.querySelector('.newsletter-input');
  if (!input || !input.value.includes('@')) {
    showToast('Please enter a valid email address.');
    return;
  }
  showToast('You\'re subscribed! Welcome to the J&J family 🎉');
  input.value = '';
}

/* ── CONTACT FORM ───────────────────────────────────────────── */
function sendContactMessage() {
  showToast('Message sent! We\'ll reply within 24 hours 📩');
}

/* ── TOAST NOTIFICATION (5 VARIANTS) ────────────────────────── */
let _toastTimer;
function showToast(msg, type = 'success') {
  // Toast type configuration
  const toastConfig = {
    success: { icon: 'bi-check-circle-fill', color: '#4CAF50', title: 'Success' },
    error:   { icon: 'bi-x-circle-fill', color: '#f44336', title: 'Error' },
    info:    { icon: 'bi-info-circle-fill', color: '#2196F3', title: 'Info' },
    warning: { icon: 'bi-exclamation-triangle-fill', color: '#ff9800', title: 'Warning' },
    cart:    { icon: 'bi-bag-check-fill', color: '#1a3a52', title: 'Added to Cart' }
  };
  
  const config = toastConfig[type] || toastConfig['success'];
  
  // Create toast container if it doesn't exist
  let container = document.getElementById('siteToastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'siteToastContainer';
    container.style.cssText = `
      position: fixed;
      top: 92px;
      right: 22px;
      z-index: 10020;
      display: flex;
      flex-direction: column;
      gap: 14px;
      pointer-events: none;
      width: min(420px, calc(100vw - 32px));
    `;
    document.body.appendChild(container);
  }
  
  // Create individual toast
  const toast = document.createElement('div');
  toast.className = 'site-toast';
  toast.style.cssText = `
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 20px;
    background: white;
    border-radius: 18px;
    box-shadow: 0 18px 40px rgba(10, 32, 51, 0.18);
    border-left: 4px solid ${config.color};
    animation: slideInToast 0.3s ease-out;
    pointer-events: auto;
    min-width: 100%;
    font-size: 0.98rem;
    backdrop-filter: blur(10px);
  `;
  
  const iconEl = document.createElement('i');
  iconEl.className = `bi ${config.icon}`;
  iconEl.style.cssText = `
    color: ${config.color};
    font-size: 1.45rem;
    flex-shrink: 0;
  `;
  
  const textEl = document.createElement('div');
  textEl.style.cssText = `flex: 1; color: #243746; line-height: 1.45; font-weight: 500;`;
  textEl.textContent = msg;
  
  const closeBtn = document.createElement('button');
  closeBtn.innerHTML = '<i class="bi bi-x-lg"></i>';
  closeBtn.style.cssText = `
    background: none;
    border: none;
    color: #8c96a0;
    cursor: pointer;
    padding: 0;
    font-size: 1rem;
    flex-shrink: 0;
  `;
  closeBtn.onclick = () => removeToast(toast);
  
  toast.appendChild(iconEl);
  toast.appendChild(textEl);
  toast.appendChild(closeBtn);
  container.appendChild(toast);
  
  // Auto-dismiss after a longer pause so the message stays visible
  const dismissTimer = setTimeout(() => removeToast(toast), 7000);
  
  // Clear timer on hover
  toast.addEventListener('mouseenter', () => clearTimeout(dismissTimer));
  toast.addEventListener('mouseleave', () => {
    setTimeout(() => removeToast(toast), 7000);
  });
}

function removeToast(toastEl) {
  if (!toastEl) return;
  toastEl.style.animation = 'slideOutToast 0.2s ease-in forwards';
  setTimeout(() => {
    if (toastEl.parentNode) toastEl.parentNode.removeChild(toastEl);
  }, 200);
}

/* Add toast animations */
if (!document.getElementById('toastStyles')) {
  const style = document.createElement('style');
  style.id = 'toastStyles';
  style.textContent = `
    @keyframes slideInToast {
      from { transform: translateX(120px); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutToast {
      from { transform: translateX(0); opacity: 1; }
      to { transform: translateX(120px); opacity: 0; }
    }
  `;
  document.head.appendChild(style);
}

/* ── PRODUCT IMAGE THUMB SWITCHER ───────────────────────────── */
function changeThumb(el, src) {
  document.querySelectorAll('.thumb').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  const main = document.getElementById('mainProductImg');
  if (main) {
    main.style.opacity = '0';
    setTimeout(() => {
      main.src = src;
      main.style.opacity = '1';
    }, 200);
  }
}

/* ── ACCORDION (FAQ) ─────────────────────────────────────────── */
// Bootstrap handles this, but ensure smooth custom styling
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.accordion-button').forEach(btn => {
    btn.addEventListener('click', () => {
      // Minor re-style pass — Bootstrap handles open/collapse
    });
  });
});

/* ── CART: live cart count update (for any page with AJAX add-to-cart) ─ */
function updateCartBadge(count) {
  document.querySelectorAll('.cart-count-badge, .bn-cart-badge').forEach(el => {
    el.textContent = count;
    el.style.display = count > 0 ? 'flex' : 'none';
  });
}

/* ── DYNAMIC NAVBAR HEIGHT ADJUSTMENT ─────────────────────── */
(function () {
  const nav = document.getElementById('mainNav');
  const main = document.querySelector('main');
  if (!nav || !main) return;

  const adjust = () => {
    const h = nav.offsetHeight || 92;
    // apply as inline style to ensure immediate effect
    main.style.paddingTop = (h + 18) + 'px';
    main.style.scrollPaddingTop = (h + 18) + 'px';
  };

  window.addEventListener('resize', adjust);
  window.addEventListener('load', adjust);
  // run immediately
  adjust();
})();
