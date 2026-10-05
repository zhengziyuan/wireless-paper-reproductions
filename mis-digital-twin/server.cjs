const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const root=__dirname,port=Number(process.argv[2]||8769);
const mime={'.html':'text/html; charset=utf-8','.js':'application/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.md':'text/plain; charset=utf-8','.png':'image/png'};
http.createServer((req,res)=>{let requested;try{requested=decodeURIComponent(new URL(req.url,'http://localhost').pathname);}catch{res.writeHead(400);res.end();return;}
if(requested==='/__mis_status'){res.setHeader('Content-Type','application/json');res.end(JSON.stringify({app:'mis-digital-twin',version:1}));return;}
const file=path.resolve(root,'.'+(requested==='/'?'/index.html':requested));if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
fs.readFile(file,(err,data)=>{if(err){res.writeHead(404);res.end('Not found');return;}res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});res.end(data);});
}).listen(port,'127.0.0.1',()=>console.log('MIS demo: http://127.0.0.1:'+port));
