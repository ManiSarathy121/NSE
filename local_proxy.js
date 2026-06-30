const http = require('http');

const PORT = 20129; // Using 20129 to avoid any conflict if 9router is running locally
const VPS_HOST = '68.233.117.244';
const VPS_PORT = 20128;
const API_KEY = 'sk-58824cf4f07ee369-kytwvj-9963ec0a';

const server = http.createServer((req, res) => {
  // Handle CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // Proxy the request
  let body = '';
  req.on('data', chunk => { body += chunk; });
  req.on('end', () => {
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + API_KEY
    };

    const proxyReq = http.request({
      hostname: VPS_HOST,
      port: VPS_PORT,
      path: req.url,
      method: req.method,
      headers: headers
    }, (proxyRes) => {
      // Remove any target-specific CORS headers to let the proxy headers prevail
      delete proxyRes.headers['access-control-allow-origin'];
      delete proxyRes.headers['access-control-allow-methods'];
      delete proxyRes.headers['access-control-allow-headers'];
      
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res);
    });

    proxyReq.on('error', (err) => {
      console.error('Proxy Error:', err.message);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Local Proxy Error: ' + err.message }));
    });

    proxyReq.write(body);
    proxyReq.end();
  });
});

server.listen(PORT, () => {
  console.log(`============================================================`);
  console.log(`Local 9Router Proxy running on http://localhost:${PORT}`);
  console.log(`Forwarding requests to VPS: http://${VPS_HOST}:${VPS_PORT}`);
  console.log(`============================================================`);
});
