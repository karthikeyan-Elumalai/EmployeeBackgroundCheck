# Resume Analysis Checklist (HR)

This checklist is designed for the current prototype behavior and for dashboard review.

## Primary factors considered

1. Identity completeness
- Full Name present
- Date reference present (DOB or issue date)
- ID Number present

2. Contact completeness
- Email present
- Phone number present
- Address present

3. Employment credibility
- Current/previous employer details
- Employment status (Active/Completed)
- Role and duration consistency

4. Profile consistency
- Name/date/id consistency across extracted fields
- Document type context match
- Cross-verification against local corpus records

5. Risk and fraud signals
- Missing required fields
- Low OCR confidence
- Unstructured or suspicious date formats
- Invalid identifier patterns

6. External verification signals (Step 3)
- Employment API match status
- Identity API match status
- Connector retries/timeouts/errors

7. Review readiness
- Recommendation: approve/review/manual_review
- Pending review queue placement
- Reviewer decision and notes capture

## Maximum checks in this prototype

### A) Required field checks (strict)
- Required fields: `name`, `date`, `id_number`
- Missing any required field -> verification `needs_review`
- Missing all required fields -> high-risk/manual review candidate

### B) Optional quality checks
- Document type extracted
- Contact details present
- Employment section present
- Skills section present
- Certification/reference hints

### C) Pipeline checks
- OCR extraction status and confidence
- Retrieval behavior from corpus
- External verification connector results
- Risk score and recommendation generation

## Test-ready resume samples

1. Complete sample (expected: likely `passed` + `approve`)
- `tests/samples/sample_resume_hr.txt`

2. Missing required fields sample (expected: `needs_review` + review/manual_review)
- `tests/samples/sample_resume_missing_required.txt`

## Dashboard usage

Open:
- `http://127.0.0.1:8000/dashboard`

Use Upload Resume section and watch:
- Total/pending/approved/rejected cards
- Risk distribution
- Recent cases list
- Latest analysis panel
