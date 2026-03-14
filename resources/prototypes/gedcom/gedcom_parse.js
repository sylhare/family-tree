/**
 * Minimal GEDCOM prototype: parse an inline GEDCOM string and print
 * individuals with their birth dates.
 *
 * Prerequisites:
 *   npm install parse-gedcom
 *
 * Run:
 *   node gedcom_parse.js
 */

const { parse } = require('parse-gedcom')

// Inline GEDCOM 5.5.1 sample — no external file needed
const gedcomString = `0 HEAD
1 GEDC
2 VERS 5.5.1
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
0 TRLR`

function getTag(node, tag) {
  return (node.tree || []).find((n) => n.tag === tag)
}

function getValue(node, tag) {
  const child = getTag(node, tag)
  return child ? child.data : null
}

const records = parse(gedcomString)
const individuals = records.filter((r) => r.tag === 'INDI')

console.log('Individuals found:', individuals.length)
console.log()

for (const indi of individuals) {
  const nameNode = getTag(indi, 'NAME')
  const name = nameNode ? nameNode.data.replace(/\//g, '').trim() : '(unknown)'
  const birtNode = getTag(indi, 'BIRT')
  const birthDate = birtNode ? getValue(birtNode, 'DATE') : null
  console.log(`  ${name}${birthDate ? '  born ' + birthDate : ''}`)
}
