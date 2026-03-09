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

---

## GEDCOM X (FamilySearch) – modern JSON/Atom based
- Purpose: Web‑friendly data model and formats for genealogical data, APIs, and interchange
- Formats: JSON, XML/Atom, RDF
- Entities: Person, Relationship, SourceDescription, Evidence

### JSON snippet
```json
{
  "persons": [
    {"id": "I1", "names": [{"nameForms": [{"fullText": "John Doe"}]}],
     "facts": [{"type": "http://gedcomx.org/Birth", "date": {"original": "1970-06-15"}}]},
    {"id": "I2", "names": [{"nameForms": [{"fullText": "Jane Smith"}]}]},
    {"id": "I3", "names": [{"nameForms": [{"fullText": "Alice Doe"}]}]}
  ],
  "relationships": [
    {"type": "http://gedcomx.org/Couple", "person1": {"resource": "#I1"}, "person2": {"resource": "#I2"}},
    {"type": "http://gedcomx.org/ParentChild", "person1": {"resource": "#I1"}, "person2": {"resource": "#I3"}},
    {"type": "http://gedcomx.org/ParentChild", "person1": {"resource": "#I2"}, "person2": {"resource": "#I3"}}
  ]
}
```

### Mapping
- Person.names[0].nameForms[0].fullText → Person.name
- Birth fact.date.original → Person.birth
- Couple → MARRIED
- ParentChild → PARENT_OF

---

## FHISO (GAJO / GEDCOM alternatives)
- FHISO (Family History Information Standards Organisation) publishes technical standards and drafts aiming at interoperable vocabularies and serializations (e.g., **ELF** – Extended Lineage-Linked Format proposals, **CITe** for citations).
- Adoption is emerging; many systems still interoperate via GEDCOM 5.5/7 or GEDCOM X.

---

## Comparison summary
- **GEDCOM 5.5/7**: Plain text, ubiquitous interchange between desktop tools; limited structure, event-oriented
- **GEDCOM X**: Web‑native JSON/RDF, richer semantics; good for APIs; used by FamilySearch ecosystem
- **FHISO**: Standards body producing interoperable specifications; adoption varies

Our app’s minimal graph model aligns well with all three by mapping:
- Persons → nodes with `id`, `name`, `birth`
- Marriages/Couples → `MARRIED` edges
- Parent‑child links → `PARENT_OF` edges

---

## Example mappings to app payload
### Input JSON for this app
```json
{
  "persons": [
    {"id": "I1", "name": "John Doe", "birth": "1970-06-15"},
    {"id": "I2", "name": "Jane Smith", "birth": "1972-02-14"},
    {"id": "I3", "name": "Alice Doe", "birth": "2000-05-30"}
  ],
  "relationships": [
    {"start_id": "I1", "end_id": "I2", "type": "MARRIED"},
    {"start_id": "I1", "end_id": "I3", "type": "PARENT_OF"},
    {"start_id": "I2", "end_id": "I3", "type": "PARENT_OF"}
  ]
}
```

### From GEDCOM (conceptually)
- INDI @I1@/@I2@ → persons with `id` I1/I2
- FAM @F1@ with HUSB @I1@, WIFE @I2@ → `MARRIED` (I1→I2)
- FAM @F1@ with CHIL @I3@ → `PARENT_OF` (I1→I3 and I2→I3)

### From GEDCOM X (conceptually)
- Person.id → `id`, nameForms.fullText → `name`
- Birth fact → `birth`
- Couple → `MARRIED`
- ParentChild → `PARENT_OF`

---

## Tips when importing
- Normalize IDs: keep stable IDs if provided (e.g., `@I1@` → `I1`), else generate unique IDs.
- Normalize names (trim whitespace) and dates (ISO: `YYYY-MM-DD`).
- Deduplicate relationships; avoid duplicated edges.
- Consider bidirectional semantics: store only one direction per relationship type in the DB and derive inverses as needed.

## Further reading
- [GEDCOM 7.x Specification (FamilySearch)](https://gedcom.io/specifications/FamilySearchGEDCOMv7.html)
- [GEDCOM X Data Formats (FamilySearch)](https://github.com/FamilySearch/gedcomx)
- [FHISO Specifications](https://fhiso.org/standards/)