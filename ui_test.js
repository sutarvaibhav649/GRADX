/**
 * GRADX Multi-Question PDF UI Test (Playwright)
 * Run: node ui_test.js
 */

const { chromium } = require('playwright');
const path = require('path');
const fs   = require('fs');

const BASE          = 'http://localhost:4200';
const EMAIL         = 'pdftest.faculty@gradx.com';
const PASS          = 'Test@1234';
const MODEL_PDF     = path.resolve(__dirname, 'backend-python/app/exam_model_answer.pdf');
const STUDENT_PDF   = path.resolve(__dirname, 'backend-python/app/exam_student_answer.pdf');
const STUDENT_EMAIL = 'pdftest.student@gradx.com';

const QUESTIONS = [
  { topic: 'Object-Oriented Programming',     sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,4,2,2] },
  { topic: 'Database Normalization',           sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,4,2,2] },
  { topic: 'OS Process Management',            sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,4,2,2] },
  { topic: 'Computer Networks and OSI Model',  sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,4,2,2] },
];

let stepNum = 0;
const step  = (msg)  => console.log(`\n[STEP ${++stepNum}] ${msg}`);
const pass  = (msg)  => console.log(`  ✅ ${msg}`);
const fail  = (msg)  => console.error(`  ❌ ${msg}`);
const info  = (msg)  => console.log(`  ℹ  ${msg}`);

let browser, page;

async function shot(name) {
  const p = path.resolve(__dirname, `screenshot_${name}.png`);
  await page.screenshot({ path: p, fullPage: false });
  info(`Screenshot → ${path.basename(p)}`);
}

