/* Rental enquiries share a regular-page fallback across the fleet and bike detail. */
(() => {
  const navigation = document.querySelector('.modern-transparent-nav');
  const desktop = matchMedia('(min-width: 992px)');
  function updateNavigation() {
    navigation?.classList.toggle('is-floating', desktop.matches && window.scrollY > 160);
  }
  window.addEventListener('scroll', updateNavigation, {passive: true});
  desktop.addEventListener('change', updateNavigation);
  updateNavigation();
  const mobileMenu = document.getElementById('navbarNav');
  document.querySelectorAll('#navbarNav a').forEach(link => {
    link.addEventListener('click', () => {
      if (!matchMedia('(max-width: 991px)').matches || !mobileMenu) return;
      const toggle = document.querySelector('.navbar-toggler');
      if (mobileMenu.classList.contains('show')) toggle.click();
      else if (toggle.getAttribute('aria-expanded') === 'true') {
        // Finish opening before closing if a link is selected during the transition.
        mobileMenu.addEventListener('shown.bs.collapse', () => toggle.click(), {once: true});
      }
    });
  });
  const dialog = document.getElementById('availability-dialog');
  if (!dialog || typeof dialog.showModal !== 'function') return;
  const form = document.getElementById('availability-form');
  const start = document.getElementById('availability-start');
  const end = document.getElementById('availability-end');
  const result = document.getElementById('availability-result');
  const parts = new Intl.DateTimeFormat('en', {
    timeZone: 'Asia/Kathmandu', year: 'numeric', month: '2-digit', day: '2-digit'
  }).formatToParts(new Date());
  const date = Object.fromEntries(parts.map(part => [part.type, part.value]));
  const today = `${date.year}-${date.month}-${date.day}`;
  start.min = end.min = today;
  let selectedBike = '';
  let opener;
  function resetResult() { result.hidden = true; }
  document.querySelectorAll('.availability-trigger').forEach(link => {
    link.addEventListener('click', event => {
      // Modified clicks keep the regular enquiry page usable in another tab.
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      selectedBike = link.dataset.bikeName;
      document.getElementById('availability-bike').textContent = selectedBike;
      document.getElementById('availability-bike-id').value = link.dataset.bikeId;
      resetResult();
      opener = link;
      dialog.showModal();
      start.focus();
    });
  });
  dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => { if (opener) opener.focus(); });
  start.addEventListener('input', () => { end.min = start.value || today; resetResult(); });
  end.addEventListener('input', resetResult);
  form.addEventListener('submit', event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const id = document.getElementById('availability-bike-id').value;
    const message = `Hello EasyMoto, is ${selectedBike} (fleet #${id}) available?\nPickup: ${start.value}\nReturn: ${end.value} by 7 PM (Nepal time).\nPlease confirm availability and the total rental cost.`;
    const query = new URLSearchParams({text: message});
    document.getElementById('availability-whatsapp').href = `https://wa.me/9779851401903?${query}`;
    document.getElementById('availability-summary').textContent = `${selectedBike}: pickup ${start.value}, return ${end.value} by 7 PM Nepal time.`;
    result.hidden = false;
    document.getElementById('availability-whatsapp').focus();
  });
})();
