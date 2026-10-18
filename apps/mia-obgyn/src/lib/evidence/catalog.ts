import catalogJson from "@/data/obgyn-reference-centers.json";

export type Jurisdiction = "EG" | "GLOBAL" | "US" | "UK";

export type EvidenceSource = {
  id: string;
  title: string;
  publisher?: string;
  jurisdiction: string[];
  topics: string[];
  url: string;
  version?: string;
  published_on?: string;
  reuse_rights: string;
  ingest_status: string;
  clinical_role?: string;
  notes?: string[];
};

type RawCatalog = { specialty: string; status: string; sources: EvidenceSource[] };
const catalog = catalogJson as RawCatalog;

export function loadObgynCatalog(): EvidenceSource[] {
  if (catalog.specialty !== "Obstetrics and Gynaecology") throw new Error("Mia OB-GYN only accepts the OB-GYN source catalog");
  const ids = new Set<string>();
  for (const item of catalog.sources) {
    if (!item.id || ids.has(item.id)) throw new Error("OB-GYN source IDs must be unique");
    ids.add(item.id);
    if (!item.url.startsWith("https://")) throw new Error(`Source ${item.id} must use HTTPS`);
    if (!item.title || !item.reuse_rights || !item.ingest_status || item.topics.length === 0 || item.jurisdiction.length === 0) {
      throw new Error(`Source ${item.id} is missing provenance, rights, topics or jurisdiction`);
    }
  }
  return catalog.sources;
}

export function sourceMatchesJurisdiction(source: EvidenceSource, selected: Jurisdiction): boolean {
  if (selected === "GLOBAL") return source.jurisdiction.some((x) => ["GLOBAL", "GLOBAL_REFERENCE"].includes(x));
  if (source.jurisdiction.includes(selected)) return true;
  return source.jurisdiction.includes("GLOBAL_REFERENCE");
}
