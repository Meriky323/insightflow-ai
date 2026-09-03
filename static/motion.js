(()=>{
  const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const qs=(s,r=document)=>r.querySelector(s), qsa=(s,r=document)=>[...r.querySelectorAll(s)];

  // reveal choreography
  const reveal=qsa('[data-reveal]');
  if(!reduced && 'IntersectionObserver' in window){
    const io=new IntersectionObserver(entries=>entries.forEach(e=>{
      if(e.isIntersecting){const d=Number(e.target.dataset.delay||0);setTimeout(()=>e.target.classList.add('is-visible'),d);io.unobserve(e.target)}
    }),{threshold:.12,rootMargin:'0px 0px -6% 0px'});
    reveal.forEach(el=>io.observe(el));
  }else reveal.forEach(el=>el.classList.add('is-visible'));

  // cursor aura: enough life without becoming a cursor gimmick
  const aura=qs('.cursor-aura');
  if(aura && !reduced && matchMedia('(pointer:fine)').matches){
    let tx=innerWidth*.55,ty=innerHeight*.35,x=tx,y=ty;
    addEventListener('pointermove',e=>{tx=e.clientX;ty=e.clientY},{passive:true});
    const tick=()=>{x+=(tx-x)*.08;y+=(ty-y)*.08;aura.style.left=x+'px';aura.style.top=y+'px';requestAnimationFrame(tick)};tick();
  }

  // magnetic CTAs inspired by ReactBits Magnet but dependency-free
  if(!reduced && matchMedia('(pointer:fine)').matches){
    qsa('.magnetic').forEach(el=>{
      el.addEventListener('pointermove',e=>{const r=el.getBoundingClientRect(),dx=(e.clientX-r.left-r.width/2)*.13,dy=(e.clientY-r.top-r.height/2)*.13;el.style.transform=`translate(${dx}px,${dy}px)`});
      el.addEventListener('pointerleave',()=>{el.style.transform=''});
    });

    // spotlight hover similar in spirit to MagicCard / ReactBits glare, but restrained
    qsa('.spotlight-card').forEach(card=>card.addEventListener('pointermove',e=>{const r=card.getBoundingClientRect();card.style.setProperty('--mx',`${e.clientX-r.left}px`);card.style.setProperty('--my',`${e.clientY-r.top}px`)}));

    // very small editorial tilt on case posters; only pointer-fine devices
    qsa('.tilt-card').forEach(card=>{
      card.addEventListener('pointermove',e=>{const r=card.getBoundingClientRect(),rx=((e.clientY-r.top)/r.height-.5)*-1.2,ry=((e.clientX-r.left)/r.width-.5)*1.8;card.style.transform=`perspective(1200px) rotateX(${rx}deg) rotateY(${ry}deg)`});
      card.addEventListener('pointerleave',()=>card.style.transform='');
    });
  }

  // scroll-linked hero drift; deliberately tiny to protect readability
  const heroStage=qs('.hero-signal-stage');
  if(heroStage && !reduced){
    let ticking=false;
    const onScroll=()=>{if(ticking)return;ticking=true;requestAnimationFrame(()=>{const y=Math.min(1,scrollY/700);heroStage.style.transform=`translateY(${y*12}px) scale(${1-y*.012})`;ticking=false})};
    addEventListener('scroll',onScroll,{passive:true});onScroll();
  }

  // language toggle feedback
  qsa('[data-lang-toggle]').forEach(btn=>btn.addEventListener('click',()=>{btn.animate?.([{transform:'scale(.9)'},{transform:'scale(1.05)'},{transform:'scale(1)'}],{duration:280,easing:'cubic-bezier(.22,.8,.24,1)'})}));
})();
