// Candidate pathway evidence — research candidates for clinician review.
//
// STATUS: CANDIDATE. Nothing in this file is an approved pathway and nothing
// here may be presented to a doctor as a recommendation. Each entry records
// what a named public guideline states, with its citation, so a reviewing
// clinician can verify it against the primary source and decide what — if
// anything — becomes an approved pathway (see medication-pathways.ts).
//
// Compiled from public sources read live 2026-10-19. Where sources disagree
// or an edition changed a position, the disagreement is flagged, not resolved.

export interface CandidateStatement {
  /** What the guideline states, in its own terms. Never a prescription. */
  text: string;
  /** Medicines named by the guideline in this statement. */
  medicines: string[];
}

export interface CandidateEvidence {
  id: string;
  condition: string;
  aspect: 'prevention' | 'treatment' | 'safety-reference' | 'case-study';
  statements: CandidateStatement[];
  citation: {
    title: string;
    publisher: string;
    edition: string;
    section: string;
    url: string;
  };
  /** Where guidelines disagree or an edition changed a position. */
  flags: string[];
  /** Reviewer notes: confidence, paywalls, what still needs checking. */
  reviewerNotes: string[];
  status: 'candidate';
}

export const CANDIDATE_PATHWAY_EVIDENCE: CandidateEvidence[] = [
  {
    id: 'cand-pph-prevention-who2025',
    condition: 'Postpartum haemorrhage — prevention',
    aspect: 'prevention',
    statements: [
      {
        text: 'A quality-assured uterotonic is recommended for all births; use only one of oxytocin, carbetocin or misoprostol (Rec 7).',
        medicines: ['oxytocin', 'carbetocin', 'misoprostol'],
      },
      {
        text: 'Oxytocin 10 IU IM/IV is first-listed for prevention of PPH for all births, given immediately (preferably within 1 minute) after birth; requires 2–8 °C cold chain (Rec 7.1).',
        medicines: ['oxytocin'],
      },
      {
        text: 'Carbetocin 100 µg IM/IV; heat-stable formulation where the cold chain cannot be guaranteed (Rec 7.2).',
        medicines: ['carbetocin'],
      },
      {
        text: 'Misoprostol 400 µg or 600 µg orally; increases shivering/fever/diarrhoea (self-limiting); usable by lay health workers (Rec 7.3).',
        medicines: ['misoprostol'],
      },
      {
        text: 'Ergometrine/methylergometrine, oxytocin+ergometrine fixed-dose combo, and injectable prostaglandins are NOT recommended for PPH prevention (Rec 9/9.1 — updated; changed from the 2018 guidance).',
        medicines: ['ergometrine', 'methylergometrine'],
      },
      {
        text: 'Tranexamic acid is NOT recommended for PPH prevention at vaginal or caesarean birth (Rec 14/15 — new).',
        medicines: ['tranexamic acid'],
      },
    ],
    citation: {
      title:
        'Consolidated guidelines for the prevention, diagnosis and treatment of postpartum haemorrhage',
      publisher: 'World Health Organization, Geneva',
      edition: '1st edition, 2025 (ISBN 978-92-4-011563-7)',
      section: 'Section 3.3, Recommendations 7–9, 14–15',
      url: 'https://www.pphaction.net/papers/9789240115637-eng.pdf',
    },
    flags: [
      'NICE NG235 (2023) still includes an oxytocin+ergometrine option for active third-stage management — direct disagreement with WHO 2025 on ergometrine for prevention.',
    ],
    reviewerNotes: [
      'Full guideline text read live 2026-10-19.',
      'Confirm which position the tool reflects, and for which settings.',
    ],
    status: 'candidate',
  },
  {
    id: 'cand-pph-treatment-who2025',
    condition: 'Postpartum haemorrhage — treatment',
    aspect: 'treatment',
    statements: [
      {
        text: 'IV oxytocin is the recommended first-line uterotonic for PPH treatment, even after prophylactic use (Rec 24).',
        medicines: ['oxytocin'],
      },
      {
        text: 'If IV oxytocin is unavailable or bleeding is unresponsive: IV ergometrine, oxytocin+ergometrine fixed-dose combo, or a prostaglandin (including sublingual misoprostol 800 µg). No evidence to rank second-line agents (Rec 25).',
        medicines: ['ergometrine', 'misoprostol'],
      },
      {
        text: 'Early IV tranexamic acid within 3 hours of birth: fixed dose 1 g IV over 10 min; second 1 g if bleeding continues after 30 min or restarts within 24 h. Beyond 3 h the guideline does not support use (Rec 27).',
        medicines: ['tranexamic acid'],
      },
      {
        text: 'Stated contraindication: avoid TXA with a clear contraindication to antifibrinolytics, e.g. known thromboembolic event during pregnancy (Rec 27).',
        medicines: ['tranexamic acid'],
      },
      {
        text: 'Standardized first-response bundle: rapid uterine massage + oxytocic + TXA + IV fluids + genital-tract examination + escalation (Rec 29).',
        medicines: ['tranexamic acid'],
      },
    ],
    citation: {
      title:
        'Consolidated guidelines for the prevention, diagnosis and treatment of postpartum haemorrhage',
      publisher: 'World Health Organization, Geneva',
      edition: '1st edition, 2025 (ISBN 978-92-4-011563-7)',
      section: 'Section 3.5, Recommendations 24–29',
      url: 'https://www.pphaction.net/papers/9789240115637-eng.pdf',
    },
    flags: [
      'ACOG PB 183 (2017) positions TXA only after initial therapy fails; WHO 2025 places it in the first-response bundle.',
      'NICE NG235 rec 1.10.35 gives TXA 1 g IV without stating the 3-hour window — confirm whether timing appears elsewhere in NICE before treating the omission as intentional.',
    ],
    reviewerNotes: [
      'Full guideline text read live 2026-10-19.',
      'The tool needs one coherent TXA rule — reviewer decides which authority governs.',
    ],
    status: 'candidate',
  },
  {
    id: 'cand-preeclampsia-who2011',
    condition: 'Pre-eclampsia / eclampsia',
    aspect: 'treatment',
    statements: [
      {
        text: 'Calcium 1.5–2.0 g elemental/day in low-intake areas; aspirin 75 mg for high-risk women, initiated before 20 weeks (prevention).',
        medicines: ['calcium', 'aspirin'],
      },
      {
        text: 'Antihypertensives for severe hypertension — the guideline names NO first-line agent; choice and route rest on the prescribing clinician’s experience, cost and local availability.',
        medicines: [],
      },
      {
        text: 'Magnesium sulfate preferred over other anticonvulsants for eclampsia prevention in severe pre-eclampsia and for eclampsia treatment; full IV or IM regimens.',
        medicines: ['magnesium sulfate'],
      },
      {
        text: 'NOT recommended: rest/bedrest, salt restriction, vitamin D, vitamins C+E, diuretics (particularly thiazides) for prevention, corticosteroids for HELLP.',
        medicines: [],
      },
    ],
    citation: {
      title:
        'WHO recommendations for prevention and treatment of pre-eclampsia and eclampsia',
      publisher: 'World Health Organization, Geneva',
      edition: '2011 (ISBN 978-92-4-154833-5) — no newer consolidated edition found',
      section: 'Box 1 (recommended), Box 2 (not recommended)',
      url: 'https://Preeclampsia.org/frontend/assets/img/advocacy_resource/2011c-who_pe_final_1584190059.pdf',
    },
    flags: [
      'WHO launched a 10-year pregnancy-hypertension roadmap (Oct 2025 news) — watch for a forthcoming revision of this 2011 edition.',
    ],
    reviewerNotes: [
      'Full guideline text read live 2026-10-19.',
      'The guideline states no explicit contraindications for individual drugs.',
    ],
    status: 'candidate',
  },
  {
    id: 'cand-htn-pregnancy-acog222',
    condition: 'Gestational hypertension / pre-eclampsia',
    aspect: 'treatment',
    statements: [
      {
        text: 'Acute-onset severe hypertension (≥160/110 persistent ≥15 min): treat within 30–60 min with IV hydralazine, IV labetalol, or oral immediate-release nifedipine — no superiority ranking; any of the three may be used.',
        medicines: ['hydralazine', 'labetalol', 'nifedipine'],
      },
      {
        text: 'Avoid labetalol in asthma, preexisting myocardial disease, decompensated cardiac function, heart block, bradycardia.',
        medicines: ['labetalol'],
      },
      {
        text: 'Magnesium sulfate is the drug of choice for seizure prevention/treatment in severe features/eclampsia. Explicit contraindications: myasthenia gravis, hypocalcemia, moderate-to-severe renal failure, cardiac ischemia, heart block, myocarditis.',
        medicines: ['magnesium sulfate'],
      },
      {
        text: 'Aspirin 81 mg/day from 12–28 weeks (optimally before 16 weeks) to delivery for prophylaxis in at-risk women.',
        medicines: ['aspirin'],
      },
    ],
    citation: {
      title: 'Gestational Hypertension and Preeclampsia — Practice Bulletin No. 222',
      publisher: 'American College of Obstetricians and Gynecologists',
      edition: '2020 (Obstet Gynecol 2020;135(6):e237–e260)',
      section: 'Acute severe HTN management; MgSO4; aspirin prophylaxis',
      url: 'https://www.acog.org/clinical/clinical-guidance/practice-bulletin/articles/2020/06/gestational-hypertension-and-preeclampsia',
    },
    flags: [
      'Aspirin dose differs across authorities: 75 mg (WHO) vs 81 mg (ACOG) vs 75–150 mg (NICE) — needs one tool position or an explicit range.',
    ],
    reviewerNotes: [
      'Full bulletin PDF read live 2026-10-19.',
      'MgSO4 regimens differ between WHO/ACOG/NICE — reviewer decides which protocol the tool encodes.',
    ],
    status: 'candidate',
  },
  {
    id: 'cand-htn-pregnancy-nice133',
    condition: 'Hypertension in pregnancy',
    aspect: 'treatment',
    statements: [
      {
        text: 'Labetalol is first-line for chronic hypertension, gestational hypertension and pre-eclampsia; nifedipine if labetalol unsuitable; methyldopa if neither suitable (stop within 2 days after birth).',
        medicines: ['labetalol', 'nifedipine', 'methyldopa'],
      },
      {
        text: 'Severe hypertension in critical care: labetalol (oral/IV), oral nifedipine, or IV hydralazine — treat immediately.',
        medicines: ['labetalol', 'nifedipine', 'hydralazine'],
      },
      {
        text: 'MgSO4 per Collaborative Eclampsia Trial regimen (4 g IV over 5–15 min, then 1 g/h for 24 h). Do NOT use diazepam, phenytoin or other anticonvulsants as an alternative in eclampsia.',
        medicines: ['magnesium sulfate'],
      },
      {
        text: 'ACE inhibitors and ARBs are contraindicated in pregnancy — stop within 2 working days of pregnancy notification. Thiazide/thiazide-like diuretics: avoid.',
        medicines: [],
      },
      {
        text: 'Aspirin 75–150 mg daily from 12 weeks to birth for high-risk or >1 moderate risk factor.',
        medicines: ['aspirin'],
      },
      {
        text: 'Postnatal: offer enalapril (with renal/K+ monitoring); avoid diuretics and ARBs while breastfeeding.',
        medicines: ['enalapril'],
      },
    ],
    citation: {
      title: 'Hypertension in pregnancy: diagnosis and management',
      publisher: 'National Institute for Health and Care Excellence (UK)',
      edition: 'NG133 (2019; reviewed 2023)',
      section: 'Recommendations 1.3–1.5, 1.8–1.9',
      url: 'https://www.nice.org.uk/guidance/ng133/chapter/Recommendations',
    },
    flags: [
      'Antihypertensive hierarchy differs: WHO 2011 names none; ACOG ranks three equally for acute severe HTN; NICE puts labetalol first for non-severe HTN — present as parallel positions, not merged.',
    ],
    reviewerNotes: [
      'Full recommendations read live 2026-10-19.',
      'ACE inhibitor/ARB and thiazide contraindications are explicit in NICE; WHO 2011 does not address them.',
    ],
    status: 'candidate',
  },
  {
    id: 'cand-pph-acog183-nice235',
    condition: 'Postpartum haemorrhage — cross-authority positions',
    aspect: 'treatment',
    statements: [
      {
        text: 'ACOG: uterotonic agents should be first-line for atonic PPH; choice of specific agent at provider discretion — none identified as superior. TXA when primary therapy fails, especially effective within 3 hours of birth.',
        medicines: ['tranexamic acid'],
      },
      {
        text: 'NICE NG235: first-line uterotonic depends on prophylaxis received (Table 12); TXA 1 g IV over 10 min alongside uterotonics, repeat after ≥30 min if bleeding continues.',
        medicines: ['tranexamic acid'],
      },
      {
        text: 'NICE NG235 1.10.9: oxytocin+ergometrine contraindicated in severe hypertension, pre-eclampsia, eclampsia, severe cardiac/hepatic/renal disease.',
        medicines: ['ergometrine'],
      },
    ],
    citation: {
      title: 'Postpartum Hemorrhage (PB 183) + Intrapartum care (NG235)',
      publisher: 'ACOG (2017) + NICE (2023)',
      edition: 'PB 183 (2017); NG235 (2023, amended 2024)',
      section: 'PB 183: atonic PPH management; NG235: 1.10.9–1.10.11, 1.10.33–1.10.35, Table 12',
      url: 'https://www.nice.org.uk/guidance/ng235/chapter/Recommendations',
    },
    flags: [
      'ACOG PB 183 full text is paywalled; medication statements verified via two independent secondary summaries — a reviewer with ACOG access should confirm exact wording.',
    ],
    reviewerNotes: [
      'ACOG statements: medium confidence (consistent across sources, paywall-limited).',
      'NICE recommendations read live 2026-10-19.',
    ],
    status: 'candidate',
  },
  {
    id: 'cand-case-studies',
    condition: 'Illustrative prescribing cases (low-certainty evidence)',
    aspect: 'case-study',
    statements: [
      {
        text: 'Chronic HTN → superimposed severe preeclampsia with cerebrovascular accident: labetalol + extended-release nifedipine as first-line maintenance; oral nifedipine preferred for acute severe HTN (Wang & Wei, Medicine 2025).',
        medicines: ['labetalol', 'nifedipine'],
      },
      {
        text: 'Twin pregnancy, superimposed preeclampsia + severe OSA: nifedipine stopped to allow safe MgSO4 use; hydralazine inpatient; nocturnal auto-CPAP added — BP/proteinuria normalized, pregnancy prolonged 49 days (Kim et al., BMC Pregnancy Childbirth 2020).',
        medicines: ['nifedipine', 'magnesium sulfate', 'hydralazine'],
      },
      {
        text: 'Ulcerative colitis in pregnancy/lactation: vedolizumab continued through pregnancy and breastfeeding (shared decision); twins at 34 weeks, no complications (Pinto et al., 2024).',
        medicines: ['vedolizumab'],
      },
      {
        text: 'Bipolar disorder: lithium continued during exclusive breastfeeding with infant serum monitoring (infant levels 10–17% of maternal at 1 month) (Viguera et al., 2012).',
        medicines: ['lithium'],
      },
    ],
    citation: {
      title: 'Four open-access case studies (PMC)',
      publisher: 'Medicine; BMC Pregnancy Childbirth; Clin Exp Gastroenterol; Arch Womens Ment Health',
      edition: '2025; 2020; 2024; 2012',
      section: 'Case reports as indexed',
      url: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12150912/',
    },
    flags: [
      'Single-case and small-series evidence is hypothesis-generating only.',
    ],
    reviewerNotes: [
      'Reviewer decides whether the tool cites these as illustrative cases with explicit low-certainty labelling.',
      'Case 1 details from abstract-level indexed content; full text not read.',
    ],
    status: 'candidate',
  },
];

/** Case-study and safety-reference URLs carried separately for the UI. */
export const CANDIDATE_CASE_URLS: { label: string; url: string }[] = [
  {
    label: 'Wang & Wei 2025 — chronic HTN, superimposed preeclampsia, stroke',
    url: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12150912/',
  },
  {
    label: 'Kim et al. 2020 — twin pregnancy, preeclampsia + OSA, CPAP adjunct',
    url: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC7268687/',
  },
  {
    label: 'Pinto et al. 2024 — vedolizumab in pregnancy & lactation',
    url: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC11122291/',
  },
  {
    label: 'Viguera et al. 2012 — lithium during breastfeeding',
    url: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC3629811/',
  },
];
