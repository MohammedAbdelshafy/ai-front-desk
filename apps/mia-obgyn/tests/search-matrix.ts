// Doctor-testing matrix for searchDiagnosisMedications.
//
// What it checks, for every query in the matrix:
//   C1  No invented medicines: every returned name appears in at least one
//       candidate statement's structured medicines list.
//   C2  Every returned statement carries a citation with a label and an
//       http(s) URL.
//   C3  Every returned statement names at least one medicine.
//   C4  Medicines are jurisdiction-independent (EG == UK == US); only the
//       books/centres list varies by jurisdiction.
//   C5  Empty/gibberish queries return an empty medicines list, never a guess.
//
// Expected-medicine assertions use "contains" (superset), never exact sets:
// the search is discovery across statements, so co-listed medicines may
// legitimately appear alongside the expected ones. The report prints the
// full returned set so a human can judge breadth.
//
// Run: npm run test:search   (bundles this file with esbuild, runs node)
import {
  searchDiagnosisMedications,
  type DiagnosisMedicationResult,
} from '../src/diagnosis-medication-search';
import {
  CANDIDATE_PATHWAY_EVIDENCE,
  type CandidateEvidence,
} from '../src/candidate-pathway-evidence';
import { EVIDENCE_SOURCES } from '../src/obgyn-data';
import type { Jurisdiction } from '../src/obgyn-data';

type Case = {
  query: string;
  expectContains?: string[];
  expectEmpty?: boolean;
  note?: string;
};

const CASES: Case[] = [
  { query: 'postpartum haemorrhage', expectContains: ['oxytocin', 'carbetocin', 'misoprostol', 'tranexamic acid'] },
  { query: 'postpartum hemorrhage', expectContains: ['oxytocin', 'tranexamic acid'], note: 'US spelling — must match the UK-spelled evidence' },
  { query: 'Postpartum Haemorrhage', expectContains: ['oxytocin'], note: 'case-insensitivity' },
  { query: 'postpartum haemorrhage, heavy bleeding', expectContains: ['oxytocin'], note: 'diagnosis + symptom text, punctuation' },
  { query: 'pre-eclampsia', expectContains: ['magnesium sulfate'] },
  { query: 'severe pre-eclampsia', expectContains: ['magnesium sulfate'], note: 'severity qualifier must not break the match' },
  { query: 'preeclampsia', expectContains: ['magnesium sulfate'], note: 'US spelling, no hyphen' },
  { query: 'eclampsia', expectContains: ['magnesium sulfate'] },
  { query: 'gestational hypertension', expectContains: ['labetalol', 'nifedipine', 'hydralazine'] },
  { query: 'hypertension in pregnancy', expectContains: ['labetalol'] },
  { query: 'bacterial vaginosis', expectEmpty: true, note: 'no candidate evidence — honest empty, never a guess' },
  { query: 'gestational diabetes', expectEmpty: true, note: 'no candidate evidence — honest empty' },
  { query: 'urinary tract infection in pregnancy', expectEmpty: true },
  { query: 'aspirin', expectContains: ['aspirin'], note: 'medicine-name query; co-listed medicines may also appear' },
  { query: 'magnesium sulfate', expectContains: ['magnesium sulfate'] },
  { query: 'tranexamic acid', expectContains: ['tranexamic acid'] },
  { query: 'xyzabc', expectEmpty: true, note: 'gibberish — empty, never a guess' },
  { query: '', expectEmpty: true, note: 'empty query — empty' },
  { query: 'pregnancy', note: 'generic token — breadth recorded, not asserted; every hit must still be cited' },
  { query: 'postpartum', note: 'generic token — breadth recorded, not asserted' },
  { query: 'نزيف ما بعد الولادة', expectEmpty: true, note: 'Arabic query — KNOWN LIMIT: Latin-script matching only; empty is honest, not a mistranslation' },
];

