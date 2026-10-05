/* Rebuild the portable, network-independent single-file demonstration. */
const fs=require('node:fs'),path=require('node:path');
const read=p=>fs.readFileSync(path.join(__dirname,p),'utf8');
let html=read('index.html').replace('<link rel="stylesheet" href="style.css">',()=>'<style>'+read('style.css')+'</style>');
for(const p of ['vendor/three.min.js','data.js','scene.js','app.js'])html=html.replace('<script src="'+p+'"></script>',()=>'<script>\n'+read(p).replace(/<\/script/gi,'<\\/script')+'\n</script>');
const out=path.join(__dirname,'MIS_3D演示.html');fs.writeFileSync(out,html);console.log('Portable HTML: '+out+' ('+Buffer.byteLength(html)+' bytes)');
