// ── 검색 토글 ─────────────────────────────
const searchToggle = document.getElementById('searchToggle');
const headerSearch = document.getElementById('headerSearch');
let searchOpen = false;

if (searchToggle && headerSearch) {
  searchToggle.addEventListener('click', () => {
    searchOpen = !searchOpen;
    headerSearch.style.display = searchOpen ? 'block' : 'none';
    if (searchOpen) headerSearch.querySelector('input').focus();
  });
  // ESC 닫기
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && searchOpen) {
      searchOpen = false;
      headerSearch.style.display = 'none';
    }
  });
}

// ── 모바일 네비게이션 토글 ────────────────
const navToggle = document.getElementById('navToggle');
const mainNav  = document.getElementById('main-nav');

if (navToggle && mainNav) {
  navToggle.addEventListener('click', () => {
    const isOpen = mainNav.classList.toggle('nav-open');
    navToggle.classList.toggle('is-open', isOpen);
  });
  // 메뉴 항목 클릭 시 닫기
  mainNav.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => mainNav.classList.remove('nav-open'));
  });
}

// ── 스크롤 헤더 그림자 ───────────────────
const header = document.querySelector('.site-header');
window.addEventListener('scroll', () => {
  header.classList.toggle('scrolled', window.scrollY > 10);
}, { passive: true });

// ── 페이드인 애니메이션 ──────────────────
if ('IntersectionObserver' in window) {
  const targets = document.querySelectorAll(
    '.poem-card, .poem-card-lg, .collection-item, .timeline-item, .gb-entry, .admin-stat-card'
  );
  const obs = new IntersectionObserver(entries => {
    entries.forEach((e, i) => {
      if (e.isIntersecting) {
        e.target.style.opacity = '1';
        e.target.style.transform = 'translateY(0)';
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.08 });

  targets.forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(18px)';
    el.style.transition = `opacity .5s ease ${i * 0.07}s, transform .5s ease ${i * 0.07}s`;
    obs.observe(el);
  });
}

// ── 히어로 스크롤 힌트 ──────────────────
const heroScroll = document.querySelector('.hero-scroll');
if (heroScroll) {
  window.addEventListener('scroll', () => {
    heroScroll.style.opacity = window.scrollY > 60 ? '0' : '1';
  }, { passive: true });
}
