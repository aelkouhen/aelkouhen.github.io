(function () {
  'use strict';

  function buildToc() {
    var article = document.querySelector('.blog-post');
    var tocNav = document.getElementById('toc-nav');
    var tocSidebar = document.getElementById('toc-sidebar');
    if (!article || !tocNav || !tocSidebar) return;

    var headings = article.querySelectorAll('h2, h3');
    if (headings.length < 2) {
      tocSidebar.style.display = 'none';
      return;
    }

    var ul = document.createElement('ul');
    ul.className = 'toc-list';

    headings.forEach(function (heading, i) {
      if (!heading.id) {
        heading.id = heading.textContent
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-|-$/g, '') + '-' + i;
      }

      var li = document.createElement('li');
      li.className = heading.tagName === 'H3' ? 'toc-item toc-item--sub' : 'toc-item';

      var a = document.createElement('a');
      a.href = '#' + heading.id;
      a.className = 'toc-link';
      a.textContent = heading.textContent;

      li.appendChild(a);
      ul.appendChild(li);
    });

    tocNav.appendChild(ul);

    // Highlight active section on scroll
    var links = ul.querySelectorAll('.toc-link');

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          links.forEach(function (l) { l.classList.remove('toc-link--active'); });
          var active = ul.querySelector('a[href="#' + entry.target.id + '"]');
          if (active) active.classList.add('toc-link--active');
        }
      });
    }, { rootMargin: '-10% 0px -80% 0px', threshold: 0 });

    headings.forEach(function (h) { observer.observe(h); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildToc);
  } else {
    buildToc();
  }
})();
