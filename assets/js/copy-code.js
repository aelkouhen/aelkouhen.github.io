(function () {
  'use strict';

  document.querySelectorAll('.highlight').forEach(function (block) {
    var btn = document.createElement('button');
    btn.className = 'code-copy-btn';
    btn.textContent = 'Copy';
    block.appendChild(btn);

    btn.addEventListener('click', function () {
      var pre = block.querySelector('pre:not(.lineno)');
      var text = pre ? pre.innerText : '';
      navigator.clipboard.writeText(text).then(function () {
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(function () {
          btn.textContent = 'Copy';
          btn.classList.remove('copied');
        }, 2000);
      }).catch(function () {
        btn.textContent = 'Error';
        setTimeout(function () { btn.textContent = 'Copy'; }, 2000);
      });
    });
  });
})();
