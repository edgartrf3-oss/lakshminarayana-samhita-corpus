function filterVerses(){const q=(document.getElementById('verseFilter')?.value||'').toLocaleLowerCase();document.querySelectorAll('.verse').forEach(v=>{v.classList.toggle('hidden',q && !v.innerText.toLocaleLowerCase().includes(q));});}
function copyLink(id){const u=new URL(location.href);u.hash=id;navigator.clipboard?.writeText(u.toString());}
