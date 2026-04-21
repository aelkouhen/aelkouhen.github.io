(function () {
  'use strict';

  function buildToc() {
    var article = document.querySelector('.blog-post');
    var tocNav   = document.getElementById('toc-nav');
    var tocSidebar = document.getElementById('toc-sidebar');
    if (!article || !tocNav || !tocSidebar) return;

    var headings = Array.from(article.querySelectorAll('h2, h3'));
    if (headings.length < 2) {
      tocSidebar.style.display = 'none';
      return;
    }

    // Ensure every heading has a stable ID
    headings.forEach(function (h, i) {
      if (!h.id) {
        h.id = h.textContent
          .toLowerCase()
          .replace(/[^\w\s-]/g, '')
          .trim()
          .replace(/\s+/g, '-') + '-' + i;
      }
    });

    // Build the list
    var ul = document.createElement('ul');
    ul.className = 'toc-list';

    headings.forEach(function (h) {
      var li = document.createElement('li');
      li.className = h.tagName === 'H3' ? 'toc-item toc-item--h3' : 'toc-item toc-item--h2';

      var a = document.createElement('a');
      a.href            = '#' + h.id;
      a.className       = 'toc-link';
      a.textContent     = h.textContent.trim();
      a.dataset.target  = h.id;

      li.appendChild(a);
      ul.appendChild(li);
    });

    tocNav.appendChild(ul);

    var links      = Array.from(ul.querySelectorAll('.toc-link'));
    var activeLink = null;

    function activate(link) {
      if (link === activeLink) return;
      if (activeLink) activeLink.classList.remove('toc-link--active');
      activeLink = link;
      if (!activeLink) return;
      activeLink.classList.add('toc-link--active');
      // Keep active item visible inside the TOC scroll area
      var sidebar = tocSidebar;
      var linkTop    = activeLink.offsetTop;
      var linkBottom = linkTop + activeLink.offsetHeight;
      var sTop    = sidebar.scrollTop;
      var sBottom = sTop + sidebar.clientHeight;
      if (linkTop < sTop) {
        sidebar.scrollTo({ top: linkTop - 16, behavior: 'smooth' });
      } else if (linkBottom > sBottom) {
        sidebar.scrollTo({ top: linkBottom - sidebar.clientHeight + 16, behavior: 'smooth' });
      }
    }

    function update() {
      var OFFSET = 110; // px below viewport top to consider "active"
      var active = null;
      for (var i = headings.length - 1; i >= 0; i--) {
        if (headings[i].getBoundingClientRect().top <= OFFSET) {
          active = headings[i];
          break;
        }
      }
      // If no heading has passed the threshold yet, highlight the first
      if (!active) active = headings[0];
      var link = ul.querySelector('[data-target="' + active.id + '"]');
      activate(link);
    }

    // Throttle with rAF
    var ticking = false;
    window.addEventListener('scroll', function () {
      if (!ticking) {
        requestAnimationFrame(function () { update(); ticking = false; });
        ticking = true;
      }
    }, { passive: true });

    update();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildToc);
  } else {
    buildToc();
  }
})();
