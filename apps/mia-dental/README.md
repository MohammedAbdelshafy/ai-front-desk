# Dr. Mia Dental OS

Standalone React/Vite source mirror for the synthetic-data clinician prototype.

Live demo: https://dr-mia-dental-os-9n85n7.v2.appdeploy.ai/

## Run locally

Use npm install, npm run typecheck, npm run build, and npm run dev.

## Scope and safety

- Use fictional/synthetic cases only. The browser UI does not persist cases or make backend/API calls.
- The approved medication pathway catalog contains zero entries. Incomplete patient context blocks review; even completed context does not return a medicine until a clinician-reviewed pathway exists.
- No autonomous diagnosis, ranking of a single best medicine, dose calculation, prescription creation/signing/transmission, or comprehensive interaction checking.
- Search terms go to public sources only when a user explicitly opens an individual link. Never enter identifying or confidential patient details into searches.
- Trial records, papers and US medicine labels are not approval to use a treatment in Egypt.
- A real pathway requires current sources and rights checks, an accountable practicing dentist, a medication-safety reviewer, a review date, clinical evaluation cases, and applicable clinical, regulatory, privacy and security approval.
- An empty catalog is a software-readiness gap, not advice to withhold care.

## Continuous integration

The mia-dental-web workflow type-checks and builds the standalone app. The repository Python suite continues to validate the shared evidence workbench.