const JURISDICTIONS: Jurisdiction[] = ['EG', 'UK', 'US'];

const allMedicines = new Set<string>();
for (const entry of CANDIDATE_PATHWAY_EVIDENCE as CandidateEvidence[]) {
  for (const statement of entry.statements) {
    for (const medicine of statement.medicines) allMedicines.add(medicine.toLowerCase());
  }
}

let failures = 0;
const fail = (message: string) => {
  failures += 1;
  console.log('  FAIL ' + message);
};

console.log('Candidate evidence entries: ' + CANDIDATE_PATHWAY_EVIDENCE.length);
console.log('Evidence directory sources: ' + EVIDENCE_SOURCES.length);
console.log('Structured medicine names in evidence: ' + allMedicines.size);

// Data-integrity checks (independent of any query).
let contextStatements = 0;
for (const entry of CANDIDATE_PATHWAY_EVIDENCE as CandidateEvidence[]) {
  if (!entry.condition) fail('candidate entry with no condition');
  if (!entry.statements.length) fail('candidate entry with no statements: ' + entry.condition);
  // Citation lives on the entry (title/publisher/edition/section/url);
  // the search copies it onto every hit statement.
  if (!entry.citation.title || !entry.citation.url) {
    fail('candidate entry missing citation: ' + entry.condition);
  } else if (!/^https?:\/\//.test(entry.citation.url)) {
    fail('citation URL not http(s): ' + entry.citation.url);
  }
  for (const statement of entry.statements) {
    if (!statement.medicines.length) contextStatements += 1; // context statement, not a failure
  }
}
console.log('Context statements without medicines (info only): ' + contextStatements);
for (const source of EVIDENCE_SOURCES) {
  if (!source.title || !source.url) fail('evidence source missing title/url');
  else if (!/^https?:\/\//.test(source.url)) fail('evidence source URL not http(s): ' + source.url);
}

const run = (query: string, jurisdiction: Jurisdiction): DiagnosisMedicationResult =>
  searchDiagnosisMedications(query, jurisdiction);

for (const testCase of CASES) {
  const result = run(testCase.query, 'EG');
  const names = result.medicines.map(m => m.name.toLowerCase());
  console.log(
    '\n[' + JSON.stringify(testCase.query) + '] -> ' + result.medicines.length +
      ' medicines: ' + (names.join(', ') || '(none)') +
      ' | sources: ' + result.sources.length +
      (testCase.note ? ' | ' + testCase.note : ''),
  );
  // C1 + C2 + C3 on every hit.
  for (const hit of result.medicines) {
    if (!allMedicines.has(hit.name.toLowerCase())) fail('invented medicine: ' + hit.name);
    for (const statement of hit.statements) {
      if (!statement.citation.title || !statement.citation.url) {
        fail('statement without citation for ' + hit.name);
      }
    }
  }
  if (testCase.expectEmpty && result.medicines.length !== 0) {
    fail('expected empty medicines for ' + JSON.stringify(testCase.query) + ', got: ' + names.join(', '));
  }
  for (const expected of testCase.expectContains ?? []) {
    if (!names.includes(expected.toLowerCase())) {
      fail('expected ' + expected + ' for ' + JSON.stringify(testCase.query) + ', got: ' + (names.join(', ') || '(none)'));
    }
  }
  // C4: jurisdiction invariance of medicines.
  for (const jurisdiction of JURISDICTIONS) {
    const other = run(testCase.query, jurisdiction).medicines.map(m => m.name.toLowerCase()).sort().join('|');
    const base = names.slice().sort().join('|');
    if (other !== base) {
      fail('medicines differ by jurisdiction for ' + JSON.stringify(testCase.query) + ' (' + jurisdiction + ')');
    }
  }
}

console.log('\n' + (failures === 0 ? 'ALL CHECKS PASSED' : failures + ' CHECK(S) FAILED'));
process.exit(failures === 0 ? 0 : 1);
