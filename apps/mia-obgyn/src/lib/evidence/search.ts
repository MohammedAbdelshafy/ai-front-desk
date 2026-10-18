import { loadObgynCatalog, sourceMatchesJurisdiction, type EvidenceSource, type Jurisdiction } from "./catalog";

export type SearchFilters = { jurisdiction: Jurisdiction; careStage?: string; limit?: number };
export type MatchedSource = EvidenceSource & { matchReason: string; relevance: number };

function normalize(value: string): string {
  return value.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu, " ").replace(/\s+/g, " ").trim();
}

function tokens(value: string): Set<string> {
  return new Set(normalize(value).split(/[\s-]+/).filter((x) => x.length > 1));
}

export function searchObgynSources(query: string, filters: SearchFilters): MatchedSource[] {
  const normalizedQuery = normalize(query).slice(0, 240);
  if (!normalizedQuery) return [];
  const queryTokens = tokens(normalizedQuery);
  const limit = Math.max(1, Math.min(15, Math.floor(filters.limit ?? 8)));
  const sources = loadObgynCatalog();
  const results: MatchedSource[] = [];

  for (const source of sources) {
    if (!sourceMatchesJurisdiction(source, filters.jurisdiction)) continue;
    const titleText = tokens(source.title);
    const topicText = tokens(source.topics.join(" "));
    const publisherText = tokens(source.publisher ?? "");
    const noteText = tokens((source.notes ?? []).join(" "));
    let score = 0;
    const reasons: string[] = [];
    for (const token of queryTokens) {
      if (titleText.has(token)) { score += 5; reasons.push(`title: ${token}`); }
      if (topicText.has(token)) { score += 4; reasons.push(`topic: ${token}`); }
      if (publisherText.has(token)) score += 1;
      if (noteText.has(token)) score += 0.5;
    }
    if (filters.careStage && source.topics.some((topic) => normalize(topic).includes(normalize(filters.careStage ?? "")))) score += 1;
    if (score > 0) results.push({ ...source, relevance: score, matchReason: [...new Set(reasons)].slice(0, 5).join(", ") });
  }
  return results.sort((a, b) => b.relevance - a.relevance || a.title.localeCompare(b.title)).slice(0, limit);
}
