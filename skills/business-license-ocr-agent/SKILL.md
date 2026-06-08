# Business License OCR Agent

Use this skill when the task is to identify Chinese business license fields, extract structured content, validate it, and repair likely OCR errors.

## Workflow

1. Read OCR text from image, PDF, or an OCR engine.
2. Extract canonical business license fields:
   - unified social credit code
   - company name
   - company type
   - legal representative
   - registered capital
   - establishment date
   - business period
   - address
   - business scope
   - registration authority
   - approval date
3. Validate high-signal fields with deterministic rules.
4. Generate repair candidates for common OCR confusions.
5. Only accept automatic repair when rules become stronger after repair.
6. Return the final fields plus an explanation report.

## Validation Rules

- Unified social credit code should be 18 characters.
- Allowed characters are digits plus uppercase letters excluding ambiguous letters such as I, O, S, V, Z.
- Use the official weighted checksum rule for the 18th character.
- Dates should match `YYYY 年 M 月 D 日`.
- Registered capital should contain a number and a currency/unit marker.

## Common OCR Repairs

- `O` or `o` -> `0`
- `I`, `l`, or `|` -> `1`
- `S` -> `5`

## Output Contract

Return:

```json
{
  "final_fields": {},
  "validation_before_repair": {},
  "repair_actions": [],
  "validation_after_repair": {},
  "summary": {}
}
```

## Demo Talking Point

OCR is perception. The agent adds reasoning, validation, repair, and explainability.

