# Genealogical Data Standards: A Quick Reference

This document summarizes common standards used to exchange genealogical data and shows how they map to the model used in this app.

## GEDCOM (FamilySearch) – de facto legacy standard
- Purpose: Plain‑text hierarchical format for exchanging genealogical data between desktop tools
- Latest widely used: GEDCOM 5.5 / 5.5.1 (1999/2010)
- Newer: GEDCOM 7.x (2021+) modernizes encoding and adds features
- File extension: `.ged`

### Structure
- Records are line‑based with level numbers, tags, optional cross‑refs
- Common record types: INDI (individual), FAM (family), SOUR (source), NOTE, OBJE
- Relationships are expressed via links between INDI and FAM records

### Minimal example (GEDCOM 5.5.1)
```
0 @I1@ INDI
1 NAME John /Doe/
1 SEX M
1 BIRT
2 DATE 15 JUN 1970
2 PLAC Springfield, USA
1 FAMS @F1@

0 @I2@ INDI
1 NAME Jane /Smith/
1 SEX F
1 BIRT
2 DATE 14 FEB 1972
1 FAMS @F1@

0 @I3@ INDI
1 NAME Alice /Doe/
1 SEX F
1 BIRT
2 DATE 30 MAY 2000
1 FAMC @F1@

0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
1 MARR
2 DATE 12 JUN 1995
```

### Key tags
- INDI/FAM: record types
- HUSB/WIFE/CHIL: family membership
- FAMS/FAMC: individual links to spouse family / child family
- BIRT/DEAT/MARR: vital events

### Mapping to this app’s model
- INDI → Person node: `Person { id, name, birth }`
- FAM with HUSB/WIFE → MARRIED relationships between two persons
- FAM with CHIL → PARENT_OF relationships from each parent to child
- Dates/places can map to person/event properties (we currently map birth date only)
