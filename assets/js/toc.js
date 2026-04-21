(function () {
  'use strict';

  function buildToc() {
    var article    = document.querySelector('.blog-post');
    var tocNav     = document.getElementById('toc-nav');
    var tocSidebar = document.getElementById('toc-sidebar');
    var tocCol     = document.querySelector('.toc-col');
    if (!article || !tocNav || !tocSidebar || !tocCol) return;

    // H2, H3, H4 — three levels
    var headings = Array.from(article.querySelectorAll('h2, h3, h4'));
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
      a.href          = '#' + h.id;
      a.className     = 'toc-link';
      a.textContent   = h.textContent.trim();
      a.dataset.target = h.id;
      li.appendChild(a);
      ul.appendChild(li);
    });
    tocNav.appendChild(ul);

    var links      = Array.from(ul.querySelectorAll('.toc-link'));
    var activeLink = null;

    /* ---- Active section tracking ---- */
    function activate(link) {
      if (link === activeLink) return;
      if (activeLink) activeLink.classList.remove('toc-link--active');
      activeLink = link;
      if (!activeLink) return;
      activeLink.classList.add('toc-link--active');
      // Scroll the sidebar so the active item stays visible
      var top    = activeLink.offsetTop;
      var bottom = top + activeLink.offsetHeight;
      var sTop   = tocSidebar.scrollTop;
      var sBtm   = sTop + tocSidebar.clientHeight;
      if (top < sTop)        tocSidebar.scrollTop = top - 8;
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

    /* ---- JS-driven sticky ---- */
    var NAVBAR     = 80;
    var isFixed    = false;
    var colLeft    = 0;
    var colWidth   = 0;

    function measure() {
      var rect  = tocCol.getBoundingClientRect();
      colLeft   = rect.left;
      colWidth  = rect.width;
    }

    function updateSticky() {
      var colRect = tocCol.getBoundingClientRect();
      if (!isFixed && colRect.top <= NAVBAR) {
        measure();
        tocSidebar.style.position = 'fixed';
        tocSidebar.style.top      = NAVBAR + 'px';
        tocSidebar.style.left     = colLeft + 'px';
        tocSidebar.style.width    = colWidth + 'px';
        isFixed = true;
      } else if (isFixed && colRect.top > NAVBAR) {
        tocSidebar.style.position = '';
        tocSidebar.style.top      = '';
        tocSidebar.style.left     = '';
        tocSidebar.style.width    = '';
        isFixed = false;
      }
    }

    window.addEventListener('resize', function () {
      tocSidebar.style.position = '';
      tocSidebar.style.top = tocSidebar.style.left = tocSidebar.style.width = '';
      isFixed = false;
      measure();
    }, { passive: true });

    /* ---- Combined scroll handler (rAF throttled) ---- */
    var ticking = false;
    window.addEventListener('scroll', function () {
      if (!ticking) {
        requestAnimationFrame(function () {
          updateSticky();
          updateActive();
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });

    measure();
    updateActive();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildToc);
  } else {
    buildToc();
  }
})();
