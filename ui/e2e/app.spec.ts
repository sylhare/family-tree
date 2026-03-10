import { test, expect } from '@playwright/test'

// Unique suffix per test run to avoid ID collisions across runs
const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 5)

test.describe('App shell', () => {
  test('heading visible and API online', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: /Family Tree Manager/i })).toBeVisible()
    await expect(page.getByText('✅ Online')).toBeVisible()
    await page.screenshot({ path: '../docs/screenshots/app.png', fullPage: true })
  })
})

test.describe('Add Person', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('✅ Online')).toBeVisible()
  })

  test('adds a person and shows a success message', async ({ page }) => {
    const id = `e2e-${uid()}`
    await page.getByLabel('ID (optional)').fill(id)
    await page.getByLabel('Name *').fill('Alice Test')
    await page.getByRole('button', { name: 'Add Person' }).click()

    await expect(page.getByText('Added Alice Test to the family tree')).toBeVisible()
  })

  test('auto-generates an ID when left blank', async ({ page }) => {
    await page.getByLabel('Name *').fill('Bob Test')
    await page.getByRole('button', { name: 'Add Person' }).click()

    await expect(page.getByText('Added Bob Test to the family tree')).toBeVisible()
  })

  test('rejects a duplicate person ID', async ({ page }) => {
    const id = `e2e-dup-${uid()}`

    await page.getByLabel('ID (optional)').fill(id)
    await page.getByLabel('Name *').fill('First')
    await page.getByRole('button', { name: 'Add Person' }).click()
    await page.getByText('Added First').waitFor()

    await page.getByLabel('ID (optional)').fill(id)
    await page.getByLabel('Name *').fill('Second')
    await page.getByRole('button', { name: 'Add Person' }).click()

    await expect(page.getByText(/already exists/i)).toBeVisible()
  })
})

test.describe('Add Relationship', () => {
  let idA: string
  let idB: string

  test.beforeEach(async ({ page }) => {
    idA = `e2e-a-${uid()}`
    idB = `e2e-b-${uid()}`

    await page.goto('/')
    await expect(page.getByText('✅ Online')).toBeVisible()

    await page.getByLabel('ID (optional)').fill(idA)
    await page.getByLabel('Name *').fill('Parent Test')
    await page.getByRole('button', { name: 'Add Person' }).click()
    await page.getByText('Added Parent Test').waitFor()

    await page.getByLabel('ID (optional)').fill(idB)
    await page.getByLabel('Name *').fill('Child Test')
    await page.getByRole('button', { name: 'Add Person' }).click()
    await page.getByText('Added Child Test').waitFor()
  })

  test('relationship form appears after 2 persons are added', async ({ page }) => {
    await expect(page.getByLabel('From Person *')).toBeVisible()
  })

  test('adds a relationship and shows a success message', async ({ page }) => {
    await page.getByLabel('From Person *').selectOption(idA)
    await page.getByLabel('Relationship Type *').selectOption('PARENT_OF')
    await page.getByLabel('To Person *').selectOption(idB)
    await page.getByRole('button', { name: 'Add Relationship' }).click()

    await expect(page.getByText('Added relationship')).toBeVisible()
    await expect(page.getByTestId('relationships-count')).not.toHaveText('0')
  })

  test('rejects a duplicate relationship', async ({ page }) => {
    const addRel = async () => {
      await page.getByLabel('From Person *').selectOption(idA)
      await page.getByLabel('Relationship Type *').selectOption('PARENT_OF')
      await page.getByLabel('To Person *').selectOption(idB)
      await page.getByRole('button', { name: 'Add Relationship' }).click()
    }

    await addRel()
    await page.getByText('Added relationship').waitFor()
    await addRel()

    await expect(page.getByText('This relationship already exists')).toBeVisible()
  })
})

