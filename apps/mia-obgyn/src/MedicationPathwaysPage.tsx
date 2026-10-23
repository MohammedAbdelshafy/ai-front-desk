import { useState } from 'react';
import { AlertTriangle, Pill, Search, ShieldCheck } from 'lucide-react';
import { searchObgynSources } from './obgyn-data';
import {
  getApprovedMedicationPathways,
  MEDICATION_PATHWAYS,
  type PathwayMedicine,
} from './clinical-medication-pathways';
import './medication-pathways.css';

export default function MedicationPathwaysPage() {
  const [diagnosisCode, setDiagnosisCode] = useState('');
  const [diagnosisLabel, setDiagnosisLabel] = useState('');
  const [diagnosisConfirmed, setDiagnosisConfirmed] = useState(false);
  const [ageYears, setAgeYears] = useState('29');
  const [weightKg, setWeightKg] = useState('');
  const [allergies, setAllergies] = useState('');
  const [allergiesReviewed, setAllergiesReviewed] = useState(false);
  const [currentMedicines, setCurrentMedicines] = useState('');
  const [medicinesReviewed, setMedicinesReviewed] = useState(false);
  const [medicalHistory, setMedicalHistory] = useState('');
  const [pregnancyStatus, setPregnancyStatus] = useState('unknown');
  const [lactationStatus, setLactationStatus] = useState('unknown');
  const [renalStatus, setRenalStatus] = useState('unknown');
  const [hepaticStatus, setHepaticStatus] = useState('unknown');
  const [observations, setObservations] = useState('');
  const [localProtocol, setLocalProtocol] = useState('unknown');
  const [submitted, setSubmitted] = useState(false);
  const resetResult = () => setSubmitted(false);
  const isUnknown = (value: string) =>
    /\b(unknown|not known|not assessed|not reconciled|not reviewed|unsure|uncertain|not confirmed)\b/i.test(value);

  const ageNumber = Number(ageYears);
  const ageComplete = ageYears.trim() !== '' && Number.isInteger(ageNumber) && ageNumber >= 0 && ageNumber <= 130;
  const allergiesComplete = allergiesReviewed && allergies.trim() !== '' && !isUnknown(allergies);
  const medicinesComplete = medicinesReviewed && currentMedicines.trim() !== '' && !isUnknown(currentMedicines);

  const blockers: string[] = [];
  if (!diagnosisCode.trim()) blockers.push('Enter the exact diagnosis code used by the local pathway.');
  if (!diagnosisLabel.trim()) blockers.push('Enter the diagnosis label confirmed by the responsible clinician.');
  if (!diagnosisConfirmed) blockers.push('Confirm the diagnosis was made by the responsible clinician.');
  if (!ageComplete) blockers.push('Confirm a valid age in years.');
  if (!allergiesComplete) blockers.push('Reconcile allergies and reactions; do not treat unknown status as negative.');
  if (!medicinesComplete) blockers.push('Reconcile current medicines and supplements, including a confirmed “none reported” response.');
  if (pregnancyStatus === 'unknown') blockers.push('Confirm pregnancy status.');
  if (lactationStatus === 'unknown') blockers.push('Confirm breastfeeding/lactation status.');
  if (localProtocol !== 'confirmed') blockers.push('Confirm the current Egypt/local facility protocol; if unavailable, consult the local clinical/pharmacy reference pathway.');

  const patientFactors: Record<string, boolean> = {
    age: ageComplete,
    weight: weightKg.trim() !== '' && Number.isFinite(Number(weightKg)) && Number(weightKg) > 0,
    allergies: allergiesComplete,
    current_medications: medicinesComplete,
    medical_history: medicalHistory.trim() !== '' && !isUnknown(medicalHistory),
    pregnancy_status: pregnancyStatus !== 'unknown',
    lactation_status: lactationStatus !== 'unknown',
    renal_function: renalStatus !== 'unknown',
    hepatic_function: hepaticStatus !== 'unknown',
    observations_labs: observations.trim() !== '' && !isUnknown(observations),
  };
  const code = diagnosisCode.trim().toUpperCase();
  const reviewedPathways = submitted && blockers.length === 0
    ? getApprovedMedicationPathways(code, 'EG')
    : [];
  const eligible = reviewedPathways.filter(pathway =>
    pathway.requiredPatientFactors.every(factor => patientFactors[factor] === true)
  );
  const withheldForContext = reviewedPathways.filter(pathway =>
    pathway.requiredPatientFactors.some(factor => patientFactors[factor] !== true)
  );
  const sources = submitted && blockers.length === 0
    ? searchObgynSources([diagnosisLabel, code].filter(Boolean).join(' '), 'EG', 4)
    : [];

  const teachingSections: { key: keyof PathwayMedicine['teaching']; label: string }[] = [
    { key: 'whyConsider', label: 'Why the guideline lists it' },
    { key: 'mechanism', label: 'Mechanism of action' },
    { key: 'evidenceSummary', label: 'Evidence summary' },
    { key: 'alternatives', label: 'Alternatives and comparison' },
    { key: 'commonAdverseEffects', label: 'Common adverse effects' },
    { key: 'seriousWarnings', label: 'Serious warnings' },
    { key: 'contraindications', label: 'Contraindications / exclusions' },
    { key: 'interactions', label: 'Interaction considerations' },
    { key: 'pregnancyLactation', label: 'Pregnancy / lactation' },
    { key: 'monitoring', label: 'Monitoring and follow-up' },
    { key: 'counseling', label: 'Patient counseling' },
    { key: 'doseContext', label: 'Dose context from source' },
    { key: 'populationLimits', label: 'Population / scope limits' },
  ];

  const clear = () => {
    setDiagnosisCode('');
    setDiagnosisLabel('');
    setDiagnosisConfirmed(false);
    setAgeYears('29');
    setWeightKg('');
    setAllergies('');
    setAllergiesReviewed(false);
    setCurrentMedicines('');
    setMedicinesReviewed(false);
    setMedicalHistory('');
    setPregnancyStatus('unknown');
    setLactationStatus('unknown');
    setRenalStatus('unknown');
    setHepaticStatus('unknown');
    setObservations('');
    setLocalProtocol('unknown');
    setSubmitted(false);
  };

  return (
    <div className="medication-pathways-page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">OB-GYN · EGYPT ONLY · SYNTHETIC DATA</div>
          <h1>Medication pathway review</h1>
          <p>Compare source-linked options only when an exact diagnosis pathway has completed Egypt-specific clinician and medication-safety review.</p>
        </div>
        <span className="status status-amber"><Pill size={13} /> {MEDICATION_PATHWAYS.length} catalog entries</span>
      </div>

      <div className="medication-pathway-intro">
        <AlertTriangle size={17} />
        <div>
          <strong>Prototype only · no approved medication pathways are enabled.</strong>
          <p>
            Use fictional case details only. Mia will not diagnose, rank a single “best” medicine,
            calculate a dose from patient details, or create/transmit prescriptions. Every pathway
            must have a current source, jurisdiction, population scope, OB-GYN reviewer, pharmacist
            reviewer and re-review date before it can appear.
          </p>
        </div>
      </div>

      <section className="panel medication-pathway-form">
        <div className="panel-heading">
          <div>
            <h3>Clinician-confirmed diagnosis and safety context</h3>
            <p>All input stays in browser memory. This screen makes no external API calls and stores no case.</p>
          </div>
          <span className="count-chip">Egypt · EG</span>
        </div>

        <div className="medication-pathway-form-grid">
          <div className="form-field">
            <label htmlFor="pathway-diagnosis-code">Exact diagnosis code</label>
            <input id="pathway-diagnosis-code" value={diagnosisCode} maxLength={80}
              placeholder="Exact local diagnosis code"
              onChange={event => { setDiagnosisCode(event.target.value); resetResult(); }} />
            <p className="hint">Exact code only. The text label cannot trigger fuzzy medication matching.</p>
          </div>
          <div className="form-field">
            <label htmlFor="pathway-diagnosis-label">Diagnosis label confirmed by clinician</label>
            <input id="pathway-diagnosis-label" value={diagnosisLabel} maxLength={160}
              placeholder="Clinician-entered diagnosis label"
              onChange={event => { setDiagnosisLabel(event.target.value); resetResult(); }} />
          </div>
          <div className="form-field">
            <label htmlFor="pathway-age">Age (years)</label>
            <input id="pathway-age" type="number" min="0" max="130" step="1" value={ageYears}
              onChange={event => { setAgeYears(event.target.value); resetResult(); }} />
          </div>
          <div className="form-field">
            <label htmlFor="pathway-weight">Weight (kg, when relevant)</label>
            <input id="pathway-weight" type="number" min="0" step="0.1" value={weightKg}
              placeholder="Leave blank if not available"
              onChange={event => { setWeightKg(event.target.value); resetResult(); }} />
          </div>
        </div>

        <div className="medication-pathway-checks">
          <label className="medication-pathway-check">
            <input type="checkbox" checked={diagnosisConfirmed}
              onChange={event => { setDiagnosisConfirmed(event.target.checked); resetResult(); }} />
            <span>The responsible clinician has confirmed this diagnosis.</span>
          </label>
          <label className="medication-pathway-check">
            <input type="checkbox" checked={allergiesReviewed}
              onChange={event => { setAllergiesReviewed(event.target.checked); resetResult(); }} />
            <span>Allergies and previous reactions have been reconciled.</span>
          </label>
          <label className="medication-pathway-check">
            <input type="checkbox" checked={medicinesReviewed}
              onChange={event => { setMedicinesReviewed(event.target.checked); resetResult(); }} />
            <span>Current medicines and supplements have been reconciled.</span>
          </label>
        </div>

        <div className="medication-pathway-form-grid">
          <div className="form-field">
            <label htmlFor="pathway-allergies">Allergies / reactions (fictional)</label>
            <textarea id="pathway-allergies" value={allergies} maxLength={1000}
              placeholder="Example: none reported and confirmed; or synthetic allergy note"
              onChange={event => { setAllergies(event.target.value); resetResult(); }} />
          </div>
          <div className="form-field">
            <label htmlFor="pathway-current-meds">Current medicines / supplements (fictional)</label>
            <textarea id="pathway-current-meds" value={currentMedicines} maxLength={1000}
              placeholder="Example: none reported and confirmed; or synthetic medicine list"
              onChange={event => { setCurrentMedicines(event.target.value); resetResult(); }} />
          </div>
          <div className="form-field">
            <label htmlFor="pathway-history">Relevant history (when needed)</label>
            <textarea id="pathway-history" value={medicalHistory} maxLength={1000}
              placeholder="Synthetic context only; state unknown/not assessed if unresolved"
              onChange={event => { setMedicalHistory(event.target.value); resetResult(); }} />
          </div>
          <div className="form-field">
            <label htmlFor="pathway-pregnancy">Pregnancy status</label>
            <select id="pathway-pregnancy" value={pregnancyStatus}
              onChange={event => { setPregnancyStatus(event.target.value); resetResult(); }}>
              <option value="unknown">Unknown / not assessed</option>
              <option value="yes">Pregnant</option>
              <option value="no">Not pregnant, confirmed</option>
              <option value="not_applicable">Clinician confirmed not applicable</option>
            </select>
          </div>
          <div className="form-field">
            <label htmlFor="pathway-lactation">Breastfeeding / lactation status</label>
            <select id="pathway-lactation" value={lactationStatus}
              onChange={event => { setLactationStatus(event.target.value); resetResult(); }}>
              <option value="unknown">Unknown / not assessed</option>
              <option value="yes">Breastfeeding / lactating</option>
              <option value="no">Not breastfeeding, confirmed</option>
              <option value="not_applicable">Clinician confirmed not applicable</option>
            </select>
          </div>
          <div className="form-field">
            <label htmlFor="pathway-renal">Renal function status</label>
            <select id="pathway-renal" value={renalStatus}
              onChange={event => { setRenalStatus(event.target.value); resetResult(); }}>
              <option value="unknown">Unknown / not assessed</option>
              <option value="normal">Known normal</option>
              <option value="abnormal">Known abnormal</option>
              <option value="not_applicable">Clinician confirmed not applicable</option>
            </select>
          </div>
          <div className="form-field">
            <label htmlFor="pathway-hepatic">Hepatic function status</label>
            <select id="pathway-hepatic" value={hepaticStatus}
              onChange={event => { setHepaticStatus(event.target.value); resetResult(); }}>
              <option value="unknown">Unknown / not assessed</option>
              <option value="normal">Known normal</option>
              <option value="abnormal">Known abnormal</option>
              <option value="not_applicable">Clinician confirmed not applicable</option>
            </select>
          </div>
          <div className="form-field">
            <label htmlFor="pathway-observations">Relevant observations / labs (when needed)</label>
            <textarea id="pathway-observations" value={observations} maxLength={1000}
              placeholder="Synthetic observations only"
              onChange={event => { setObservations(event.target.value); resetResult(); }} />
            <p className="hint">A pathway may require weight, observations or labs. Missing required factors withhold that pathway.</p>
          </div>
          <div className="form-field">
            <label htmlFor="pathway-protocol">Local guideline / formulary confirmation</label>
            <select id="pathway-protocol" value={localProtocol}
              onChange={event => { setLocalProtocol(event.target.value); resetResult(); }}>
              <option value="unknown">Not yet checked</option>
              <option value="confirmed">Current Egypt/local facility protocol checked</option>
              <option value="not_available">No accessible local protocol</option>
            </select>
            <p className="hint">Workflow confirmation only; this does not verify stock, product registration or local authorization.</p>
          </div>
        </div>

        <div className="form-actions">
          <button type="button" className="btn btn-primary" onClick={() => setSubmitted(true)}>
            <Search size={15} /> Review approved pathways
          </button>
          <button type="button" className="btn btn-secondary" onClick={clear}>Clear review</button>
        </div>
      </section>

      {submitted ? (
        <section className="medication-pathway-results" aria-live="polite">
          {blockers.length ? (
            <div className="medication-pathway-blockers" role="status">
              <h3>Review blocked · confirm required context first</h3>
              <ul>{blockers.map(blocker => <li key={blocker}>{blocker}</li>)}</ul>
            </div>
          ) : (
            <>
              {withheldForContext.length ? (
                <div className="medication-pathway-blockers" role="status">
                  <h3>Pathway withheld · required patient factors missing</h3>
                  <ul>{withheldForContext.map(pathway => {
                    const missing = pathway.requiredPatientFactors.filter(factor => patientFactors[factor] !== true);
                    return <li key={pathway.id}>{pathway.diagnosisCode}: confirm {missing.join(', ')} before this pathway can be shown.</li>;
                  })}</ul>
                </div>
              ) : null}
              {eligible.length ? (
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h3>Clinician-reviewed options for exact code {code}</h3>
                      <p>Roles and teaching are reproduced from reviewed references. Mia does not independently rank or select the final medicine.</p>
                    </div>
                    <span className="count-chip">{eligible.length} matched pathway(s)</span>
                  </div>
                  {eligible.map(pathway => (
                    <article className="medication-pathway-card" key={pathway.id}>
                      <h3>{pathway.diagnosis}</h3>
                      <p>Pathway {pathway.id} · {pathway.jurisdictions.join(', ')} · review due {pathway.reviewDueOn}</p>
                      {pathway.medicines.map(medicine => (
                        <div className="medication-pathway-option" key={medicine.name}>
                          <h4>{medicine.name}</h4>
                          <span className={'medication-pathway-role' + (medicine.role === 'not-recommended-here' ? ' role-warning' : '')}>
                            {medicine.role.replace(/-/g, ' ')}
                          </span>
                          <p>{medicine.rationale}</p>
                          <div className="medication-pathway-teaching">
                            {teachingSections.map(section => (
                              <section key={section.key}>
                                <h5>{section.label}</h5>
                                <p>{medicine.teaching[section.key]}</p>
                              </section>
                            ))}
                          </div>
                        </div>
                      ))}
                      <div className="medication-pathway-citations">
                        {pathway.sources.map(source => (
                          <a key={source.url} href={source.url} target="_blank" rel="noopener noreferrer">
                            {source.title} · {source.publisher} · {source.version} · {source.section}
                          </a>
                        ))}
                      </div>
                      <p>OB-GYN reviewer: {pathway.clinicianReviewer.name}, {pathway.clinicianReviewer.credential}. Medication-safety reviewer: {pathway.pharmacistReviewer.name}, {pathway.pharmacistReviewer.credential}.</p>
                    </article>
                  ))}
                </section>
              ) : withheldForContext.length === 0 ? (
                <div className="medication-pathway-empty" role="status">
                  <h3>No approved medication pathway for this exact diagnosis yet</h3>
                  <p>
                    No medicine was selected. This is a catalogue gap, not a conclusion that
                    medication is or is not indicated. Follow current Egyptian Health Council
                    guidance, the relevant EDA/product label and the facility's approved protocol,
                    or consult the supervising OB-GYN/pharmacist.
                  </p>
                  <p>Matching words in reference search do not create a medication recommendation.</p>
                  {sources.length ? (
                    <div className="medication-pathway-source-list">
                      {sources.map(source => (
                        <a key={source.id} className="medication-pathway-source" href={source.url} target="_blank" rel="noopener noreferrer">
                          <strong>{source.title}</strong>
                          <span>{source.publisher} · {source.year || 'Version/date must be confirmed'} · {source.note}</span>
                        </a>
                      ))}
                    </div>
                  ) : (
                    <p>No local source match was found. Use the local clinical/pharmacy escalation pathway; no-match does not mean no guidance exists.</p>
                  )}
                </div>
              ) : null}
            </>
          )}
          <div className="evidence-notice">
            <ShieldCheck size={16} />
            <p><strong>Clinical boundary.</strong> This is a synthetic prototype, not approved for patient care. It does not diagnose, calculate a dose, issue a prescription or run comprehensive interaction checking. A missing alert is not evidence of safety. Every clinical decision remains with the responsible clinician.</p>
          </div>
        </section>
      ) : null}
    </div>
  );
}
