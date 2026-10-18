# Mia OB-GYN Clinical OS

Standalone OB-GYN-only web prototype.

## Run locally

```bash
npm install
npm run dev
```

Build with `npm run build`.

## Safety boundary

- Synthetic demo records only. Do not enter real patient data.
- No backend, production authentication, external AI/model call, live patient links, e-prescribing or clinical actions.
- Mia searches a local curated source directory and presents reference links. It does not diagnose, select a medicine, calculate a dose or claim that a drug is safe.
- Existing source matches are directory-level discovery, not approved clinical pathways. Every source/pathway needs current-version, licensing, jurisdiction and qualified clinical review.
- UI avatar customization is client-local and does not upload images.
- This is not approved for real patient care or a compliance certification.

## Separate deployment principle

This app contains only obstetrics and gynaecology content. Each clinic/specialty should get a separate deployment and, before production, separate auth, secrets, storage, database and backups by default.
