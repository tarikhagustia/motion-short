// HUD: slow scan band sweeping down the screen, status dot blink.
const hudBand = document.getElementById('hud-band');
const hudDot = document.querySelector('.hud-dot');
STYLE.frame = function (t) {
  if (hudBand) hudBand.style.top = (((t * 260) % 2300) - 200) + 'px';
  if (hudDot) hudDot.style.opacity = (Math.floor(t * 2) % 2) ? .3 : 1;
};
