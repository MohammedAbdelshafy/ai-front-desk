# Dr. Mia OB-GYN workbench and avatar personalization

## OB-GYN specialty workspace

The separate OB-GYN workbench is launched with:

\`\`\`bash
python -m pip install -e .
dr-mia-obgyn-workbench --port 8768
\`\`\`

Open http://127.0.0.1:8768. Bind only to loopback. Use synthetic case IDs such as \`synthetic-obgyn-001\`; never enter real patient identifiers or real patient histories.

The first version routes clinicians to source centers by care stage and jurisdiction. It covers preconception, antenatal care, labour/birth, postpartum care, general gynaecology, contraception, fertility, medication in pregnancy/lactation and gynaecologic oncology. The source directory includes WHO maternal-health and postpartum-haemorrhage guidance, ACOG and RCOG reference links, CDC contraceptive guidance, LactMed, MotherToBaby, UKTIS/BUMPS, DailyMed/openFDA, and Egypt-specific MOHP maternity-service, EDA register, medicine-list and safety-alert references.

The OB-GYN screen also has an explicitly opt-in U.S. medicine-label lookup, using the same standalone-name-only RxNorm/openFDA adapter as the dental app. A separate checkbox can show selected label sections for clinician reference. The lookup is disabled by default, is blocked in Egypt/UK/Global mode, does not receive gestational week or clinical-question fields, and is not a pregnancy-risk assessment, lactation assessment, interaction check or medication recommendation. For pregnancy/lactation evidence, Mia routes to the linked LactMed, MotherToBaby and UKTIS/BUMPS records; it does not copy or adjudicate their full text.

The urgent-prompt list covers potential major bleeding, seizure/loss of consciousness, collapse/shock, severe breathlessness, chest pain, severe headache/visual changes, severe abdominal/pelvic pain, fever/systemic illness, reduced fetal movement and postpartum deterioration. Selecting a prompt only displays an escalation reminder. The form is not a triage algorithm and cannot rule out an emergency. The hospital's approved emergency protocol and senior clinical response take priority.

### Suggested synthetic test cases for Dr. Shafy

1. **Postpartum haemorrhage reference routing**
   - Jurisdiction: `EG` or `GLOBAL`; care stage: `Postpartum care`.
   - Clinical question: `postpartum haemorrhage guideline version and local emergency protocol`.
   - Expected: WHO PPH guidance and relevant Egyptian/local sources are shown as references. The selected urgent-prompt checklist is not a substitute for hospital emergency activation or local haemorrhage protocol.

2. **Hypertension / preeclampsia**
   - Jurisdiction: `EG`; care stage: `Pregnancy / antenatal care`.
   - Clinical question: `preeclampsia hypertensive disorders pregnancy local protocol`.
   - Expected: Egypt/global links appear; the app does not silently substitute a US ACOG protocol for local hospital policy.

3. **Medicine during pregnancy or lactation**
   - Jurisdiction: `GLOBAL` or `US`; care stage: `Medication during pregnancy or lactation`.
   - Clinical question: `breastfeeding medicine exposure` or `medication in pregnancy`.
   - Expected: links to relevant LactMed, MotherToBaby and/or UKTIS/BUMPS references appear with their role and rights status. Topic matching is not a risk assessment and does not determine whether a medicine should be started, stopped or changed.

4. **Egypt-specific regulatory reference**
   - Jurisdiction: `EG`; care stage: `General OB-GYN question`.
   - Clinical question: `Egyptian Drug Register pregnancy medication safety alert`.
   - Expected: the EDA and MOHP reference links are available. The optional US label lookup must reject this jurisdiction rather than call openFDA.

5. **Optional public label lookup**
   - Jurisdiction: `US`; medicine field: `ibuprofen`; check the medicine-label lookup checkbox and optionally the label-sections checkbox.
   - Expected: if the public API is reachable, Mia shows RxNorm/openFDA identity and label information. Only `ibuprofen` is sent externally. This does **not** check safety in pregnancy or lactation, patient-specific contraindications or interactions; the app must show its reference-only warning.

6. **Emergency escalation prompt**
   - Select a synthetic `heavy bleeding` or `seizure` prompt.
   - Expected: a clear instruction to activate the hospital's local emergency response appears. Do not wait for Mia when an actual person may be deteriorating.

7. **Avatar**
   - Change to each preset, upload a test image, and confirm the avatar updates throughout the current app. Export the profile and import it in the other local app on its separate port, then reset to default.
   - Expected: the photo remains in browser storage and no network request sends it to the Mia server or an AI endpoint. Do not use a real patient's photo.

## Clinical boundary

This is a **reference-routing prototype**, not a prescribing engine. It does not diagnose, recommend a medicine, calculate a dose, determine delivery management, or approve care. Reference relevance is based on topic text, not clinical applicability. Copyrighted, commercially restricted or uncertain source content remains link-only until reuse rights are confirmed. Any future OB-GYN medication pathway requires jurisdiction-specific source selection, exact product/version checks, qualified obstetric/gynaecology and pharmacy review, clinical governance approval and evaluation.

The Egypt mode helps keep Egyptian regulator/formulary references visible. It does not establish current registration, local availability, local dosing or treatment suitability.

## Personalizing Mia's avatar

The same reusable component is now included in:
- the main Mia intake / dashboard prototype;
- the dental clinical evidence workbench;
- the OB-GYN clinical reference workbench.

A user can choose a built-in persona or upload their own portrait for Mia's avatar. The browser resizes a permitted JPEG, PNG or WebP image locally and saves it in browser storage. The image is not uploaded to the local Python server or sent to a model. Users can reset the avatar or export/import an avatar-profile JSON between apps.

### Local prototype limitation

These prototypes use different localhost ports, and browser storage is isolated by origin. To carry a custom avatar between these local apps, use **Export for other Mia apps** in one app and import the JSON in the other. An exported profile containing a portrait should be treated like a personal photo and shared privately.

For production, the same component should read and save a non-clinical avatar preference in the authenticated user's account profile across apps. Image storage, deletion, retention, consent, authorization and account separation must be designed before enabling hosted uploads. Avatar choice changes only the visual appearance, never the user's role, permissions, clinical behavior, evidence sources or safety rules.

## Validation checklist

- Confirm each app page loads \`/assets/mia-avatar.css\` and \`/assets/mia-avatar.js\`.
- Choose each built-in persona and check that all Mia avatar displays on that app update.
- Upload a sample photo. Check that it is cropped/resized for display, and that no network request sends the image.
- Export the profile and import it into another local Mia app.
- Reset the avatar and confirm the default Mia appearance returns.
- Confirm that changing the avatar has no effect on evidence routing, jurisdiction, clinical decisions or app permissions.

The workbenches remain local, unauthenticated synthetic-data demos. Do not expose them publicly or use them for real-patient care.
