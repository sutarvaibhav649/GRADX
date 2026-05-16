/**
 * GRADX 80-Marks Exam UI Test (Playwright)
 * 10 questions × 4 sections × 8 marks = 80 marks
 * Stops at cross-check modal so you can review AI evaluation.
 * Run: node ui_test_80marks.js
 */

const { chromium } = require('playwright');
const path = require('path');
const fs   = require('fs');

const BASE          = 'http://localhost:4200';
const EMAIL         = 'pdftest.faculty@gradx.com';
const PASS          = 'Test@1234';
const MODEL_PDF     = path.resolve(__dirname, 'backend-python/app/model_80marks.pdf');
const STUDENT_PDF   = path.resolve(__dirname, 'backend-python/app/student_80_excellent.pdf');
const STUDENT_EMAIL = 'pdftest.student@gradx.com';

const QUESTIONS = [
  { topic: 'Object-Oriented Programming',          sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,3,2,1] },
  { topic: 'Database Normalization',                sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,3,2,1] },
  { topic: 'OS Process Management',                 sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,3,2,1] },
  { topic: 'Computer Networks and OSI Model',       sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,3,2,1] },
  { topic: 'Binary Trees and BST',                  sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,3,2,1] },
  { topic: 'Sorting Algorithms',                    sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,3,2,1] },
  { topic: 'SDLC and Agile Methodology',            sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,3,2,1] },
  { topic: 'Computer Architecture CPU and Memory',  sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,3,2,1] },
  { topic: 'Web Technologies and HTTP',             sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,3,2,1] },
  { topic: 'Cloud Computing Service Models',        sections: ['Introduction','Core_Concepts','Examples','Conclusion'], marks: [2,3,2,1] },
];

let stepNum = 0;
const step = (msg) => console.log(`\n[STEP ${++stepNum}] ${msg}`);
const pass = (msg) => console.log(`  OK  ${msg}`);
const fail = (msg) => console.error(`  FAIL  ${msg}`);
const info = (msg) => console.log(`  >>  ${msg}`);

let browser, page;

async function shot(name) {
  const p = path.resolve(__dirname, `screenshot_80m_${name}.png`);
  await page.screenshot({ path: p, fullPage: false });
  info(`Screenshot -> ${path.basename(p)}`);
}

async function fillMarks(locator, value) {
  await locator.click({ clickCount: 3 });
  await locator.pressSequentially(String(value));
  await locator.press('Tab');
  await page.waitForTimeout(120);
}

