/* Optional catalog enhancement; every product remains crawlable without JavaScript. */
const filters = document.querySelector('.filter-bar');
if (filters) {
  filters.hidden = false;
  const cards = [...document.querySelectorAll('[data-platform]')];
  const status = document.querySelector('[data-filter-status]');
  function filter(platform) {
    for (const card of cards) card.hidden = platform !== 'all' && card.dataset.platform !== platform;
    for (const button of filters.querySelectorAll('button')) button.setAttribute('aria-pressed', String(button.dataset.filter === platform));
    const count = cards.filter(card => !card.hidden).length;
    status.textContent = document.documentElement.lang === 'ja' ? `${count}件のアプリを表示` : `${count} apps shown`;
  }
  filters.addEventListener('click', event => {
    const button = event.target.closest('button[data-filter]');
    if (button) filter(button.dataset.filter);
  });
  const hash = location.hash.toLowerCase();
  if (hash === '#macos') filter('macOS');
  if (hash === '#ios') filter('iOS');
}
