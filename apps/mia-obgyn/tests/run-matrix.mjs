// Bundles tests/search-matrix.ts with the project's esbuild and runs it.
// No new dependency: esbuild ships with vite.
import { execFileSync, spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, '..');
const require = createRequire(path.join(appRoot, 'package.json'));
const esbuildBin = require.resolve('esbuild/bin/esbuild');
import os from 'node:os';
const outFile = path.join(os.tmpdir(), 'mia-search-matrix.cjs');

execFileSync(esbuildBin, [
  path.join(here, 'search-matrix.ts'),
  '--bundle',
  '--platform=node',
  '--format=cjs',
  '--outfile=' + outFile,
  '--log-level=error',
], { stdio: 'inherit' });

const run = spawnSync(process.execPath, [outFile], { stdio: 'inherit' });
process.exit(run.status ?? 1);
