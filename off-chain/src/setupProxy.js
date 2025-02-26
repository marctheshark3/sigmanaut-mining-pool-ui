const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use((req, res, next) => {
    // Remove X-Frame-Options header to allow embedding
    res.removeHeader('X-Frame-Options');
    
    // Set CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    // Set CSP headers
    res.setHeader(
      'Content-Security-Policy',
      "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; " +
      "frame-ancestors * http://localhost:* http://127.0.0.1:*; " +
      "img-src * data: blob:; " +
      "style-src * 'unsafe-inline'; " +
      "script-src * 'unsafe-inline' 'unsafe-eval' blob:; " +
      "connect-src * ws: wss:;"
    );

    next();
  });

  // Handle OPTIONS requests
  app.use((req, res, next) => {
    if (req.method === 'OPTIONS') {
      res.status(200).end();
      return;
    }
    next();
  });
}; 