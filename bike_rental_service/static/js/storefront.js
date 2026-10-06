(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const scene = document.querySelector('[data-tilt]');
  if (scene && !reduced && matchMedia('(pointer: fine)').matches) {
    scene.addEventListener('pointermove', e => {const r = scene.getBoundingClientRect(); scene.style.transform = `rotateX(${-(e.clientY-r.top-r.height/2)/r.height*5}deg) rotateY(${(e.clientX-r.left-r.width/2)/r.width*7}deg)`;});
    scene.addEventListener('pointerleave', () => {scene.style.transform = '';});
  }
  if (!reduced && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {if(entry.isIntersecting){entry.target.classList.add('reveal-active');observer.unobserve(entry.target);}}), {threshold:.1});
    document.querySelectorAll('.section-intro,.document-card,.journey-grid article').forEach(el => observer.observe(el));
  }
  const search = document.getElementById('faq-search');
  if(search) search.addEventListener('input', () => {let count = 0;document.querySelectorAll('.faq-item').forEach(item => {item.hidden = !item.textContent.toLowerCase().includes(search.value.trim().toLowerCase());if(!item.hidden)count++;});document.getElementById('faq-status').textContent = search.value ? `${count} matching answers` : '';});
  const target = document.getElementById('google-reviews');
  const safeLink = value => {try{const url=new URL(value);return url.protocol==='https:'?url.href:'';}catch{return '';}};
  async function loadReviews(){
    try{const response=await fetch(target.dataset.endpoint,{credentials:'omit'});if(!response.ok)return;const data=await response.json();if(!data.available)return;
      const heading=document.createElement('p');heading.className='google-attribution';heading.textContent=`${data.rating} / 5 · ${data.count} Google reviews · selected by relevance`;
      const grid=document.createElement('div');grid.className='google-review-grid';
      for(const review of data.reviews){const card=document.createElement('figure');card.className='rental-panel';const rating=document.createElement('p');rating.textContent=`${review.rating} / 5 `;const star=document.createElement('i');star.className='fas fa-star';star.setAttribute('aria-hidden','true');rating.append(star);const text=document.createElement('blockquote');text.textContent=review.text;const author=document.createElement('figcaption');const link=document.createElement('a');link.textContent=review.author;link.href=safeLink(review.author_url)||safeLink(data.url);if(safeLink(review.photo)){const photo=document.createElement('img');photo.src=safeLink(review.photo);photo.alt='';photo.loading='lazy';author.append(photo);}author.append(link);const source=document.createElement('a');source.href=safeLink(review.url)||safeLink(data.url);source.textContent=`Read on Google · ${review.time}`;card.append(rating,text,author,source);grid.append(card);}
      const branding=document.createElement('p');branding.className='google-attribution';const logo=document.createElement('img');logo.className='google-maps-credit';logo.src=target.dataset.logo;logo.alt='Google Maps';branding.append(logo);for(const attribution of data.attributions||[]){const link=document.createElement('a');link.textContent=attribution.name;link.href=safeLink(attribution.url)||safeLink(data.url);branding.append(' · ',link);}target.replaceChildren(heading,grid,branding);
    }catch{/* Keep the useful public profile link when Google is unavailable. */}
  }
  if(target && target.dataset.endpoint){if('IntersectionObserver' in window){const observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){observer.disconnect();loadReviews();}},{rootMargin:'150px'});observer.observe(target);}else{loadReviews();}}
})();

/* A compact, manually controlled showroom; the full catalogue remains a grid. */
(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const carousel = document.querySelector('.fleet-carousel');
  if (carousel) {
    const track = carousel.querySelector('.fleet-track');
    const cards = [...track.querySelectorAll('.rental-card')];
    const controls = carousel.querySelector('.fleet-carousel-tools');
    const previous = carousel.querySelector('.fleet-prev');
    const next = carousel.querySelector('.fleet-next');
    let active = 0;
    let frame;
    function update() {
      carousel.querySelector('.fleet-viewport').classList.toggle('has-scrolled', track.scrollLeft > 8);
      const bounds = track.getBoundingClientRect();
      const center = bounds.left + bounds.width / 2;
      let closest = Infinity;
      cards.forEach((card, index) => {
        const box = card.getBoundingClientRect();
        const distance = Math.abs(box.left + box.width / 2 - center);
        if (distance < closest) { closest = distance; active = index; }
      });
      cards.forEach((card, index) => {
        card.classList.toggle('is-featured-slide', index === active);
        card.style.setProperty('--slide-angle', index === active ? '0deg' : index < active ? '5deg' : '-5deg');
      });
      carousel.querySelector('.fleet-position').textContent = `${String(active + 1).padStart(2, '0')} / ${String(cards.length).padStart(2, '0')} · ${cards[active].querySelector('h3').textContent}`;
      previous.disabled = active === 0;
      next.disabled = active === cards.length - 1;
    }
    function go(index) {
      const card = cards[Math.max(0, Math.min(index, cards.length - 1))];
      track.scrollTo({left: card.offsetLeft - (track.clientWidth - card.offsetWidth) / 2, behavior: reduced ? 'auto' : 'smooth'});
    }
    if (cards.length) {
      if (cards.length > 1) controls.hidden = false;
      previous.addEventListener('click', () => go(active - 1));
      next.addEventListener('click', () => go(active + 1));
      track.addEventListener('keydown', event => {
        if (event.target !== track) return;
        if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
          event.preventDefault(); go(active + (event.key === 'ArrowRight' ? 1 : -1));
        } else if (event.key === 'Home' || event.key === 'End') {
          event.preventDefault(); go(event.key === 'Home' ? 0 : cards.length - 1);
        }
      });
      track.addEventListener('scroll', () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(update); }, {passive: true});
      if ('ResizeObserver' in window) new ResizeObserver(update).observe(track);
      update();
    }
  }
})();
