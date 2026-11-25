
(function(){
var mb=document.querySelector('.menu-btn');if(mb){mb.addEventListener('click',function(){var h=mb.closest('header'),a=h.classList.toggle('aberto');mb.setAttribute('aria-expanded',a);mb.setAttribute('aria-label',a?'Fechar menu':'Abrir menu')})}
var fs=document.querySelectorAll('.colorir');
if('IntersectionObserver' in window&&fs.length){var o=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&matchMedia('(hover:none)').matches)e.target.classList.add('ativo')})},{threshold:.6});fs.forEach(function(f){o.observe(f);f.addEventListener('click',function(){f.classList.toggle('ativo')})})}
var bi=document.querySelector('form.busca[action] input');
if(bi){var bf=bi.form,box=document.createElement('ul'),sel=-1,opts=[],pedido=false;
box.className='sugest';box.id='sugest';box.setAttribute('role','listbox');box.hidden=true;bi.parentNode.appendChild(box);
bi.setAttribute('role','combobox');bi.setAttribute('aria-autocomplete','list');bi.setAttribute('aria-controls','sugest');bi.setAttribute('aria-expanded','false');
var carregar=function(){if(window.INDICE||pedido)return;pedido=true;var s=document.createElement('script');s.src='indice.js';s.onload=sugerir;document.head.appendChild(s)};
var fechar=function(){box.hidden=true;sel=-1;bi.setAttribute('aria-expanded','false');bi.removeAttribute('aria-activedescendant')};
var marcar=function(){opts.forEach(function(a,k){a.parentNode.classList.toggle('on',k===sel);a.parentNode.setAttribute('aria-selected',k===sel)});
if(sel>-1){bi.setAttribute('aria-activedescendant',opts[sel].parentNode.id);opts[sel].scrollIntoView({block:'nearest'})}else bi.removeAttribute('aria-activedescendant')};
var sugerir=function(){var v=bi.value.trim(),t=norm(v);if(!t||!window.INDICE){fechar();return}
var r=window.INDICE.map(function(i){var a=norm(i.t),p=a.indexOf(t),n=p===0?0:p>-1?1:norm(i.f.join(' ')).indexOf(t)>-1?2:norm(i.x).indexOf(t)>-1?3:-1;return{i:i,n:n}}).filter(function(o){return o.n>-1});
r.sort(function(a,b){return a.n-b.n});
box.innerHTML=r.length?r.slice(0,8).map(function(o,k){var i=o.i;return'<li id="sg'+k+'" role="option"><a href="r-'+i.s+'.html"><span class="sg-tipo">'+(i.k==='receita'?'Receita':'Memória')+'</span>'+esc(i.t)+(i.f.length?' <small>♥ '+esc(i.f.join(', '))+'</small>':'')+'</a></li>'}).join('')
+'<li id="sgt" class="sg-todos" role="option"><a href="receitas.html?q='+encodeURIComponent(v)+'">Ver '+(r.length===1?'o resultado':'todos os '+r.length+' resultados')+' →</a></li>'
:'<li class="sg-vazio">Nada encontrado para “'+esc(v)+'”</li>';
opts=[].slice.call(box.querySelectorAll('a'));sel=-1;marcar();box.hidden=false;bi.setAttribute('aria-expanded','true')};
bi.addEventListener('input',function(){carregar();sugerir()});
bi.addEventListener('focus',function(){carregar();if(bi.value.trim())sugerir()});
bi.addEventListener('keydown',function(e){if(e.key==='Escape'){fechar();return}
if(box.hidden||!opts.length)return;
if(e.key==='ArrowDown'){e.preventDefault();sel=sel+1<opts.length?sel+1:0;marcar()}
else if(e.key==='ArrowUp'){e.preventDefault();sel=sel>0?sel-1:opts.length-1;marcar()}
else if(e.key==='Enter'&&sel>-1){e.preventDefault();location.href=opts[sel].href}});
document.addEventListener('click',function(e){if(!bf.contains(e.target))fechar()})}
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
