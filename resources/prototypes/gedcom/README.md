# GEDCOM Prototype

Demonstrates parsing a GEDCOM 5.5.1 file with JavaScript. The prototype uses an inline GEDCOM string (no external file required) and prints each individual with their birth date.

## What is GEDCOM?

GEDCOM (Genealogical Data Communication) is the de facto plain-text standard for exchanging genealogical data between software tools. Files use the `.ged` extension and consist of hierarchical line-based records with level numbers and tags.

See [docs/genealogy-standards.md](../../../docs/genealogy-standards.md) for a full reference.

## Prerequisites

```bash
npm install parse-gedcom
```

## Run

```bash
node gedcom_parse.js
```

## Expected Output

```
Individuals found: 3

  John Doe  born 15 JUN 1970
  Jane Smith  born 14 FEB 1972
  Alice Doe  born 30 MAY 2000
```