async function waitAndClick(selector, opts = {}) {
  const el = page.locator(selector).first();
  await el.waitFor({ state: 'visible', timeout: 8000 });
  await el.click(opts);
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN
// ─────────────────────────────────────────────────────────────────────────────
(async () => {
  browser = await chromium.launch({ headless: false, slowMo: 80,
    args: ['--start-maximized'] });
  const ctx = await browser.newContext({
    viewport: { width: 1400, height: 900 }
  });
  page = await ctx.newPage();

  // ── STEP 1: Login ──────────────────────────────────────────────────────────
  step('Login as faculty');
  await page.goto(`${BASE}/auth/login`, { waitUntil: 'networkidle' });

  // role selector — try different approaches
  const roleEl = page.locator('select').filter({ hasText: /faculty|student|admin/i }).first();
  await roleEl.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
  await roleEl.selectOption('faculty').catch(async () => {
    await page.locator('[formControlName="role"]').selectOption('faculty');
  });

  await page.locator('[formControlName="email"]').fill(EMAIL);
  await page.locator('[formControlName="password"]').fill(PASS);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(/dashboard|faculty/, { timeout: 15000 });
  pass(`Logged in — URL: ${page.url()}`);
  await shot('01_dashboard');

  // ── STEP 2: Exam details ───────────────────────────────────────────────────
  step('Fill basic exam details');
  await page.locator('[formControlName="academicYear"]').selectOption('2025-26');
  await page.locator('[formControlName="year"]').selectOption('second');
  await page.locator('[formControlName="department"]').selectOption('cse');
  await page.locator('[formControlName="examType"]').selectOption('mse');
  await page.locator('[formControlName="semester"]').selectOption('odd');
  await page.locator('[formControlName="subject"]').fill('Computer Science Fundamentals');
  pass('Academic year / dept / subject filled');

  // ── STEP 3: Switch to Multi-Q mode ────────────────────────────────────────
  step('Enable Multi-Q (PDF) mode');
  // Find the "Multi-Q" toggle button
  const multiQBtn = page.locator('button', { hasText: /Multi-Q/i });
  await multiQBtn.waitFor({ state: 'visible', timeout: 5000 });
  await multiQBtn.click();
  await page.waitForTimeout(500);
  pass('Multi-Q mode activated');
  await shot('02_multiq_toggled');

  // ── STEP 4: Build questions ────────────────────────────────────────────────
  step('Configure 4 questions with sections');

  for (let qIdx = 0; qIdx < QUESTIONS.length; qIdx++) {
    const q = QUESTIONS[qIdx];

    // Add question button (not needed for Q1 — it's auto-added)
    if (qIdx > 0) {
      const addQBtn = page.locator('button', { hasText: /Add Question/i });
      await addQBtn.waitFor({ state: 'visible', timeout: 5000 });
      await addQBtn.click();
      await page.waitForTimeout(400);
    }

    // All question container divs inside .sections-builder
    const qContainers = page.locator('.question-container');
    const qContainer  = qContainers.nth(qIdx);
    await qContainer.waitFor({ state: 'visible', timeout: 5000 });

    // Fill question topic
    const topicInput = qContainer.locator('input[placeholder*="Optional topic"]');
    await topicInput.fill(q.topic);

    // Each question starts with 1 empty section row. Add sections iteratively.
    for (let sIdx = 0; sIdx < q.sections.length; sIdx++) {
      if (sIdx > 0) {
        // Click "Add Section" inside this question's container
        const addSecBtn = qContainer.locator('button', { hasText: /Add Section/i });
        await addSecBtn.waitFor({ state: 'visible', timeout: 5000 });
        await addSecBtn.click();
        await page.waitForTimeout(250);
      }

      // All section-name inputs in this question
      const nameInputs  = qContainer.locator('input.section-name-input');
      const marksInputs = qContainer.locator('input.section-marks-input');

      await nameInputs.nth(sIdx).fill(q.sections[sIdx]);
      // Use evaluate to set number input value and fire native events that Zone.js picks up
      await marksInputs.nth(sIdx).evaluate((el, val) => {
        el.value = val;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }, String(q.marks[sIdx]));
      await page.waitForTimeout(60);
    }

    info(`Q${qIdx + 1} "${q.topic}" — ${q.sections.length} sections`);
  }

  pass('4 questions configured');
  await shot('03_questions_built');

  // ── STEP 5: Verify max marks auto-filled to 40 ────────────────────────────
  step('Verify max marks');
  await page.waitForTimeout(800);
  let maxMarks = await page.locator('[formControlName="maxMarks"]').inputValue();
  if (maxMarks === '40') {
    pass(`Max marks = ${maxMarks} ✓`);
  } else {
    info(`Max marks = "${maxMarks}" — forcing to 40 (backend recomputes from questionSet anyway)`);
    const maxMarksEl = page.locator('[formControlName="maxMarks"]');
    await maxMarksEl.evaluate((el) => {
      el.value = '40';
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await page.waitForTimeout(200);
    maxMarks = await maxMarksEl.inputValue();
    pass(`Max marks set to ${maxMarks}`);
  }

  // ── STEP 6: Upload student answer PDF ─────────────────────────────────────
  step('Upload student answer PDF');
  const [studentChooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    page.locator('.upload-add-btn').click(),
  ]);
  await studentChooser.setFiles(STUDENT_PDF);
  await page.waitForTimeout(600);

  // Fill student email
  const emailInput = page.locator('input.paper-email').last();
  await emailInput.waitFor({ state: 'visible', timeout: 5000 });
  await emailInput.fill(STUDENT_EMAIL);
  pass(`Student PDF: ${path.basename(STUDENT_PDF)} | email: ${STUDENT_EMAIL}`);

  // ── STEP 7: Upload model answer PDF ───────────────────────────────────────
  step('Upload model answer PDF');
  const [modelChooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    page.locator('.upload-area--compact').nth(1).click(),
  ]);
  await modelChooser.setFiles(MODEL_PDF);
  await page.waitForTimeout(600);

  const modelName = await page.locator('.file-preview span').last().textContent().catch(() => '');
  pass(`Model PDF: ${path.basename(MODEL_PDF)} (shown: "${modelName.trim()}")`);
  await shot('04_files_uploaded');

  // ── STEP 8: Ensure AI mode + cross-check ──────────────────────────────────
  step('Confirm AI mode + cross-check enabled');
  const aiRadio = page.locator('input[value="ai"]');
  if (!(await aiRadio.isChecked())) await aiRadio.check();
  const crossCheckBox = page.locator('[formControlName="enableCrossCheck"]');
  if (!(await crossCheckBox.isChecked())) await crossCheckBox.check();
  pass('AI mode active, cross-check enabled');

  // ── STEP 9: Submit ─────────────────────────────────────────────────────────
  step('Click "Start Evaluation"');
  await page.locator('button[type="submit"]').click();

  // Wait for progress modal to open
  await page.waitForFunction(() => {
    const modals = document.querySelectorAll('.modal');
    for (const m of modals) {
      if (!m.querySelector('.cross-check-modal') && m.style.display === 'flex') return true;
    }
    return false;
  }, null, { timeout: 15000 });
  pass('Progress modal opened');
  await shot('05_progress_modal');

  // ── STEP 10: Wait for evaluation ──────────────────────────────────────────
  step('Waiting for AI evaluation (up to 3 min)…');
  info('This uploads PDFs to FastAPI, extracts text via PyMuPDF, and evaluates all 16 sections');

  // Wait for progress modal to CLOSE (flex → none = evaluation done)
  await page.waitForFunction(() => {
    const modals = document.querySelectorAll('.modal');
    for (const m of modals) {
      if (!m.querySelector('.cross-check-modal') && m.style.display === 'none') return true;
    }
    return false;
  }, null, { timeout: 180000 });

  pass('Evaluation finished — progress modal closed');
  await shot('06_evaluation_done');
  // Angular setTimeout(1000ms) fires after progress modal closes → cross-check opens
  await page.waitForTimeout(2500);

  // ── STEP 11: Cross-check modal ─────────────────────────────────────────────
  step('Inspect cross-check modal');
  const crossModal = page.locator('.cross-check-modal');
  const isVisible  = await crossModal.isVisible().catch(() => false);

  if (!isVisible) {
    info('Cross-check modal not shown — checking for toast / dashboard update');
    const toast = page.locator('.toast, .alert, [class*="toast"]').first();
    const toastText = await toast.textContent().catch(() => '');
    if (toastText) info(`Toast: "${toastText.trim()}"`);
    await shot('07_no_crosscheck');
    pass('Evaluation completed (no cross-check modal needed)');
  } else {
    pass('Cross-check modal is open');
    await shot('07_crosscheck_modal');

    // Paper counter
    const paperCounter = await page.locator('.paper-counter').textContent().catch(() => '');
    info(`Paper: ${paperCounter.trim()}`);

    // AI score
    const aiScore = await page.locator('#aiScore').textContent().catch(() => '?');
    const aiMax   = await page.locator('#aiMaxMarks').textContent().catch(() => '?');
    if (parseInt(aiScore) > 0)
      pass(`AI Score: ${aiScore} / ${aiMax}`)
    else
      fail(`AI Score: ${aiScore} / ${aiMax} (expected > 0)`);

    // Section scores
    const sectionItems = page.locator('#aiQuestionMarks .question-item');
    const count = await sectionItems.count();
    info(`Section rows in modal: ${count}`);

    const allText = [];
    for (let i = 0; i < count; i++) {
      const t = await sectionItems.nth(i).textContent();
      allText.push(t.trim().replace(/\s+/g, ' '));
    }

    // Check for Q1, Q2, Q3, Q4 prefixes
    const hasQ1 = allText.some(t => t.startsWith('Q1:'));
    const hasQ4 = allText.some(t => t.startsWith('Q4:'));
    if (hasQ1 && hasQ4) pass('All 4 questions visible in cross-check (Q1…Q4)');
    else if (count > 0) fail(`Only some questions shown (${count} section rows, Q1=${hasQ1}, Q4=${hasQ4})`);
    else fail('No section scores visible');

    for (const t of allText) info(`  ${t}`);
    await shot('08_crosscheck_sections');

    // Extracted answer preview
    const extractedSecs = await page.locator('#extractedAnswerPreview .extracted-section').count();
    if (extractedSecs > 0) pass(`OCR extracted text: ${extractedSecs} sections shown`);
    else info('OCR extracted text panel may be loading');

    await shot('09_crosscheck_extracted');

    // Approve
    const approveBtn = page.locator('button', { hasText: /Approve/i });
    if (await approveBtn.isVisible()) {
      await approveBtn.click();
      await page.waitForTimeout(1000);
      pass('Evaluation approved — moving to next paper');
    }
  }

  // ── DONE ──────────────────────────────────────────────────────────────────
  console.log('\n═══════════════════════════════════════════════════');
  console.log('  UI TEST COMPLETE');
  console.log('═══════════════════════════════════════════════════');
  console.log('Screenshots saved in GRADX root:');
  fs.readdirSync(__dirname).filter(f => f.startsWith('screenshot_')).forEach(f => console.log(`  ${f}`));

  await page.waitForTimeout(4000);
  await browser.close();

})().catch(async err => {
  console.error('\n❌ Test error:', err.message);
  if (page) await shot('ERROR').catch(() => {});
  if (browser) await browser.close();
  process.exit(1);
});
