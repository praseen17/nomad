/* NOMAD Core JavaScript */
'use strict';

// ── Custom Cursor ──
const initCursor = () => {
  if (!document.querySelector('.cursor-dot')) return;
  const dot = document.querySelector('.cursor-dot');
  const ring = document.querySelector('.cursor-ring');
  let mx = 0, my = 0, rx = 0, ry = 0;
  document.addEventListener('mousemove', e => {
    mx = e.clientX; my = e.clientY;
    dot.style.left = mx + 'px'; dot.style.top = my + 'px';
  });
  const animateRing = () => {
    rx += (mx - rx) * 0.12; ry += (my - ry) * 0.12;
    ring.style.left = rx + 'px'; ring.style.top = ry + 'px';
    requestAnimationFrame(animateRing);
  };
  animateRing();
  document.addEventListener('mousedown', () => {
    dot.style.width = '6px'; dot.style.height = '6px';
    ring.style.width = '48px'; ring.style.height = '48px';
  });
  document.addEventListener('mouseup', () => {
    dot.style.width = '10px'; dot.style.height = '10px';
    ring.style.width = '36px'; ring.style.height = '36px';
  });
};

// ── Scroll Reveal ──
const initReveal = () => {
  const els = document.querySelectorAll('.reveal');
  if (!els.length) return;
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); } });
  }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });
  els.forEach(el => obs.observe(el));
};

// ── Counter Animation ──
const animateCounter = (el, target, duration = 1800) => {
  let start = null;
  const prefix = el.dataset.prefix || '';
  const suffix = el.dataset.suffix || '';
  const step = ts => {
    if (!start) start = ts;
    const progress = Math.min((ts - start) / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    const value = Math.floor(ease * target);
    el.textContent = prefix + value.toLocaleString('en-IN') + suffix;
    if (progress < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
};

const initCounters = () => {
  const counters = document.querySelectorAll('[data-count]');
  if (!counters.length) return;
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        animateCounter(e.target, parseInt(e.target.dataset.count));
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.5 });
  counters.forEach(c => obs.observe(c));
};

// ── Role Tabs ──
const initRoleTabs = () => {
  const tabs = document.querySelectorAll('.role-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      document.querySelectorAll('.role-panel').forEach(p => p.classList.remove('active'));
      const target = document.getElementById(tab.dataset.panel);
      if (target) target.classList.add('active');
    });
  });
};

// ── Bento Tile Mouse Glow ──
const initBentoGlow = () => {
  document.querySelectorAll('.bento-tile').forEach(tile => {
    tile.addEventListener('mousemove', e => {
      const rect = tile.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      tile.style.setProperty('--mx', x + '%');
      tile.style.setProperty('--my', y + '%');
    });
  });
};

// ── Modals ──
const openModal = (id) => {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.add('open');
  modal.querySelector('[data-focus]')?.focus();
  document.body.style.overflow = 'hidden';
};
const closeModal = (id) => {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.remove('open');
  document.body.style.overflow = '';
};

document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('open');
    document.body.style.overflow = '';
  }
  if (e.target.closest('[data-modal-open]')) {
    openModal(e.target.closest('[data-modal-open]').dataset.modalOpen);
  }
  if (e.target.closest('[data-modal-close]')) {
    closeModal(e.target.closest('[data-modal-close]').dataset.modalClose);
  }
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop.open').forEach(m => {
      m.classList.remove('open');
      document.body.style.overflow = '';
    });
  }
});

// ── Chart.js Theme Defaults ──
const initChartDefaults = () => {
  if (!window.Chart) return;
  Chart.defaults.color = '#9A9080';
  Chart.defaults.borderColor = '#2C2820';
  Chart.defaults.font.family = "'Instrument Sans', sans-serif";
  Chart.defaults.font.size = 12;
};

// ── Stat Cards Count Up on Dashboard Load ──
const initStatCards = () => {
  document.querySelectorAll('.stat-value[data-count]').forEach(el => {
    animateCounter(el, parseInt(el.dataset.count), 1500);
  });
};

// ── Table Status Auto-Refresh (Dashboard) ──
const initTableRefresh = () => {
  const grid = document.getElementById('live-table-grid');
  if (!grid) return;
  setInterval(() => {
    // In a full implementation, this would poll an API endpoint
    // For now, just a placeholder
  }, 30000);
};

