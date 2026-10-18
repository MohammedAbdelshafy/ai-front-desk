import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(currentDir, "..");
const repoRoot = path.resolve(appRoot, "../..");
const sourceFile = path.join(repoRoot, "ai_front_desk/clinical/obgyn_reference_centers.json");
const destFile = path.join(appRoot, "src/data/obgyn-reference-centers.json");

const raw = JSON.parse(await readFile(sourceFile, "utf8"));
if (raw.specialty !== "Obstetrics and Gynaecology") throw new Error("Wrong source catalog specialty");
if (!Array.isArray(raw.sources) || raw.sources.length < 20) throw new Error("OB-GYN source catalog is incomplete");
const ids = new Set();
for (const source of raw.sources) {
  if (!source.id || ids.has(source.id)) throw new Error(`Invalid/duplicate source id: ${source.id}`);
  ids.add(source.id);
  if (!source.title || !source.url?.startsWith("https://") || !Array.isArray(source.topics) || !Array.isArray(source.jurisdiction)) {
    throw new Error(`Incomplete provenance for source ${source.id}`);
  }
  if (!source.reuse_rights || !source.ingest_status) throw new Error(`Missing rights/status for source ${source.id}`);
}
await mkdir(path.dirname(destFile), { recursive: true });
await writeFile(destFile, JSON.stringify(raw, null, 2) + "\n", "utf8");
console.log(`Synced ${raw.sources.length} OB-GYN references (directory only; no protocols approved).`);
