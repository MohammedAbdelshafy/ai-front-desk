// Approved medication pathways — the ONLY way medicine suggestions may
// ever appear in this app.
//
// Policy (quality control): a pathway becomes visible to doctors only when
// ALL of the following are recorded:
//   - a named clinician reviewer (name, credential, review date),
//   - a named pharmacist reviewer (name, credential, review date),
//   - the exact guideline cited (title, publisher, edition, section, URL),
//   - the jurisdictions it applies to,
//   - a scheduled re-review date.
//
// Anything less than this stays invisible — including to the developers.
// "Most accurate" is earned through this gate, not asserted by software.
// There are currently ZERO approved pathways. That number only moves when
// a real clinician and a real pharmacist sign a pathway off.

export interface PathwayMedicine {
  /** Exact generic or product name as written in the cited guideline. */
  name: string;
  /** What the cited guideline says about this medicine for this diagnosis. */
  role: 'first-line' | 'alternative' | 'not-recommended-here';
  /** One-line reason, paraphrased from the cited guideline section. No dosing. */
  note: string;
}

export interface MedicationPathway {
  id: string;
  diagnosis: string;
  synonyms: string[];
  jurisdictions: string[];
  medicines: PathwayMedicine[];
  guideline: {
    title: string;
    publisher: string;
    edition: string;
    section: string;
    url: string;
  };
  clinicianReviewer: { name: string; credential: string; date: string };
  pharmacistReviewer: { name: string; credential: string; date: string };
  /** ISO date when this pathway must be re-reviewed or it auto-expires. */
  reviewDue: string;
  status: 'approved' | 'draft' | 'blocked';
}

/** The registry. Empty until a pathway clears the approval gate. */
export const MEDICATION_PATHWAYS: MedicationPathway[] = [];

/** What the UI may show. Drafts and blocked entries are never rendered. */
export const APPROVED_PATHWAYS: MedicationPathway[] = MEDICATION_PATHWAYS.filter(
  pathway => pathway.status === 'approved'
);

/** Displayed verbatim in the app so every doctor sees the rule. */
export const PATHWAY_APPROVAL_REQUIREMENTS: string[] = [
  'Named clinician reviewer with credential and review date',
  'Named pharmacist reviewer with credential and review date',
  'Exact guideline cited: title, publisher, edition, section, link',
  'Jurisdictions the pathway applies to',
  'Scheduled re-review date — expired pathways disappear automatically',
];
