#!/usr/bin/env node

const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const rootDir = path.resolve(__dirname, '..');
const backendDir = path.join(rootDir, 'backend');

const candidates = process.platform === 'win32'
  ? [
      path.join(backendDir, 'venv', 'Scripts', 'python.exe'),
      path.join(backendDir, '.venv', 'Scripts', 'python.exe'),
      'python',
    ]
  : [
      path.join(backendDir, 'venv', 'bin', 'python'),
      path.join(backendDir, '.venv', 'bin', 'python'),
      'python3',
      'python',
    ];

const python = candidates.find((candidate) => (
  path.isAbsolute(candidate) ? fs.existsSync(candidate) : true
));

if (!python) {
  console.error('Could not find Python. Create backend/venv first, then install backend/requirements.txt.');
  process.exit(1);
}

const child = spawn(
  python,
  ['-m', 'uvicorn', 'app.main:app', '--reload', '--port', '8000'],
  {
    cwd: backendDir,
    stdio: 'inherit',
  },
);

child.on('error', (error) => {
  console.error(`Could not start the backend: ${error.message}`);
  process.exit(1);
});

child.on('exit', (code) => {
  process.exit(code ?? 0);
});
