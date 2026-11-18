import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const viteBin = path.join(__dirname, 'node_modules', 'vite', 'bin', 'vite.js');

console.log('Starting Vite server from:', __dirname);
const child = spawn(process.execPath, [viteBin, '--host', '0.0.0.0', '--port', '3001'], {
  cwd: __dirname,
  stdio: 'inherit'
});
