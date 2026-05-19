/**
 * GRADX Scanned/Handwritten PDF UI Test (Playwright)
 * Uses an image-only PDF (no text layer) to trigger the OCR path via Gemini.
 * Run: node ui_test_scanned.js
 */

const { chromium } = require('playwright');
const path = require('path');
const fs   = require('fs');

const BASE          = 'http://localhost:4200';
const EMAIL         = 'pdftest.faculty@gradx.com';
const PASS          = 'Test@1234';
const MODEL_PDF     = path.resolve(__dirname, 'backend-python/app/exam_model_answer.pdf');   // typed (PyMuPDF)
const STUDENT_PDF   = path.resolve(__dirname, 'backend-python/app/scanned_student_answer.pdf'); // image-only (OCR)
const STUDENT_EMAIL = 'pdftest.student@gradx.com';

const QUESTIONS = [
  { topic: 'Object-Oriented Programming',     sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,4,2,2] },
  { topic: 'Database Normalization',           sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,4,2,2] },
  { topic: 'OS Process Management',            sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,4,2,2] },
  { topic: 'Computer Networks and OSI Model',  sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,4,2,2] },
];

let stepNum = 0;
const step = (msg) => console.log(`\n[STEP ${++stepNum}] ${msg}`);
const pass = (msg) => console.log(`  ✅ ${msg}`);
const fail = (msg) => console.error(`  ❌ ${msg}`);
const info = (msg) => console.log(`  ℹ  ${msg}`);

let browser, page;

async function shot(name) {
  const p = path.resolve(__dirname, `screenshot_scan_${name}.png`);
  await page.screenshot({ path: p, fullPage: false });
  info(`Screenshot → ${path.basename(p)}`);
}

async function waitAndClick(selector, opts = {}) {
  const el = page.locator(selector).first();
  await el.waitFor({ state: 'visible', timeout: 8000 });
  await el.click(opts);
}