// ── Nav Scroll Effect ──
const initNavScroll = () => {
  const nav = document.querySelector('.nav-bar');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      nav.style.background = 'rgba(14,12,10,0.95)';
      nav.style.borderBottom = '1px solid #2C2820';
    } else {
      nav.style.background = 'linear-gradient(to bottom, rgba(14,12,10,0.9), transparent)';
      nav.style.borderBottom = 'none';
    }
  }, { passive: true });
};

// ── Category Filter (Customer Menu) ──
const initCategoryFilter = () => {
  const pills = document.querySelectorAll('.category-pill');
  if (!pills.length) return;
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const target = pill.dataset.category;
      document.querySelectorAll('.menu-section').forEach(section => {
        if (target === 'all' || section.dataset.category === target) {
          section.style.display = '';
        } else {
          section.style.display = 'none';
        }
      });
    });
  });
};

// ── Dish Search ──
const initMenuSearch = () => {
  const searchInput = document.getElementById('menu-search');
  if (!searchInput) return;
  searchInput.addEventListener('input', () => {
    const q = searchInput.value.toLowerCase();
    document.querySelectorAll('.dish-card').forEach(card => {
      const name = card.querySelector('.dish-name')?.textContent.toLowerCase() || '';
      card.style.display = name.includes(q) ? '' : 'none';
    });
  });
};

// ── QR Copy Link ──
const copyMenuLink = (url) => {
  navigator.clipboard.writeText(url).then(() => {
    showToast('Menu link copied!', 'success');
  }).catch(() => {
    showToast('Copy failed. Try manually.', 'error');
  });
};

// ── Toast Utility ──
const showToast = (message, type = 'info') => {
  const container = document.getElementById('toast-container') || (() => {
    const c = document.createElement('div');
    c.className = 'toast-container';
    c.id = 'toast-container';
    document.body.appendChild(c);
    return c;
  })();
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<div class="toast-content">${message}</div><button class="toast-close" onclick="this.parentElement.remove()">✕</button>`;
  container.appendChild(toast);
  setTimeout(() => { toast.style.animation = 'toastSlideOut 0.4s ease forwards'; setTimeout(() => toast.remove(), 400); }, 4000);
};

// ── Password Toggle ──
const initPasswordToggle = () => {
  document.querySelectorAll('[data-toggle-password]').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.querySelector(btn.dataset.togglePassword);
      if (!input) return;
      input.type = input.type === 'password' ? 'text' : 'password';
      btn.querySelector('i')?.setAttribute('data-lucide', input.type === 'password' ? 'eye' : 'eye-off');
      if (window.lucide) lucide.createIcons();
    });
  });
};

// ── Form Submit Loading State ──
document.addEventListener('submit', e => {
  const form = e.target;
  const btn = form.querySelector('[type=submit]');
  if (!btn || btn.dataset.noLoading) return;
  const originalHTML = btn.innerHTML;
  btn.innerHTML = '<div class="loading-spinner"></div>';
  btn.disabled = true;
  setTimeout(() => { btn.innerHTML = originalHTML; btn.disabled = false; }, 8000);
});

// ── Sidebar Active Link ──
const initSidebarActive = () => {
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar-item').forEach(item => {
    if (item.getAttribute('href') === path || (item.getAttribute('href') !== '/' && path.startsWith(item.getAttribute('href')))) {
      item.classList.add('active');
    }
  });
};

// ── Hero Text Animation ──
const initHeroText = () => {
  const title = document.querySelector('.hero-title');
  if (!title || title.dataset.animated) return;
  title.dataset.animated = '1';
};

// ── Init All ──
document.addEventListener('DOMContentLoaded', () => {
  initCursor();
  initReveal();
  initCounters();
  initRoleTabs();
  initBentoGlow();
  initChartDefaults();
  initStatCards();
  initNavScroll();
  initCategoryFilter();
  initMenuSearch();
  initPasswordToggle();
  initSidebarActive();
  initHeroText();
  initTableRefresh();
});

// Expose utilities globally
window.NOMAD = { openModal, closeModal, showToast, copyMenuLink, animateCounter };
