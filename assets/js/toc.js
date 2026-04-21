(function () {
  'use strict';

  // ── Reading progress bar ─────────────────────────────────────────────────
  function initProgress() {
    var bar     = document.getElementById('reading-progress');
    var article = document.querySelector('.blog-post');
    if (!bar || !article) return;

    var navbar = document.querySelector('.navbar-custom');

    function update() {
      if (navbar) bar.style.top = navbar.getBoundingClientRect().bottom + 'px';
      var articleTop    = article.getBoundingClientRect().top + window.scrollY;
      var articleHeight = article.offsetHeight;
      var scrolled      = window.scrollY - articleTop;
      var pct           = Math.max(0, Math.min(100, (scrolled / articleHeight) * 100));
      bar.style.width   = pct + '%';
    }

    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  // ── Table of Contents ────────────────────────────────────────────────────
  function buildToc() {
    var article    = document.querySelector('.blog-post');
    var tocNav     = document.getElementById('toc-nav');
    var tocSidebar = document.getElementById('toc-sidebar');
    if (!article || !tocNav || !tocSidebar) return;

    var headings = Array.from(article.querySelectorAll('h2, h3'));
    if (headings.length < 2) { tocSidebar.style.display = 'none'; return; }

    // Ensure stable IDs
    headings.forEach(function (h, i) {
      if (!h.id) {
        h.id = h.textContent.toLowerCase()
          .replace(/[^\w\s-]/g, '').trim()
          .replace(/\s+/g, '-') + '-' + i;
      }
    });

    // Build list
    var ul = document.createElement('ul');
    ul.className = 'toc-list';
    headings.forEach(function (h) {
      var li = document.createElement('li');
      li.className = 'toc-item toc-item--' + h.tagName.toLowerCase();
      var a = document.createElement('a');
      a.href           = '#' + h.id;
      a.className      = 'toc-link';
      a.textContent    = h.textContent.trim();
      a.dataset.target = h.id;
      li.appendChild(a);
      ul.appendChild(li);
    });
    tocNav.appendChild(ul);

    var activeLink = null;

    function activate(link) {
      if (link === activeLink) return;
      if (activeLink) activeLink.classList.remove('toc-link--active');
      activeLink = link;
      if (!activeLink) return;
      activeLink.classList.add('toc-link--active');
      var top    = activeLink.offsetTop;
      var bottom = top + activeLink.offsetHeight;
      var sTop   = tocSidebar.scrollTop;
      var sBtm   = sTop + tocSidebar.clientHeight;
      if (top < sTop)         tocSidebar.scrollTop = top - 8;
      else if (bottom > sBtm) tocSidebar.scrollTop = bottom - tocSidebar.clientHeight + 8;
    }

    function updateActive() {
      var THRESHOLD = 120;
      var current = null;
      for (var i = headings.length - 1; i >= 0; i--) {
        if (headings[i].getBoundingClientRect().top <= THRESHOLD) {
          current = headings[i]; break;
        }
      }
      if (!current) current = headings[0];
      activate(ul.querySelector('[data-target="' + current.id + '"]'));
    }

    var ticking = false;
    window.addEventListener('scroll', function () {
      if (!ticking) {
        requestAnimationFrame(function () { updateActive(); ticking = false; });
        ticking = true;
      }
    }, { passive: true });

    updateActive();
  }

  function init() {
    initProgress();
    buildToc();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
