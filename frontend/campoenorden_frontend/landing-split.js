const fs = require('fs');

const www = 'www';

fs.copyFileSync(`${www}/index.html`, `${www}/login.html`);
fs.copyFileSync('src/landing.html', `${www}/index.html`);

console.log('landing split ok: / -> landing.html como index, /login -> app');