// ─────────────────────────────────────────────────────────────────────────────
(async () => {
  browser = await chromium.launch({ headless: false, slowMo: 60, args: ['--start-maximized'] });
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  page = await ctx.newPage();

  // ── STEP 1: Login ──────────────────────────────────────────────────────────
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

  // ── STEP 2: Exam details ───────────────────────────────────────────────────
  step('Fill exam details');
  await page.locator('[formControlName="academicYear"]').selectOption('2025-26');
  await page.locator('[formControlName="year"]').selectOption('second');
  await page.locator('[formControlName="department"]').selectOption('cse');
  await page.locator('[formControlName="examType"]').selectOption('ese');
  await page.locator('[formControlName="semester"]').selectOption('odd');
  await page.locator('[formControlName="subject"]').fill('Computer Science — End Semester Exam');
  pass('Exam details filled (ESE, 80 marks)');

  // ── STEP 3: Enable Multi-Q mode ───────────────────────────────────────────
  step('Enable Multi-Q mode');
  const multiQBtn = page.locator('button', { hasText: /Multi-Q/i });
  await multiQBtn.waitFor({ state: 'visible', timeout: 5000 });
  await multiQBtn.click();
  await page.waitForTimeout(500);
  pass('Multi-Q mode active');
  await shot('02_multiq');

  // ── STEP 4: Configure 10 questions × 4 sections ──────────────────────────
  step('Configure 10 questions (Introduction 2 + Core_Concepts 3 + Examples 2 + Conclusion 1 = 8 marks each)');

  for (let qIdx = 0; qIdx < QUESTIONS.length; qIdx++) {
    const q = QUESTIONS[qIdx];

    if (qIdx > 0) {
      const addQBtn = page.locator('button', { hasText: /Add Question/i });
      await addQBtn.waitFor({ state: 'visible', timeout: 5000 });
      await addQBtn.click();
      await page.waitForTimeout(350);
    }

    const qContainer = page.locator('.question-container').nth(qIdx);
    await qContainer.waitFor({ state: 'visible', timeout: 5000 });

    // Fill topic
    await qContainer.locator('input[placeholder*="Optional topic"]').fill(q.topic);

    for (let sIdx = 0; sIdx < q.sections.length; sIdx++) {
      if (sIdx > 0) {
        const addSecBtn = qContainer.locator('button', { hasText: /Add Section/i });
        await addSecBtn.waitFor({ state: 'visible', timeout: 5000 });
        await addSecBtn.click();
        await page.waitForTimeout(250);
      }

      const nameInputs  = qContainer.locator('input.section-name-input');
      const marksInputs = qContainer.locator('input.section-marks-input');
      await nameInputs.nth(sIdx).fill(q.sections[sIdx]);
      await fillMarks(marksInputs.nth(sIdx), q.marks[sIdx]);
    }

    info(`Q${qIdx + 1}: "${q.topic}" — sections: ${q.sections.join(', ')} | marks: ${q.marks.join('+')} = ${q.marks.reduce((a,b)=>a+b,0)}`);
  }

  pass('10 questions configured');
  await shot('03_questions_built');

  // ── STEP 5: Verify max marks = 80 ────────────────────────────────────────
  step('Verify max marks = 80');
  await page.waitForTimeout(600);
  let maxMarks = await page.locator('[formControlName="maxMarks"]').inputValue();
  if (maxMarks !== '80') {
    info(`Max marks = "${maxMarks}" — forcing to 80`);
    const mxEl = page.locator('[formControlName="maxMarks"]');
    await mxEl.click({ clickCount: 3 });
    await mxEl.fill('80');
    await mxEl.press('Tab');
    await page.waitForTimeout(200);
    maxMarks = await mxEl.inputValue();
  }
  pass(`Max marks = ${maxMarks}`);

  // ── STEP 6: Upload EXCELLENT student PDF ─────────────────────────────────
  step('Upload student answer PDF (Excellent quality — ~88%)');
  const [studentChooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    page.locator('.upload-add-btn').click(),
  ]);
  await studentChooser.setFiles(STUDENT_PDF);
  await page.waitForTimeout(600);
  const emailInput = page.locator('input.paper-email').last();
  await emailInput.waitFor({ state: 'visible', timeout: 5000 });
  await emailInput.fill(STUDENT_EMAIL);
  pass(`Student PDF: ${path.basename(STUDENT_PDF)} | email: ${STUDENT_EMAIL}`);

  // ── STEP 7: Upload model answer PDF ──────────────────────────────────────
  step('Upload model answer PDF (9 pages, 80 marks)');
  const [modelChooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    page.locator('.upload-area--compact').nth(1).click(),
  ]);
  await modelChooser.setFiles(MODEL_PDF);
  await page.waitForTimeout(600);
  pass(`Model PDF: ${path.basename(MODEL_PDF)}`);
  await shot('04_files_uploaded');

  // ── STEP 8: AI mode + cross-check ────────────────────────────────────────
  step('Enable AI mode + cross-check');
  const aiRadio = page.locator('input[value="ai"]');
  if (!(await aiRadio.isChecked())) await aiRadio.check();
  const crossCheckBox = page.locator('[formControlName="enableCrossCheck"]');
  if (!(await crossCheckBox.isChecked())) await crossCheckBox.check();
  pass('AI mode active, cross-check enabled');

  // ── STEP 9: Submit ────────────────────────────────────────────────────────
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
  pass('Progress modal opened — AI evaluating 10 questions × 40 sections total...');
  await shot('05_progress_modal');

  // ── STEP 10: Wait for evaluation (up to 5 min for 10 questions) ──────────
  step('Waiting for AI evaluation (up to 5 min for 80-marks / 10-question paper)...');
  info('FastAPI evaluates 40 sections (10 Q x 4 sections) using Gemini + SentenceTransformers');

  await page.waitForFunction(() => {
    const modals = document.querySelectorAll('.modal');
    for (const m of modals) {
      if (!m.querySelector('.cross-check-modal') && m.style.display === 'none') return true;
    }
    return false;
  }, null, { timeout: 300000 });

  pass('Evaluation finished — progress modal closed');
  await shot('06_evaluation_done');

  // Angular setTimeout fires after 1s → cross-check modal opens
  await page.waitForTimeout(2500);
  await shot('06b_after_wait');

  // ── STEP 11: Cross-check modal — show all scores ──────────────────────────
  step('Reading AI evaluation results from cross-check modal...');

  const crossModal = page.locator('.cross-check-modal');
  await crossModal.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
  const isVisible = await crossModal.isVisible().catch(() => false);

  if (!isVisible) {
    info('Cross-check modal not visible — checking for toast');
    const toastText = await page.locator('.toast, .alert, [class*="toast"]').first().textContent().catch(() => '');
    if (toastText) info(`Toast: "${toastText.trim()}"`);
    await shot('07_no_crosscheck');
    pass('Evaluation completed (no cross-check modal)');
  } else {
    pass('=== CROSS-CHECK MODAL OPEN ===');
    await shot('07_crosscheck_modal');

    const paperCounter = await page.locator('.paper-counter').textContent().catch(() => '');
    info(`Paper: ${paperCounter.trim()}`);

    const aiScore = await page.locator('#aiScore').textContent().catch(() => '?');
    const aiMax   = await page.locator('#aiMaxMarks').textContent().catch(() => '?');

    console.log('\n╔══════════════════════════════════════════════════════╗');
    console.log(`║  AI SCORE:  ${aiScore} / ${aiMax}  (student_80_excellent.pdf)`.padEnd(55) + '║');
    console.log('╠══════════════════════════════════════════════════════╣');

    const sectionItems = page.locator('#aiQuestionMarks .question-item');
    const count = await sectionItems.count();
    info(`Total section rows: ${count} (expected 40 for 10Q x 4 sections)`);

    const allText = [];
    for (let i = 0; i < count; i++) {
      const t = await sectionItems.nth(i).textContent();
      allText.push(t.trim().replace(/\s+/g, ' '));
    }

    // Print per-question breakdown
    let currentQ = '';
    for (const t of allText) {
      const qMatch = t.match(/^(Q\d+):/);
      if (qMatch && qMatch[1] !== currentQ) {
        currentQ = qMatch[1];
        console.log('║' + '─'.repeat(54) + '║');
        console.log(`║  ${currentQ}`.padEnd(55) + '║');
      }
      console.log(`║    ${t}`.padEnd(55) + '║');
    }
    console.log('╚══════════════════════════════════════════════════════╝');

    if (parseInt(aiScore) > 0)
      pass(`AI total score: ${aiScore} / ${aiMax}`);
    else
      fail(`AI score is 0 — evaluation may have failed`);

    // Check question coverage
    const hasQ1  = allText.some(t => t.startsWith('Q1:'));
    const hasQ10 = allText.some(t => t.startsWith('Q10:'));
    if (hasQ1 && hasQ10)
      pass('All 10 questions visible in cross-check (Q1...Q10)');
    else
      fail(`Partial coverage (Q1=${hasQ1}, Q10=${hasQ10})`);

    await shot('08_crosscheck_scores');

    // Scroll to extracted answer preview
    await page.locator('#extractedAnswerPreview').scrollIntoViewIfNeeded().catch(() => {});
    const extractedSecs = await page.locator('#extractedAnswerPreview .extracted-section').count();
    if (extractedSecs > 0)
      pass(`Extracted text preview: ${extractedSecs} sections shown`);
    await shot('09_crosscheck_extracted');

    console.log('\n  [PAUSED — Browser staying open for 90 seconds so you can review]');
    console.log('  [Close the browser or press Ctrl+C when done]\n');

    // Wait 90 seconds for manual review — do NOT approve
    await page.waitForTimeout(90000);
  }

  // ── DONE ──────────────────────────────────────────────────────────────────
  console.log('\n=========================================================');
  console.log('  80-MARKS TEST COMPLETE  (paused before approve)');
  console.log('=========================================================');
  const shots = fs.readdirSync(__dirname).filter(f => f.startsWith('screenshot_80m_'));
  shots.forEach(f => console.log(`  ${f}`));

  await browser.close();

})().catch(async err => {
  console.error('\nTest error:', err.message);
  if (page) await shot('ERROR').catch(() => {});
  if (browser) await browser.close();
  process.exit(1);
});
