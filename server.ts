/**
 * AI Knowledge Inbox Full-Stack Server
 * Hosts Vite dev server on port 3000 and proxies /api/* requests to the FastAPI backend.
 * Spawns and manages FastAPI and the Ingestion Worker background process.
 */
import express from 'express';
import { createServer as createViteServer } from 'vite';
import http from 'http';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = 3000;
const FASTAPI_PORT = 8000;
const FASTAPI_HOST = '127.0.0.1';

let fastApiProcess: ChildProcess | null = null;
let workerProcess: ChildProcess | null = null;

function startBackendProcesses() {
  const backendDir = path.resolve(__dirname, 'backend');

  console.log('[Runner] Starting FastAPI backend on port 8000...');
  fastApiProcess = spawn(
    'python3',
    ['-m', 'uvicorn', 'app.main:app', '--host', FASTAPI_HOST, '--port', String(FASTAPI_PORT)],
    {
      cwd: backendDir,
      stdio: ['ignore', 'inherit', 'inherit'],
      env: { ...process.env, PYTHONPATH: backendDir },
    }
  );

  fastApiProcess.on('exit', (code) => {
    console.warn(`[Runner] FastAPI exited with code ${code}.`);
  });

  console.log('[Runner] Starting Ingestion Worker process...');
  workerProcess = spawn('python3', ['-m', 'app.workers.ingestion_worker'], {
    cwd: backendDir,
    stdio: ['ignore', 'inherit', 'inherit'],
    env: { ...process.env, PYTHONPATH: backendDir },
  });

  workerProcess.on('exit', (code) => {
    console.warn(`[Runner] Worker exited with code ${code}.`);
  });
}

function stopBackendProcesses() {
  if (fastApiProcess) {
    fastApiProcess.kill('SIGTERM');
    fastApiProcess = null;
  }
  if (workerProcess) {
    workerProcess.kill('SIGTERM');
    workerProcess = null;
  }
}

process.on('SIGINT', () => {
  stopBackendProcesses();
  process.exit(0);
});

process.on('SIGTERM', () => {
  stopBackendProcesses();
  process.exit(0);
});

async function createServer() {
  const app = express();

  // Start FastAPI and background worker
  startBackendProcesses();

  // Proxy /api/* to FastAPI
  app.use('/api', (req, res) => {
    const targetUrl = `http://${FASTAPI_HOST}:${FASTAPI_PORT}/api${req.url}`;
    const options: http.RequestOptions = {
      hostname: FASTAPI_HOST,
      port: FASTAPI_PORT,
      path: `/api${req.url}`,
      method: req.method,
      headers: {
        ...req.headers,
        host: `${FASTAPI_HOST}:${FASTAPI_PORT}`,
      },
    };

    const proxyReq = http.request(options, (proxyRes) => {
      res.writeHead(proxyRes.statusCode || 500, proxyRes.headers);
      proxyRes.pipe(res, { end: true });
    });

    proxyReq.on('error', (err) => {
      console.warn(`[Proxy] Waiting for FastAPI backend (${err.message})...`);
      res.status(503).json({
        detail: 'FastAPI backend is warming up. Please retry in a few seconds.',
      });
    });

    req.pipe(proxyReq, { end: true });
  });

  // Mount Vite dev server
  const vite = await createViteServer({
    server: {
      middlewareMode: true,
      port: PORT,
      host: '0.0.0.0',
    },
    appType: 'spa',
  });

  app.use(vite.middlewares);

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`[Full-Stack] Server running at http://0.0.0.0:${PORT}`);
    console.log(`[Full-Stack] FastAPI backend running at http://127.0.0.1:${FASTAPI_PORT}`);
  });
}

createServer().catch((err) => {
  console.error('Failed to start full-stack server:', err);
  process.exit(1);
});
