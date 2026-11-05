/**
 * Clinician-approved medication pathway registry for Dr. Mia.
 * Intentionally empty until each pathway has current source and specialist/
 * medication-safety reviewer approval. It never diagnoses or prescribes.
 */
export type MedicationRole = 'first-line' | 'alternative' | 'not-recommended-here';
export type MedicationJurisdiction = 'EG' | 'US' | 'UK' | 'GLOBAL';

export interface MedicationTeaching {
  whyConsider: string;
  mechanism: string;
  evidenceSummary: string;
  alternatives: string;
  commonAdverseEffects: string;
  seriousWarnings: string;
  contraindications: string;
  interactions: string;
  pregnancyLactation: string;
  monitoring: string;
  counseling: string;
  doseContext: string;
  populationLimits: string;
}
export interface PathwayMedicine {
  name: string;
  role: MedicationRole;
  rationale: string;
  teaching: MedicationTeaching;
}
export interface PathwaySource {
  title: string;
  publisher: string;
  edition: string;
  version: string;
  section: string;
  effectiveDate: string;
  url: string;
}
export interface PathwayReviewer {
  name: string;
  credential: string;
  reviewedOn: string;
}
export interface MedicationPathway {
  id: string;
  diagnosisCode: string;
  diagnosis: string;
  jurisdictions: MedicationJurisdiction[];
  requiredPatientFactors: string[];
  medicines: PathwayMedicine[];
  sources: PathwaySource[];
  clinicianReviewer: PathwayReviewer;
  pharmacistReviewer: PathwayReviewer;
  reviewDueOn: string;
  status: 'approved' | 'draft' | 'blocked';
}

/** No actual medication entries are enabled in this initial release. */
export const MEDICATION_PATHWAYS: MedicationPathway[] = [];

function localDateString(value: Date): string {
  return [
    value.getFullYear(),
    String(value.getMonth() + 1).padStart(2, '0'),
    String(value.getDate()).padStart(2, '0'),
  ].join('-');
}
function validIsoDate(value: unknown): value is string {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(value + 'T00:00:00.000Z');
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}
function nonEmpty(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}
function validReviewer(reviewer: PathwayReviewer, today: string): boolean {
  return Boolean(
    reviewer && nonEmpty(reviewer.name) && nonEmpty(reviewer.credential) &&
    validIsoDate(reviewer.reviewedOn) && reviewer.reviewedOn <= today
  );
}

/** Exact diagnosis code + current jurisdiction + all review/source gates. */
export function getApprovedMedicationPathways(
  diagnosisCode: string,
  jurisdiction: MedicationJurisdiction = 'EG',
  today: Date = new Date(),
): MedicationPathway[] {
  const requestedCode = String(diagnosisCode || '').trim().toUpperCase();
  if (!requestedCode) return [];
  const todayIso = localDateString(today);
  const teachingFields: (keyof MedicationTeaching)[] = [
    'whyConsider', 'mechanism', 'evidenceSummary', 'alternatives',
    'commonAdverseEffects', 'seriousWarnings', 'contraindications',
    'interactions', 'pregnancyLactation', 'monitoring', 'counseling',
    'doseContext', 'populationLimits',
  ];

  return MEDICATION_PATHWAYS.filter(pathway => {
    if (
      pathway.status !== 'approved' ||
      !nonEmpty(pathway.id) ||
      !nonEmpty(pathway.diagnosisCode) ||
      pathway.diagnosisCode.trim().toUpperCase() !== requestedCode ||
      !nonEmpty(pathway.diagnosis) ||
      !Array.isArray(pathway.jurisdictions) ||
      !pathway.jurisdictions.includes(jurisdiction) ||
      !Array.isArray(pathway.requiredPatientFactors) ||
      pathway.requiredPatientFactors.length === 0 ||
      !Array.isArray(pathway.medicines) ||
      pathway.medicines.length === 0 ||
      !Array.isArray(pathway.sources) ||
      pathway.sources.length === 0 ||
      !validReviewer(pathway.clinicianReviewer, todayIso) ||
      !validReviewer(pathway.pharmacistReviewer, todayIso) ||
      !validIsoDate(pathway.reviewDueOn) ||
      pathway.reviewDueOn < todayIso
    ) return false;

    const dueMs = Date.parse(pathway.reviewDueOn + 'T00:00:00.000Z');
    const clinicianMs = Date.parse(pathway.clinicianReviewer.reviewedOn + 'T00:00:00.000Z');
    const pharmacistMs = Date.parse(pathway.pharmacistReviewer.reviewedOn + 'T00:00:00.000Z');
    if (
      dueMs < clinicianMs || dueMs < pharmacistMs ||
      dueMs - clinicianMs > 366 * 86400000 ||
      dueMs - pharmacistMs > 366 * 86400000
    ) return false;

    if (!pathway.sources.every(source =>
      nonEmpty(source.title) && nonEmpty(source.publisher) &&
      nonEmpty(source.edition) && nonEmpty(source.version) &&
      nonEmpty(source.section) && validIsoDate(source.effectiveDate) &&
      source.effectiveDate <= todayIso && nonEmpty(source.url) &&
      source.url.startsWith('https://')
    )) return false;

    return pathway.medicines.every(medicine =>
      nonEmpty(medicine.name) &&
      ['first-line', 'alternative', 'not-recommended-here'].includes(medicine.role) &&
      nonEmpty(medicine.rationale) &&
      teachingFields.every(field => nonEmpty(medicine.teaching?.[field]))
    );
  });
}
