(()=>{
  'use strict';
  const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const fine=window.matchMedia?.('(pointer:fine)').matches;
  const qs=(s,r=document)=>r.querySelector(s), qsa=(s,r=document)=>[...r.querySelectorAll(s)];

  // Mount non-semantic motion artifacts once.
  if(!qs('#if-scroll-progress')){
    const p=document.createElement('div');p.id='if-scroll-progress';p.setAttribute('aria-hidden','true');document.body.appendChild(p);
  }
  if(!qs('#if-transition-veil')){
    const v=document.createElement('div');v.id='if-transition-veil';v.setAttribute('aria-hidden','true');document.body.appendChild(v);
  }

  const root=document.documentElement;
  let scrollTick=false;
  const updateScroll=()=>{
    const max=Math.max(1,document.documentElement.scrollHeight-innerHeight);
    root.style.setProperty('--if-scroll',Math.min(1,scrollY/max).toFixed(4));
    qs('.site-nav')?.classList.toggle('if-scrolled',scrollY>18);
    if(!reduced){
      const ax=Math.max(-16,Math.min(16,(scrollY/max-.25)*18));
      root.style.setProperty('--if-aura-y',`${ax}px`);
    }
    scrollTick=false;
  };
  addEventListener('scroll',()=>{if(!scrollTick){scrollTick=true;requestAnimationFrame(updateScroll)}},{passive:true});
  updateScroll();

  // Hero text finishing stroke.
  const heroCopy=qs('.hero-v2-copy');
  if(heroCopy) requestAnimationFrame(()=>setTimeout(()=>heroCopy.classList.add('if-entered'),160));

  // Context-aware active nav on the landing page.
  const navPairs=qsa('.site-links a[href^="#"]').map(a=>({a,el:qs(a.getAttribute('href'))})).filter(x=>x.el);
  if(navPairs.length && 'IntersectionObserver' in window){
    const navIO=new IntersectionObserver(entries=>{
      const visible=entries.filter(e=>e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];
      if(!visible)return;
      navPairs.forEach(x=>x.a.classList.toggle('if-active',x.el===visible.target));
    },{rootMargin:'-25% 0px -55% 0px',threshold:[0,.1,.25,.5]});
    navPairs.forEach(x=>navIO.observe(x.el));
  }

  // Scroll-stack progress. Inspired by ReactBits Scroll Stack, rebuilt dependency-free.
  if(!reduced && 'IntersectionObserver' in window){
    const cards=qsa('.story-card');
    const stackIO=new IntersectionObserver(entries=>entries.forEach(e=>{
      if(e.isIntersecting)e.target.dataset.ifVisible='1';
    }),{rootMargin:'10% 0px 10% 0px'});
    cards.forEach(c=>stackIO.observe(c));
    let stackTick=false;
    const stackUpdate=()=>{
      const vh=innerHeight;
      cards.forEach(c=>{
        const r=c.getBoundingClientRect();
        const p=Math.max(0,Math.min(1,(vh-r.top)/(vh*.72)));
        c.style.setProperty('--if-card-progress',p.toFixed(3));
      });
      stackTick=false;
    };
    addEventListener('scroll',()=>{if(!stackTick){stackTick=true;requestAnimationFrame(stackUpdate)}},{passive:true});
    addEventListener('resize',stackUpdate,{passive:true});stackUpdate();
  }

  // Pointer-reactive signal stage and product preview.
  if(fine && !reduced){
    const stage=qs('.hero-signal-stage');
    if(stage){
      stage.addEventListener('pointermove',e=>{
        const r=stage.getBoundingClientRect();
        const x=(e.clientX-r.left)/r.width, y=(e.clientY-r.top)/r.height;
        stage.style.setProperty('--if-stage-x',`${(x*100).toFixed(1)}%`);
        stage.style.setProperty('--if-stage-y',`${(y*100).toFixed(1)}%`);
        const rx=(.5-y)*1.8, ry=(x-.5)*2.4;
        stage.style.transform=`perspective(1400px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(${Math.min(10,scrollY/80)}px)`;
      });
      stage.addEventListener('pointerleave',()=>stage.style.transform='');
    }
    const wp=qs('.workspace-preview');
    if(wp){
      wp.addEventListener('pointerenter',()=>wp.classList.add('if-hover'));
      wp.addEventListener('pointermove',e=>{
        const r=wp.getBoundingClientRect(),x=(e.clientX-r.left)/r.width,y=(e.clientY-r.top)/r.height;
        wp.style.transform=`perspective(1600px) rotateX(${(.5-y)*.9}deg) rotateY(${(x-.5)*1.1}deg)`;
      });
      wp.addEventListener('pointerleave',()=>{wp.classList.remove('if-hover');wp.style.transform=''});
    }
    qsa('.case-poster').forEach(p=>p.addEventListener('pointermove',e=>{
      const r=p.getBoundingClientRect();p.style.setProperty('--mx',`${((e.clientX-r.left)/r.width*100).toFixed(1)}%`);p.style.setProperty('--my',`${((e.clientY-r.top)/r.height*100).toFixed(1)}%`);
    }));
  }

  // Language switch gets a tiny directional cue without changing app translation logic.
  qsa('[data-lang-toggle]').forEach(btn=>{
    const sync=()=>{const t=(btn.textContent||'').trim().toLowerCase();btn.style.setProperty('--if-lang-shift',t.includes('english')||t==='en'?'30px':'0px')};
    sync();btn.addEventListener('click',()=>setTimeout(sync,40));
  });

  // Progressive numeric proof on first viewport appearance.
  if(!reduced && 'IntersectionObserver' in window){
    const nums=qsa('.hero-proof-inline b').filter(n=>/^\d+$/.test((n.textContent||'').trim()));
    const numIO=new IntersectionObserver(entries=>entries.forEach(e=>{
      if(!e.isIntersecting)return;numIO.unobserve(e.target);
      const target=Number(e.target.textContent),start=performance.now(),dur=650;
      const tick=t=>{const p=Math.min(1,(t-start)/dur),v=Math.round(target*(1-Math.pow(1-p,3)));e.target.textContent=String(v);if(p<1)requestAnimationFrame(tick)};requestAnimationFrame(tick);
    }),{threshold:.7});nums.forEach(n=>numIO.observe(n));
  }

  // Add a page veil only for in-product navigation links; external links remain instant.
  qsa('a[href^="/case-"]').forEach(a=>a.addEventListener('click',e=>{
    if(e.metaKey||e.ctrlKey||a.target==='_blank'||reduced)return;
    e.preventDefault();document.body.classList.add('if-leaving');setTimeout(()=>location.href=a.href,360);
  }));

  // Expose the design build for live verification without touching app APIs.
  window.__INSIGHTFLOW_DESIGN_BUILD__='2.1-evidence-editorial';
})();
