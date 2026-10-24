// Diagnosis → medications discovery across the FULL library.
//
// What this does: given a diagnosis (plus symptoms), it returns
//   (a) every medicine NAMED in our candidate guideline evidence for
//       matching conditions, with the exact statement and citation, and
//   (b) every matching book / information centre from the full evidence
//       directory (searchObgynSources), so the doctor knows where else
//       to look.
//
// What this does NOT do:
//   - It never invents a medicine. If no candidate evidence names a
//     medicine for the diagnosis, the medicines list is EMPTY and says so.
//     The books/centres list is then the answer: go read them.
//   - It never recommends, ranks, or doses. Candidate evidence is
//     research material for clinician review (see candidate-pathway-
//     evidence.ts), not an approved pathway — approved pathways stay at
//     ZERO until a named clinician and pharmacist sign one off.
//   - It never touches the trials page: trials are one shelf in the
//     library, and this search covers all shelves.
//
// Candidate evidence was compiled from public guidelines read live
// 2026-10-19. Where a guideline's full text was paywalled, the entry
// says so and confidence is labelled there.

import {
  CANDIDATE_PATHWAY_EVIDENCE,
  type CandidateEvidence,
} from './candidate-pathway-evidence';
import {
  searchObgynSources,
  type EvidenceSource,
  type Jurisdiction,
} from './obgyn-data';

export interface MedicationStatementHit {
  /** The guideline statement, in its own terms. Never a prescription. */
  text: string;
  condition: string;
  aspect: CandidateEvidence['aspect'];
  citation: CandidateEvidence['citation'];
  flags: string[];
}

export interface DiagnosisMedicationHit {
  /** Medicine name exactly as written in the guideline statement. */
  name: string;
  statements: MedicationStatementHit[];
}

export interface DiagnosisMedicationResult {
  medicines: DiagnosisMedicationHit[];
  /** Matching books / information centres from the full directory. */
  sources: EvidenceSource[];
}

function normalize(value: string): string {
  // US -> UK spelling aliases, applied to BOTH sides of every match
  // (queries and evidence text pass through this same function), so a
  // doctor typing US spellings still reaches the UK-spelled evidence.
  return value
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, ' ')
    .replace(/hemorrhage/g, 'haemorrhage')
    .replace(/preeclampsia/g, 'pre-eclampsia')
    .replace(/anemia/g, 'anaemia')
    .replace(/edema/g, 'oedema')
    .replace(/estrogen/g, 'oestrogen')
    .replace(/cesarean/g, 'caesarean')
    .replace(/fetus/g, 'foetus')
    .replace(/tumor/g, 'tumour')
    .replace(/post-partum/g, 'postpartum')
    .replace(/post partum/g, 'postpartum');
}

// Severity and certainty words describe a presentation, they do not
// identify a condition, so they never count as matching tokens.
const QUALIFIER_TOKENS = new Set([
  'severe',
  'mild',
  'moderate',
  'acute',
  'chronic',
  'suspected',
]);

function tokensOf(value: string): string[] {
  return normalize(value)
    .split(/\s+/)
    .filter(token => token.length >= 3 && !QUALIFIER_TOKENS.has(token));
}

/**
 * Find medicines named across the whole evidence corpus for a diagnosis.
 * Medicines come ONLY from candidate guideline evidence; books/centres
 * come from the full evidence directory. Empty medicines + a sources
 * list is a valid, honest result — never padded.
 */
export function searchDiagnosisMedications(
  query: string,
  jurisdiction: Jurisdiction
): DiagnosisMedicationResult {
  const normalized = normalize(query);
  const tokens = tokensOf(query);
  const sources = searchObgynSources(query, jurisdiction, 10);
  if (!tokens.length) return { medicines: [], sources };

  // Precision rule (fixed 2026-10-24 after the doctor-testing matrix
  // showed single-token leakage: "gestational diabetes" returned
  // hypertension medicines because it shares the token "gestational"
  // with "Gestational hypertension"). A statement's medicines are
  // included ONLY when:
  //   (a) its entry matches the query — the full query string appears
  //       in the condition name, or a single-token query's token does,
  //       or at least two query tokens appear in the condition name
  //       (so "postpartum haemorrhage, heavy bleeding" still matches
  //       while "gestational diabetes" does not); or
  //   (b) the same threshold is met inside the statement text itself; or
  //   (c) a query token names a medicine (medicine-name queries).
  // Anything else stays out, so an unmatched diagnosis returns an
  // honest empty list instead of a neighbouring condition's medicines.
  // Known breadth that remains by design: a single generic token such
  // as "pregnancy" matches every statement mentioning it, including
  // low-certainty case-study entries — each hit still shows its
  // condition, aspect and flags so the doctor can see the context.
  const queryNorm = normalized.trim();
  const hits = (corpus: string) =>
    tokens.length === 1
      ? corpus.includes(tokens[0])
      : tokens.filter(token => corpus.includes(token)).length >= 2;
  const byMedicine = new Map<string, DiagnosisMedicationHit>();
  for (const entry of CANDIDATE_PATHWAY_EVIDENCE) {
    const conditionNorm = normalize(entry.condition);
    const entryMatches =
      queryNorm.length > 0 &&
      (conditionNorm.includes(queryNorm) || hits(conditionNorm));
    for (const statement of entry.statements) {
      const statementNorm = normalize(statement.text);
      const statementMatches = hits(statementNorm);
      const medicineMatch = statement.medicines.some(medicine =>
        tokens.some(token => normalize(medicine).includes(token))
      );
      if (!entryMatches && !statementMatches && !medicineMatch) continue;
      for (const medicine of statement.medicines) {
        const key = medicine.toLowerCase();
        const hit = byMedicine.get(key) ?? { name: medicine, statements: [] };
        hit.statements.push({
          text: statement.text,
          condition: entry.condition,
          aspect: entry.aspect,
          citation: entry.citation,
          flags: entry.flags,
        });
        byMedicine.set(key, hit);
      }
    }
  }

  const medicines = [...byMedicine.values()].sort((a, b) =>
    a.name.localeCompare(b.name)
  );
  return { medicines, sources };
}