test.describe('Clear All', () => {
  test('clears local state and shows empty state', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('✅ Online')).toBeVisible()

    await page.getByLabel('Name *').fill('To Be Cleared')
    await page.getByRole('button', { name: 'Add Person' }).click()
    await page.getByText('Added To Be Cleared').waitFor()

    page.on('dialog', (d) => d.accept())
    await page.getByRole('button', { name: 'Clear All' }).click()

    await expect(page.getByText('Start building your family tree')).toBeVisible()
  })
})

test.describe('Import GEDCOM X', () => {
  test('imports a GEDCOM X JSON file', async ({ page }) => {
    const id = `gedcom-${uid()}`
    const name = `GedcomX Person ${id}`

    await page.goto('/')
    await expect(page.getByText('✅ Online')).toBeVisible()

    const dialogPromise = page.waitForEvent('dialog')

    await page.locator('input[type="file"][accept*="json"]').setInputFiles({
      name: 'family.json',
      mimeType: 'application/json',
      buffer: Buffer.from(JSON.stringify({
        persons: [{ id, display: { name } }],
        relationships: [],
      })),
    })

    const dialog = await dialogPromise
    expect(dialog.message()).toBe('GEDCOM X imported successfully.')
    await dialog.accept()
  })
})

test.describe('Save to Neo4j', () => {
  test('saves a person and it persists after page reload', async ({ page }) => {
    const id = `e2e-save-${uid()}`
    const name = `Persisted Person ${id}`

    await page.goto('/')
    await expect(page.getByText('✅ Online')).toBeVisible()

    await page.getByLabel('ID (optional)').fill(id)
    await page.getByLabel('Name *').fill(name)
    await page.getByRole('button', { name: 'Add Person' }).click()
    await page.getByText(`Added ${name}`).waitFor()

    await page.getByRole('button', { name: 'Save to Neo4j' }).click()
    await expect(page.getByText('Family tree successfully saved to Neo4j!')).toBeVisible()

    // Reload and verify the person was persisted in Neo4j
    await page.reload()
    await expect(page.getByText('✅ Online')).toBeVisible()
    await page.getByRole('button', { name: /List/i }).click()
    await expect(page.getByTestId('person-name').filter({ hasText: name })).toBeVisible()
  })

  test('saves a relationship and it persists after page reload', async ({ page }) => {
    const idA = `e2e-rel-a-${uid()}`
    const idB = `e2e-rel-b-${uid()}`
    const nameA = `Parent Persist ${idA}`
    const nameB = `Child Persist ${idB}`

    await page.goto('/')
    await expect(page.getByText('✅ Online')).toBeVisible()

    await page.getByLabel('ID (optional)').fill(idA)
    await page.getByLabel('Name *').fill(nameA)
    await page.getByRole('button', { name: 'Add Person' }).click()
    await page.getByText(`Added ${nameA}`).waitFor()

    await page.getByLabel('ID (optional)').fill(idB)
    await page.getByLabel('Name *').fill(nameB)
    await page.getByRole('button', { name: 'Add Person' }).click()
    await page.getByText(`Added ${nameB}`).waitFor()

    await page.getByLabel('From Person *').selectOption(idA)
    await page.getByLabel('Relationship Type *').selectOption('PARENT_OF')
    await page.getByLabel('To Person *').selectOption(idB)
    await page.getByRole('button', { name: 'Add Relationship' }).click()
    await page.getByText('Added relationship').waitFor()

    await page.getByRole('button', { name: 'Save to Neo4j' }).click()
    await expect(page.getByText('Family tree successfully saved to Neo4j!')).toBeVisible()

    // Reload and verify the relationship persisted
    await page.reload()
    await expect(page.getByText('✅ Online')).toBeVisible()
    await page.getByRole('button', { name: /List/i }).click()
    await expect(page.getByTestId('person-name').filter({ hasText: nameA })).toBeVisible()
    await expect(page.getByTestId('person-name').filter({ hasText: nameB })).toBeVisible()
    await expect(
      page.getByTestId('relationship-item').filter({ hasText: nameA }).filter({ hasText: nameB })
    ).toBeVisible()
  })
})
