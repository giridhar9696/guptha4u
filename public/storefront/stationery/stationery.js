(() => {
  const kalam = document.body.dataset.department === 'kalam';
  const root = kalam ? '/shop/kalam' : '/shop/stationery';
  if (kalam) {
    const reduced = matchMedia('(prefers-reduced-motion: reduce)');
    const handoff = 'gupta:kalam-zoom';
    document.addEventListener('click', event => {
      if (event.button !== 0 || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
      const link = event.target.closest('.kalam-tile, .kalam-back');
      const display = link?.matches('.kalam-back') ? document.querySelector('.kalam-collection-photo .kalam-display') :
        link?.querySelector('.kalam-display');
      if (!display) return;
      const {x, y, width, height} = display.getBoundingClientRect();
      if (y + height < 0 || y >= innerHeight || !width || !height) return;
      try {
        sessionStorage.setItem(handoff, JSON.stringify({
          group: display.dataset.kalamDisplay, path: link.pathname, x, y, width, height, time: Date.now()
        }));
      } catch { /* The collection link still works without storage. */ }
    });
    try {
      const start = JSON.parse(sessionStorage.getItem(handoff));
      sessionStorage.removeItem(handoff);
      const display = [...document.querySelectorAll('.kalam-display')]
        .find(item => item.dataset.kalamDisplay === start?.group);
      if (display && start.path === location.pathname && Date.now() - start.time < 3500) {
        if (reduced.matches) {
          display.animate([{opacity: .65}, {opacity: 1}], {duration: 90});
        } else {
          const end = display.getBoundingClientRect();
          display.animate([
            {transform: 'translate(' + (start.x - end.x) + 'px,' + (start.y - end.y) + 'px) scale(' +
              start.width / end.width + ',' + start.height / end.height + ')', transformOrigin: 'top left'},
            {transform: 'none', transformOrigin: 'top left'}
          ], {id: 'kalam-scene-zoom', duration: 660, easing: 'cubic-bezier(.22,.78,.24,1)'});
        }
      }
    } catch { /* A direct link or restored tab renders the scene normally. */ }
  }
  const back = document.querySelector('[data-stationery-product-back]');
  if (back && document.referrer && history.length > 1) {
    const previous = new URL(document.referrer);
    const previousView = previous.pathname === '/shop/cart' ? 'cart' : previous.pathname === '/shop/wishlist' ? 'wishlist' :
      (previous.pathname === root || previous.pathname.startsWith(root + '/')) &&
        !previous.pathname.startsWith(root + '/product/') ? (kalam ? 'Kalam' : 'stationery') : '';
    if (previous.origin === location.origin && previousView) {
      back.href = previous.href;
      back.textContent = `← Back to ${previousView}`;
      back.addEventListener('click', event => {
        if (event.button || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
        event.preventDefault();
        history.back();
      });
    }
  }
  const hero = document.querySelector('[data-stationery-hero]');
  if (!hero) return;
  const desktop = matchMedia('(min-width: 901px)');
  const fine = matchMedia('(hover: hover) and (pointer: fine)');
  const motion = matchMedia('(prefers-reduced-motion: no-preference)');
  let pending;

  function updateLift() {
    const active = hero.dataset.group ? null : (fine.matches ? hero.querySelector('.stationery-object:hover') : null) ||
      hero.querySelector('.stationery-object:focus-visible');
    for (const layer of hero.querySelectorAll('[data-lift]')) {
      layer.classList.toggle('is-active', active?.dataset.stationeryObject === layer.dataset.lift);
    }
  }

  for (const event of ['pointerover', 'pointerout', 'focusin', 'focusout']) {
    hero.addEventListener(event, () => requestAnimationFrame(updateLift));
  }

  async function openScene(url, key, push) {
    pending?.abort();
    const controller = new AbortController();
    pending = controller;
    const target = [...hero.querySelectorAll('[data-stationery-object]')]
      .find(link => link.dataset.stationeryObject === key);
    const copy = hero.querySelector('.stationery-copy');
    copy.classList.add('is-changing');
    if (target) {
      hero.dataset.side = target.dataset.side;
      hero.style.setProperty('--camera-pan', target.dataset.pan);
    }
    hero.dataset.group = key;
    updateLift();
    const skeleton = setTimeout(() => showProductSkeleton(document.querySelector('#stationery-products')), 140);
    try {
      const response = await fetch(url, { signal: controller.signal });
      if (!response.ok) throw new Error('Stationery collection unavailable');
      const page = new DOMParser().parseFromString(await response.text(), 'text/html');
      const next = page.querySelector('[data-stationery-hero]');
      const items = page.querySelector('#stationery-products');
      if (!next || !items) throw new Error('Stationery page unavailable');
      if (controller.signal.aborted) return;
      const replacement = next.querySelector('.stationery-copy');
      replacement.classList.add('is-changing');
      copy.replaceWith(replacement);
      hero.querySelector('.stationery-selected').replaceWith(next.querySelector('.stationery-selected'));
      document.querySelector('#stationery-products').replaceWith(items);
      const announcement = document.querySelector('[data-store-announcement]');
      const nextAnnouncement = page.querySelector('[data-store-announcement]');
      if (nextAnnouncement && announcement.innerHTML !== nextAnnouncement.innerHTML) {
        announcement.replaceWith(nextAnnouncement);
      }
      document.title = page.title;
      document.querySelector('link[rel="canonical"]').href = page.querySelector('link[rel="canonical"]').href;
      if (push) history.pushState({}, '', url);
      if (!key) {
        delete hero.dataset.side;
        hero.style.removeProperty('--camera-pan');
      }
      if (motion.matches) requestAnimationFrame(() => requestAnimationFrame(() => replacement.classList.remove('is-changing')));
      else replacement.classList.remove('is-changing');
      const heading = replacement.querySelector('h1');
      heading.tabIndex = -1;
      heading.focus({ preventScroll: true });
      document.dispatchEvent(new Event('storefront:navigated'));
      updateLift();
    } catch (error) {
      if (error.name !== 'AbortError') location.assign(url);
    } finally {
      clearTimeout(skeleton);
    }
  }

  hero.addEventListener('click', event => {
    const link = event.target.closest('[data-stationery-object], [data-stationery-back]');
    if (!link || !desktop.matches || event.button !== 0 || event.altKey || event.ctrlKey ||
        event.metaKey || event.shiftKey) return;
    event.preventDefault();
    openScene(link.href, link.dataset.stationeryObject || '', true);
  });
  window.addEventListener('popstate', () => {
    const key = location.pathname.slice(root.length).replace(/^\//, '');
    if (location.pathname === root || [...hero.querySelectorAll('[data-stationery-object]')]
        .some(link => link.pathname === location.pathname)) {
      openScene(location.href, key, false);
    } else location.reload();
  });
})();
