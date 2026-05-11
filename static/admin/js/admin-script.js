// ==================== SIDEBAR & MOBILE ====================
let sidebarCollapsed = false;

function toggleSidebar() {
  if (window.innerWidth <= 900) {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const isOpen = sidebar.classList.contains('mobile-open');
    if (isOpen) {
      sidebar.classList.remove('mobile-open');
      overlay.classList.remove('visible');
      document.body.style.overflow = '';
    } else {
      sidebar.classList.add('mobile-open');
      overlay.classList.add('visible');
      document.body.style.overflow = 'hidden';
    }
  } else {
    sidebarCollapsed = !sidebarCollapsed;
    document.getElementById('sidebar').classList.toggle('collapsed', sidebarCollapsed);
    document.getElementById('main').classList.toggle('expanded', sidebarCollapsed);
  }
}

function closeSidebarMobile() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (sidebar) sidebar.classList.remove('mobile-open');
  if (overlay) overlay.classList.remove('visible');
  document.body.style.overflow = '';
}

// Make sidebar nav items clickable and close sidebar after click on mobile
document.addEventListener('DOMContentLoaded', function () {
  // Sidebar nav-item click closes sidebar on mobile
  document.querySelectorAll('.sidebar .nav-item').forEach(function (item) {
    item.addEventListener('click', function (e) {
      if (window.innerWidth <= 900) {
        // Allow link navigation first, then close
        setTimeout(closeSidebarMobile, 80);
      }
    });
  });

  // Overlay click closes sidebar
  const overlay = document.getElementById('sidebarOverlay');
  if (overlay) {
    overlay.addEventListener('click', closeSidebarMobile);
  }

  // Touch swipe left on sidebar closes it
  let touchStartX = 0;
  const sidebar = document.getElementById('sidebar');
  if (sidebar) {
    sidebar.addEventListener('touchstart', function (e) {
      touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    sidebar.addEventListener('touchend', function (e) {
      const diff = touchStartX - e.changedTouches[0].screenX;
      if (diff > 60) { closeSidebarMobile(); }
    }, { passive: true });
  }
});

// ==================== THEME TOGGLE ====================
function toggleTheme() {
  const html = document.documentElement;
  const dark = html.getAttribute('data-theme') === 'dark';
  const newTheme = dark ? 'light' : 'dark';
  html.setAttribute('data-theme', newTheme);
  localStorage.setItem('admin-theme', newTheme);
}

(function () {
  const savedTheme = localStorage.getItem('admin-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
})();

// ==================== MODALS ====================
function openModal(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.remove('open');
  // Only restore scroll if no other modals are open
  if (!document.querySelector('.modal-overlay.open')) {
    document.body.style.overflow = '';
  }
}

document.addEventListener('click', function (e) {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
    if (!document.querySelector('.modal-overlay.open')) {
      document.body.style.overflow = '';
    }
  }
});

// ==================== TOASTS ====================
function showToast(type, title, msg) {
  const icons = {
    success: 'bi-check-circle-fill',
    error: 'bi-x-circle-fill',
    info: 'bi-info-circle-fill',
    warning: 'bi-exclamation-triangle-fill'
  };
  const t = document.createElement('div');
  t.className = 'toast';
  t.innerHTML = `
    <div class="toast-icon ${type}"><i class="bi ${icons[type] || icons.info}"></i></div>
    <div class="toast-body"><div class="toast-title">${title}</div><div class="toast-msg">${msg}</div></div>
    <div class="toast-close" onclick="this.parentElement.remove()"><i class="bi bi-x-lg"></i></div>
  `;
  const container = document.getElementById('toastContainer');
  if (container) container.appendChild(t);
  setTimeout(function () { if (t && t.parentNode) t.remove(); }, 4500);
}

// ==================== NOTIFICATION PANEL ====================
function toggleNotif() {
  document.getElementById('notifPanel').classList.toggle('open');
}

document.addEventListener('click', function (e) {
  const panel = document.getElementById('notifPanel');
  if (panel && panel.classList.contains('open') &&
    !panel.contains(e.target) && !e.target.closest('.topbar-btn')) {
    panel.classList.remove('open');
  }
});

// ==================== FULLSCREEN ====================
function toggleFullscreen() {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen().catch(function () {});
  else document.exitFullscreen();
}

// ==================== SETTINGS TABS ====================
function settingsTab(el, targetId) {
  document.querySelectorAll('.settings-nav-btn').forEach(function (btn) {
    btn.classList.remove('active');
  });
  el.classList.add('active');
  document.querySelectorAll('.settings-panel').forEach(function (panel) {
    panel.style.display = 'none';
  });
  const target = document.getElementById(targetId);
  if (target) target.style.display = 'block';
}

// ==================== IMAGE PREVIEW ====================
function previewImage(input, previewId) {
  const preview = document.getElementById(previewId);
  if (!preview) return;
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = function (e) {
      preview.src = e.target.result;
      preview.style.display = 'block';
    };
    reader.readAsDataURL(input.files[0]);
  } else {
    preview.style.display = 'none';
  }
}

function previewMultipleImages(input) {
  const container = document.getElementById('multiplePreview');
  if (!container) return;
  container.innerHTML = '';
  if (input.files) {
    for (let i = 0; i < Math.min(input.files.length, 5); i++) {
      const file = input.files[i];
      const reader = new FileReader();
      reader.onload = function (e) {
        const img = document.createElement('img');
        img.src = e.target.result;
        img.style.cssText = 'width:100%;height:100px;object-fit:cover;border-radius:8px;border:2px solid var(--divider);';
        container.appendChild(img);
      };
      reader.readAsDataURL(file);
    }
  }
}

// ==================== TOGGLE SWITCH (settings) ====================
document.addEventListener('click', function (e) {
  if (e.target.classList.contains('toggle-switch')) {
    e.target.classList.toggle('on');
  }
});

// ==================== DELETE CONFIRMATION MODAL ====================
let deleteAction = { form: null, url: null };


function showDeleteConfirmFromEl(button) {
  const form = button ? button.closest('form') : null;
  if (!form) return;
  let itemName = form.getAttribute('data-item-name') || 'this item';
  try { itemName = JSON.parse(itemName); } catch (e) {}
  showDeleteConfirm(itemName, form);
}

function showDeleteConfirm(itemName, formElement) {
  deleteAction.form = formElement;
  deleteAction.url = null;
  const nameEl = document.getElementById('deleteItemName');
  if (nameEl) nameEl.textContent = itemName;
  openModal('deleteConfirmModal');
}

function showDeleteConfirmWithURL(itemName, url) {
  deleteAction.form = null;
  deleteAction.url = url;
  const nameEl = document.getElementById('deleteItemName');
  if (nameEl) nameEl.textContent = itemName;
  openModal('deleteConfirmModal');
}

function performDelete() {
  if (deleteAction.form) {
    // Close modal first to avoid UI confusion
    closeModal('deleteConfirmModal');
    setTimeout(function () {
      deleteAction.form.submit();
    }, 120);
  } else if (deleteAction.url) {
    closeModal('deleteConfirmModal');
    window.location.href = deleteAction.url;
  }
}

function cancelDelete() {
  closeModal('deleteConfirmModal');
  deleteAction.form = null;
  deleteAction.url = null;
}