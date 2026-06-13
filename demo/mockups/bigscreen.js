// Big-screen street look-around. Self-contained, injected with one <script src> line.
// Adds a top-right "BIG SCREEN" button that opens the 360 look-around for the
// currently selected site, fullscreen, for the projector. Reads the page's global `sel`.
(function () {
  const FALLBACK_POLE = 'UP-369';
  function currentPole() {
    try { return (typeof sel !== 'undefined' && sel) ? sel : FALLBACK_POLE; }
    catch (e) { return FALLBACK_POLE; }
  }

  // --- button (top right of the header status, or fixed fallback) ---
  const btn = document.createElement('button');
  btn.id = 'bigscreen-btn';
  btn.textContent = 'BIG SCREEN';
  btn.style.cssText =
    'font-family:"JetBrains Mono",monospace;font-size:10px;letter-spacing:.14em;font-weight:600;' +
    'color:#06221d;background:#34e3d4;border:0;padding:7px 13px;border-radius:6px;cursor:pointer;' +
    'box-shadow:0 0 12px rgba(52,227,212,.35)';
  const status = document.querySelector('.status');
  if (status) {
    btn.style.marginRight = '12px';
    status.insertBefore(btn, status.firstChild);
  } else {
    btn.style.position = 'fixed'; btn.style.top = '10px'; btn.style.right = '14px'; btn.style.zIndex = '9999';
    document.body.appendChild(btn);
  }

  // --- fullscreen overlay with the look-around in an iframe ---
  const ov = document.createElement('div');
  ov.id = 'bigscreen-ov';
  ov.style.cssText = 'position:fixed;inset:0;z-index:10000;background:#070b11;display:none';
  ov.innerHTML =
    '<iframe id="bigscreen-frame" allow="fullscreen" style="width:100%;height:100%;border:0;display:block"></iframe>' +
    '<button id="bigscreen-close" style="position:fixed;top:12px;right:16px;z-index:10001;' +
    'font-family:\'JetBrains Mono\',monospace;font-size:11px;letter-spacing:.1em;color:#d3deea;' +
    'background:rgba(7,11,17,.85);border:1px solid rgba(74,222,210,.4);padding:8px 13px;border-radius:7px;cursor:pointer">CLOSE  ESC</button>';
  document.body.appendChild(ov);
  const frame = ov.querySelector('#bigscreen-frame');

  function open() {
    frame.src = 'lookaround.html?pole=' + encodeURIComponent(currentPole());
    ov.style.display = 'block';
    if (ov.requestFullscreen) ov.requestFullscreen().catch(() => {});
  }
  function close() {
    ov.style.display = 'none';
    frame.src = '';
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
  }
  btn.onclick = open;
  ov.querySelector('#bigscreen-close').onclick = close;
  addEventListener('keydown', e => { if (e.key === 'Escape' && ov.style.display === 'block') close(); });
})();
