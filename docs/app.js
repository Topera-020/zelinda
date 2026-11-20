
(function(){
var mb=document.querySelector('.menu-btn');if(mb){mb.addEventListener('click',function(){var h=mb.closest('header'),a=h.classList.toggle('aberto');mb.setAttribute('aria-expanded',a);mb.setAttribute('aria-label',a?'Fechar menu':'Abrir menu')})}
var fs=document.querySelectorAll('.colorir');
if('IntersectionObserver' in window&&fs.length){var o=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&matchMedia('(hover:none)').matches)e.target.classList.add('ativo')})},{threshold:.6});fs.forEach(function(f){o.observe(f);f.addEventListener('click',function(){f.classList.toggle('ativo')})})}
var L=document.getElementById('lista');if(!L||!window.INDICE)return;
var q=document.getElementById('q'),cont=document.getElementById('cont'),tipo='';
var p=new URLSearchParams(location.search);q.value=p.get('q')||'';tipo=p.get('t')||'';
function norm(s){return s.normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase()}
function esc(s){return s.replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function render(){var t=norm(q.value.trim()),r=window.INDICE.filter(function(i){return(!tipo||i.k===tipo)&&(!t||norm(i.t+' '+i.f.join(' ')+' '+i.x).indexOf(t)>-1)});
L.innerHTML=r.map(function(i){return'<li><a href="r-'+i.s+'.html">'+esc(i.t)+'</a>'+(i.f.length?' <small>♥ '+esc(i.f.join(', '))+'</small>':'')+'</li>'}).join('');
cont.textContent=r.length+' resultado'+(r.length===1?'':'s');
document.querySelectorAll('.filtros button').forEach(function(b){b.classList.toggle('on',b.dataset.t===tipo)})}
q.addEventListener('input',render);document.querySelectorAll('.filtros button').forEach(function(b){b.addEventListener('click',function(){tipo=b.dataset.t;render()})});render();
})();