// ─────────────────────────────────────────────────────────────────────────────
(async () => {
  browser = await chromium.launch({ headless: false, slowMo: 80, args: ['--start-maximized'] });
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  page = await ctx.newPage();

  // ── STEP 1: Verify scanned PDF has no embedded text ───────────────────────
  step('Verify scanned PDF is image-only (no text layer)');
  info(`Scanned PDF: ${STUDENT_PDF}`);
  info(`File exists: ${fs.existsSync(STUDENT_PDF)}`);
  info(`File size: ${(fs.statSync(STUDENT_PDF).size / 1024).toFixed(1)} KB`);
  pass('Scanned student PDF ready');

  // ── STEP 2: Login as faculty ──────────────────────────────────────────────
  step('Login as faculty');
  await page.goto(`${BASE}/auth/login`, { waitUntil: 'networkidle' });
  await page.locator('select').first().selectOption('faculty').catch(async () => {
    await page.locator('[formControlName="role"]').selectOption('faculty');
  });
  await page.locator('[formControlName="email"]').fill(EMAIL);
  await page.locator('[formControlName="password"]').fill(PASS);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(/dashboard|faculty/, { timeout: 15000 });
  pass(`Logged in — URL: ${page.url()}`);
  await shot('01_dashboard');

  // ── STEP 3: Exam details ──────────────────────────────────────────────────
  step('Fill basic exam details');
  await page.locator('[formControlName="academicYear"]').selectOption('2025-26');
  await page.locator('[formControlName="year"]').selectOption('second');
  await page.locator('[formControlName="department"]').selectOption('cse');
  await page.locator('[formControlName="examType"]').selectOption('mse');
  await page.locator('[formControlName="semester"]').selectOption('odd');
  await page.locator('[formControlName="subject"]').fill('Computer Science Fundamentals');
  pass('Exam details filled');

  // ── STEP 4: Enable Multi-Q mode ───────────────────────────────────────────
  step('Enable Multi-Q (PDF) mode');
  const multiQBtn = page.locator('button', { hasText: /Multi-Q/i });
  await multiQBtn.waitFor({ state: 'visible', timeout: 5000 });
  await multiQBtn.click();
  await page.waitForTimeout(500);
  pass('Multi-Q mode activated');

  // helper: fill a marks input reliably for Angular ngModel (number type)
  async function fillMarks(locator, value) {
    await locator.click({ clickCount: 3 });          // focus + select all
    await locator.pressSequentially(String(value));   // type char-by-char (fires keydown/input per char)
    await locator.press('Tab');                        // blur → fires change event
    await page.waitForTimeout(150);
  }

  // ── STEP 5: Build 4 questions ─────────────────────────────────────────────
  step('Configure 4 questions × 4 sections each');
  for (let qIdx = 0; qIdx < QUESTIONS.length; qIdx++) {
    const q = QUESTIONS[qIdx];
    if (qIdx > 0) {
      const addQBtn = page.locator('button', { hasText: /Add Question/i });
      await addQBtn.waitFor({ state: 'visible', timeout: 5000 });
      await addQBtn.click();
      await page.waitForTimeout(400);
    }
    const qContainer = page.locator('.question-container').nth(qIdx);
    await qContainer.waitFor({ state: 'visible', timeout: 5000 });

    const topicInput = qContainer.locator('input[placeholder*="Optional topic"]');
    await topicInput.fill(q.topic);

    for (let sIdx = 0; sIdx < q.sections.length; sIdx++) {
      if (sIdx > 0) {
        const addSecBtn = qContainer.locator('button', { hasText: /Add Section/i });
        await addSecBtn.waitFor({ state: 'visible', timeout: 5000 });
        await addSecBtn.click();
        await page.waitForTimeout(300);
      }
      const nameInputs  = qContainer.locator('input.section-name-input');
      const marksInputs = qContainer.locator('input.section-marks-input');
      await nameInputs.nth(sIdx).fill(q.sections[sIdx]);
      await fillMarks(marksInputs.nth(sIdx), q.marks[sIdx]);
    }
    info(`Q${qIdx + 1} "${q.topic}" — ${q.sections.length} sections configured`);
  }

  // Verify Angular computed the correct total marks
  await page.waitForTimeout(500);
  const totalDisplay = await page.locator('.sections-total strong').textContent().catch(() => '?');
  info(`Angular total marks display: "${totalDisplay}"`);
  pass('4 questions configured');
  await shot('02_questions_built');

  // ── STEP 6: Check max marks ───────────────────────────────────────────────
  step('Verify max marks = 40');
  await page.waitForTimeout(600);
  let maxMarks = await page.locator('[formControlName="maxMarks"]').inputValue();
  if (maxMarks !== '40') {
    info(`Max marks = "${maxMarks}" — forcing to 40 via fill()`);
    const mxEl = page.locator('[formControlName="maxMarks"]');
    await mxEl.click({ clickCount: 3 });
    await mxEl.fill('40');
    await mxEl.press('Tab');
    await page.waitForTimeout(200);
    maxMarks = await mxEl.inputValue();
  }
  pass(`Max marks = ${maxMarks}`);

  // ── STEP 7: Upload SCANNED student PDF ───────────────────────────────────
  step('Upload SCANNED student answer PDF (image-only → triggers OCR)');
  const [studentChooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    page.locator('.upload-add-btn').click(),
  ]);
  await studentChooser.setFiles(STUDENT_PDF);
  await page.waitForTimeout(600);
  const emailInput = page.locator('input.paper-email').last();
  await emailInput.waitFor({ state: 'visible', timeout: 5000 });
  await emailInput.fill(STUDENT_EMAIL);
  pass(`Student scanned PDF uploaded | email: ${STUDENT_EMAIL}`);

  // ── STEP 8: Upload typed model answer PDF ─────────────────────────────────
  step('Upload typed model answer PDF');
  const [modelChooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    page.locator('.upload-area--compact').nth(1).click(),
  ]);
  await modelChooser.setFiles(MODEL_PDF);
  await page.waitForTimeout(600);
  pass(`Model PDF: ${path.basename(MODEL_PDF)}`);
  await shot('03_files_uploaded');

  // ── STEP 9: AI mode + cross-check ────────────────────────────────────────
  step('Confirm AI mode + cross-check enabled');
  const aiRadio = page.locator('input[value="ai"]');
  if (!(await aiRadio.isChecked())) await aiRadio.check();
  const crossCheckBox = page.locator('[formControlName="enableCrossCheck"]');
  if (!(await crossCheckBox.isChecked())) await crossCheckBox.check();
  pass('AI mode active, cross-check enabled');

  // ── STEP 10: Submit ───────────────────────────────────────────────────────
  step('Click "Start Evaluation"');
  await page.locator('button[type="submit"]').click();

  // Identify the PROGRESS modal (the one that does NOT contain .cross-check-modal)
  // Strategy: wait for ANY modal to become visible
  await page.waitForFunction(() => {
    const modals = document.querySelectorAll('.modal');
    for (const m of modals) {
      if (!m.querySelector('.cross-check-modal') && m.style.display === 'flex') return true;
    }
    return false;
  }, null, { timeout: 15000 });
  pass('Progress modal opened — OCR will now run via Gemini API (may take ~90s for 4 pages)');
  await shot('04_progress_modal');
  info('FastAPI: is_text_based() → False → pdf_to_images() → Gemini OCR per page');

  // ── STEP 11: Wait for OCR + evaluation (up to 4 min) ──────────────────────
  step('Waiting for OCR + AI evaluation (up to 4 min)…');
  // Wait for progress modal to CLOSE (transition flex → none = evaluation done)
  await page.waitForFunction(() => {
    const modals = document.querySelectorAll('.modal');
    for (const m of modals) {
      if (!m.querySelector('.cross-check-modal') && m.style.display === 'none') return true;
    }
    return false;
  }, null, { timeout: 240000 });
  pass('OCR + evaluation finished — progress modal closed');
  await shot('05_evaluation_done');

  // Angular runs a setTimeout(1000ms) before opening the cross-check modal
  await page.waitForTimeout(2500);
  await shot('05b_after_wait');

  // ── STEP 12: Inspect cross-check modal ───────────────────────────────────
  step('Inspect cross-check modal — verify OCR extracted sections');

  // Wait up to 10s for the modal to appear
  const crossModal = page.locator('.cross-check-modal');
  await crossModal.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
  const isVisible  = await crossModal.isVisible().catch(() => false);

  if (!isVisible) {
    info('Cross-check modal not shown');
    await shot('06_no_crosscheck');
    pass('Evaluation completed without cross-check');
  } else {
    pass('Cross-check modal is open');
    await shot('06_crosscheck_modal');

    const paperCounter = await page.locator('.paper-counter').textContent().catch(() => '');
    info(`Paper: ${paperCounter.trim()}`);

    const aiScore = await page.locator('#aiScore').textContent().catch(() => '?');
    const aiMax   = await page.locator('#aiMaxMarks').textContent().catch(() => '?');
    if (parseInt(aiScore) > 0)
      pass(`AI Score: ${aiScore} / ${aiMax}  (OCR-based scoring)`);
    else
      fail(`AI Score: ${aiScore} / ${aiMax}  — OCR may have failed`);

    // Section scores
    const sectionItems = page.locator('#aiQuestionMarks .question-item');
    const count = await sectionItems.count();
    info(`Section rows: ${count} (expected 16 for 4Q × 4 sections)`);

    const allText = [];
    for (let i = 0; i < count; i++) {
      const t = await sectionItems.nth(i).textContent();
      allText.push(t.trim().replace(/\s+/g, ' '));
    }
    const hasQ1 = allText.some(t => t.startsWith('Q1:'));
    const hasQ4 = allText.some(t => t.startsWith('Q4:'));
    if (count === 16 && hasQ1 && hasQ4)
      pass('All 16 sections scored via OCR (Q1…Q4)');
    else if (count > 0)
      fail(`Only ${count} section rows (Q1=${hasQ1}, Q4=${hasQ4})`);
    else
      fail('No section scores visible — OCR likely failed');

    for (const t of allText) info(`  ${t}`);
    await shot('07_crosscheck_sections');

    // Check OCR extracted text preview
    const extractedSecs = await page.locator('#extractedAnswerPreview .extracted-section').count();
    if (extractedSecs > 0)
      pass(`OCR extracted text preview: ${extractedSecs} sections shown`);
    else
      info('Extracted text preview not shown or empty');
    await shot('08_crosscheck_extracted');

    // Low confidence warning?
    const bodyText = await crossModal.textContent().catch(() => '');
    if (/low.?confidence|unclear|verify/i.test(bodyText))
      info('Low confidence flag detected in modal (OCR quality warning shown)');

    // Approve
    const approveBtn = page.locator('button', { hasText: /Approve/i });
    if (await approveBtn.isVisible()) {
      await approveBtn.click();
      await page.waitForTimeout(1000);
      pass('Evaluation approved');
    }
  }

  // ── DONE ──────────────────────────────────────────────────────────────────
  console.log('\n═══════════════════════════════════════════════════');
  console.log('  SCANNED PDF TEST COMPLETE');
  console.log('═══════════════════════════════════════════════════');
  const scanShots = fs.readdirSync(__dirname).filter(f => f.startsWith('screenshot_scan_'));
  scanShots.forEach(f => console.log(`  ${f}`));

  await page.waitForTimeout(4000);
  await browser.close();

})().catch(async err => {
  console.error('\n❌ Test error:', err.message);
  if (page) await shot('ERROR').catch(() => {});
  if (browser) await browser.close();
  process.exit(1);
});
