import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, FormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { UpperCasePipe, CommonModule } from '@angular/common';
import { AuthService } from '../../shared/services/auth.service';
import { FacultyService } from '../../shared/services/faculty.service';
import { ToastService } from '../../shared/toast.service';
import { Subscription } from 'rxjs';
import { environment } from '../../../environments/environment';

type StudentOption = {
  _id: string;
  fullName: string;
  email: string;
  idNumber?: string;
  department?: string;
};

@Component({
  selector: 'app-faculty-dashboard',
  imports: [ReactiveFormsModule, FormsModule, UpperCasePipe, CommonModule, RouterLink],
  templateUrl: './faculty-dashboard.component.html',
  styleUrl: './faculty-dashboard.component.css',
})
export class FacultyDashboardComponent implements OnInit, OnDestroy {
  private finalizeS?: Subscription;
  private progressInterval?: ReturnType<typeof setInterval>;

  uploadForm!: FormGroup;

  stats = { papersUploaded: 0, aiEvaluated: 0, manuallyEvaluated: 0, pendingEvaluation: 0 };
  recentExams: any[] = [];
  availableStudents: StudentOption[] = [];

  selectedStudentPapers: Array<{ file: File; email: string }> = [];
  selectedModelAnswer: File | null = null;

  isSubmitting = false;
  showProgressModal = false;
  showCrossCheckModal = false;

  // Enhanced Progress Tracking
  totalPapers = 0;
  processedPapers = 0;
  successfulPapers = 0;
  progressPercentage = 0;
  evaluationLogs: Array<{ message: string; type: 'info' | 'success' | 'error' }> = [];

  // Cross-check data
  crossCheckPapers: any[] = [];
  currentPaperIndex = 0;
  currentPaperTotal = 0;
  currentEvaluationData: any = null;
  currentSectionNames: string[] = [];

  // Phase 1.1: Custom question sections (single-question mode)
  selectedSections: { name: string; marks: number }[] = [];

  // Multi-question mode
  isMultiQuestion = false;
  questionSet: Array<{ questionText: string; sections: { name: string; marks: number }[] }> = [];

  get totalSectionMarks(): number {
    return this.selectedSections.reduce((sum, s) => sum + (s.marks || 0), 0);
  }

  get totalQuestionSetMarks(): number {
    return this.questionSet.reduce(
      (sum, q) => sum + q.sections.reduce((s2, sec) => s2 + (sec.marks || 0), 0), 0
    );
  }

  toggleMultiQuestion() {
    this.isMultiQuestion = !this.isMultiQuestion;
    if (this.isMultiQuestion && this.questionSet.length === 0) {
      this.addQuestion();
    }
    this.syncMaxMarks();
  }

  addQuestion() {
    this.questionSet.push({ questionText: '', sections: [{ name: '', marks: 0 }] });
    this.syncMaxMarks();
  }

  removeQuestion(index: number) {
    this.questionSet.splice(index, 1);
    this.syncMaxMarks();
  }

  addQuestionSection(qIdx: number) {
    this.questionSet[qIdx].sections.push({ name: '', marks: 0 });
    this.syncMaxMarks();
  }

  removeQuestionSection(qIdx: number, sIdx: number) {
    this.questionSet[qIdx].sections.splice(sIdx, 1);
    this.syncMaxMarks();
  }

  syncMaxMarks() {
    if (this.isMultiQuestion) {
      if (this.totalQuestionSetMarks > 0) {
        this.uploadForm.get('maxMarks')?.setValue(this.totalQuestionSetMarks);
      }
    } else if (this.selectedSections.length > 0) {
      this.uploadForm.get('maxMarks')?.setValue(this.totalSectionMarks);
    }
  }

  addSection() {
    this.selectedSections.push({ name: '', marks: 0 });
    this.syncMaxMarksFromSections();
  }

  removeSection(index: number) {
    this.selectedSections.splice(index, 1);
    this.syncMaxMarksFromSections();
  }

  syncMaxMarksFromSections() {
    if (this.selectedSections.length > 0) {
      this.uploadForm.get('maxMarks')?.setValue(this.totalSectionMarks);
    }
  }

  get userInitial() { return this.auth.getUser()?.fullName?.charAt(0)?.toUpperCase() || 'F'; }
  get userName() { return this.auth.getUser()?.fullName || 'Faculty'; }

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private facultyService: FacultyService,
    private router: Router,
    private toastService: ToastService
  ) {}

  ngOnDestroy(): void {
    this.finalizeS?.unsubscribe();
    if (this.progressInterval) clearInterval(this.progressInterval);
  }

  ngOnInit() {
    this.initForm();
    this.loadDashboard();
    this.loadAvailableStudents();
  }

  private initForm() {
    this.uploadForm = this.fb.group({
      academicYear: ['', Validators.required],
      year: ['', Validators.required],
      department: ['', Validators.required],
      examType: ['', Validators.required],
      semester: ['', Validators.required],
      maxMarks: [''],
      subject: ['', Validators.required],
      evaluationMode: ['ai'],
      enableCrossCheck: [true],
      evaluationStrictness: ['moderate']
    });
  }

  loadDashboard() {
    this.facultyService.getDashboard().subscribe({
      next: (res) => {
        this.stats = res.data.stats;
        this.recentExams = res.data.recentExams;
      },
      error: (err: any) => {
        this.toastService.show('error', 'Failed to load dashboard data.');
      }
    });
  }

  loadAvailableStudents() {
    this.facultyService.getAvailableStudents().subscribe({
      next: (res) => {
        this.availableStudents = res.data || [];
      },
      error: () => {
        this.toastService.show('error', 'Failed to load available students.');
      }
    });
  }

  manualEvaluate() {
    this.toastService.show('info', 'Manual evaluation feature coming soon!');
  }

  viewResults() {
    this.toastService.show('info', 'View results feature coming soon!');
  }

  finalizeEvaluation(examId: string) {
    this.finalizeS = this.facultyService.finalizeResult(examId).subscribe({
      next: (res) => {
        this.toastService.show('success', res.message || 'Results finalized successfully!');
        this.loadDashboard();
      },
      error: (err: any) => {
        console.error('Error finalizing results:', err);
        this.toastService.show('error', err.error?.message || 'Failed to finalize results.');
      }
    });
  }

  updateMaxMarks() {
    // Only auto-fill if no custom sections are defined (sections override the total)
    if (this.selectedSections.length === 0) {
      const examType = this.uploadForm.get('examType')?.value;
      const marks: Record<string, number> = { mse: 30, ese: 80, makeup: 80, quiz: 20 };
      this.uploadForm.patchValue({ maxMarks: marks[examType] ?? '' });
    }
  }

  onStudentPapersChange(event: Event) {
    const input = event.target as HTMLInputElement;
    const files = Array.from(input.files || []);
    const newPapers = files.map((file) => ({ file, email: '' }));
    this.selectedStudentPapers = [...this.selectedStudentPapers, ...newPapers];
    input.value = '';
  }

  updateStudentPaperStudent(index: number, email: string) {
    if (index < 0 || index >= this.selectedStudentPapers.length) {
      return;
    }
    this.selectedStudentPapers[index].email = email;
  }

  getStudentsForCurrentExam(): StudentOption[] {
    const selectedDepartment = this.uploadForm?.get('department')?.value;
    if (!selectedDepartment) {
      return [];
    }
    return this.availableStudents.filter((student) => student.department === selectedDepartment);
  }

  get hasSelectedDepartment(): boolean {
    return Boolean(this.uploadForm?.get('department')?.value);
  }

  isStudentAlreadySelected(email: string, currentIndex: number): boolean {
    return this.selectedStudentPapers.some((paper, index) => index !== currentIndex && paper.email === email);
  }

  removeStudentPaper(index: number) {
    if (index < 0 || index >= this.selectedStudentPapers.length) {
      return;
    }
    this.selectedStudentPapers.splice(index, 1);
  }

  onModelAnswerChange(event: Event) {
    const input = event.target as HTMLInputElement;
    this.selectedModelAnswer = input.files?.[0] || null;
  }

  addLogMessage(message: string, type: 'info' | 'success' | 'error') {
    this.evaluationLogs.push({ message, type });
  }

  updateProgress(percentage: number, processed: number, successful: number) {
    this.progressPercentage = percentage;
    this.processedPapers = processed;
    this.successfulPapers = successful;
  }

  submitEvaluation() {
    if (this.uploadForm.invalid) {
      this.uploadForm.markAllAsTouched();
      this.toastService.show('error', 'Please fill in all required fields correctly.');
      return;
    }
    if (this.selectedStudentPapers.length === 0) {
      this.toastService.show('error', 'Please upload at least one student answer sheet file.');
      return;
    }
    if (this.selectedStudentPapers.some((paper) => !paper.email?.trim())) {
      this.toastService.show('error', 'Please select a student for each uploaded answer sheet.');
      return;
    }
    const selectedEmails = this.selectedStudentPapers.map((paper) => paper.email.trim());
    if (new Set(selectedEmails).size !== selectedEmails.length) {
      this.toastService.show('error', 'Each student can be selected only once per exam.');
      return;
    }
    const availableStudentEmails = new Set(this.getStudentsForCurrentExam().map((student) => student.email));
    const invalidStudent = selectedEmails.some((email) => !availableStudentEmails.has(email));
    if (invalidStudent) {
      this.toastService.show('error', 'Please select only active registered students from the selected department.');
      return;
    }
    if (!this.selectedModelAnswer) {
      this.toastService.show('error', 'Please select the model answer image.');
      return;
    }

    // Validate question config BEFORE setting isSubmitting so form is never stuck
    if (this.isMultiQuestion) {
      if (this.questionSet.length === 0) {
        this.toastService.show('error', 'Add at least one question in multi-question mode.');
        return;
      }
      for (const q of this.questionSet) {
        const invalid = q.sections.filter(s => !s.name.trim() || s.marks <= 0);
        if (invalid.length > 0) {
          this.toastService.show('error', 'Each section must have a name and marks greater than 0.');
          return;
        }
      }
    } else if (this.selectedSections.length > 0) {
      const invalidSections = this.selectedSections.filter(s => !s.name.trim() || s.marks <= 0);
      if (invalidSections.length > 0) {
        this.toastService.show('error', 'Each section must have a name and marks greater than 0.');
        return;
      }
    }

    this.isSubmitting = true;
    this.showProgressModal = true;

    this.totalPapers = this.selectedStudentPapers.length;
    this.processedPapers = 0;
    this.successfulPapers = 0;
    this.progressPercentage = 0;
    this.evaluationLogs = [];
    this.addLogMessage('Starting evaluation process...', 'info');

    const fd = new FormData();
    const raw = this.uploadForm.getRawValue();
    Object.entries(raw).forEach(([key, val]) => fd.append(key, String(val)));
    this.selectedStudentPapers.forEach((paper) => {
      fd.append('studentPapers', paper.file);
      fd.append('studentEmails', paper.email.trim());
    });
    fd.append('modelAnswer', this.selectedModelAnswer!);
    if (this.isMultiQuestion && this.questionSet.length > 0) {
      // Multi-question: send questionSet JSON
      const qsPayload = this.questionSet.map((q, idx) => ({
        number: idx + 1,
        text: q.questionText.trim(),
        sections: q.sections.map(s => ({ name: s.name.trim(), marks: s.marks }))
      }));
      fd.append('questionSet', JSON.stringify(qsPayload));
    } else if (this.selectedSections.length > 0) {
      fd.append('questions', JSON.stringify(this.selectedSections));
    }

    this.facultyService.createExam(fd).subscribe({
      next: (examRes) => {
        const examId = examRes.data._id;
        this.addLogMessage(`Exam created successfully with ID: ${examId}`, 'success');

        if (raw['evaluationMode'] === 'ai') {
          this.startAIEvaluationWithProgress(examId);
        } else {
          this.isSubmitting = false;
          this.showProgressModal = false;
          this.toastService.show('success', 'Exam uploaded successfully. Manual evaluation pending.');
          this.resetFormAfterSubmit();
        }
      },
      error: (err) => {
        this.isSubmitting = false;
        this.showProgressModal = false;
        this.toastService.show('error', err.error?.message || 'Upload failed.');
        this.addLogMessage(`Upload failed: ${err.error?.message || 'Unknown error'}`, 'error');
      }
    });
  }

  private startAIEvaluationWithProgress(examId: string) {
    this.addLogMessage('Starting AI evaluation...', 'info');
    this.simulateProgress();
    
    this.facultyService.startEvaluation(examId).subscribe({
      next: (evalRes: any) => {
        this.addLogMessage(`Evaluation completed! Processing results...`, 'success');
        // Show any backend warnings (skipped students, mock scores used)
        if (evalRes.warnings?.length) {
          evalRes.warnings.forEach((w: string) => {
            this.addLogMessage(w, 'error');
            this.toastService.show('warn', w);
          });
        }
        this.updateProgress(100, this.totalPapers, this.totalPapers);
        
        setTimeout(() => {
          this.isSubmitting = false;
          this.showProgressModal = false;
          
          const enableCrossCheck = this.uploadForm.get('enableCrossCheck')?.value;
          
          if (enableCrossCheck && evalRes.data?.results) {
            this.crossCheckPapers = evalRes.data.results.map((result: any) => {
              const extractedAnswer = result.extractedAnswer || {};
              const aiDetails = result.aiEvaluationDetails || {};
              const filePath = result.studentAnswerSheet?.filePath || '';
              const studentAnswerSheetUrl = this.toFileUrl(filePath);
              const studentAnswerSheetName = result.studentAnswerSheet?.originalName || filePath;
              const isStudentAnswerSheetPdf = String(studentAnswerSheetName).toLowerCase().includes('.pdf');

              return {
                resultId: result._id,
                studentEmail: result.studentAnswerSheet?.email || '',
                studentAnswerSheetUrl,
                isStudentAnswerSheetPdf,
                usedMockEvaluation: result.usedMockEvaluation === true,
                lowConfidence: aiDetails.low_confidence === true,
                confidenceNote: aiDetails.confidence_note || null,
                success: true,
                student_extracted: {
                  Answer: Object.keys(extractedAnswer).length > 0 ? extractedAnswer : (aiDetails.student_text || {})
                },
                evaluation: {
                  total_marks: result.totalMarksObtained || result.aiScore || 0,
                  max_marks: result.maxMarks || 0,
                  percentage: result.percentage || 0,
                  section_scores: aiDetails.section_scores || {},
                  feedback: aiDetails.feedback || {
                    strengths: [],
                    improvements: [],
                    warnings: []
                  }
                }
              };
            });
            
            this.currentPaperTotal = this.crossCheckPapers.length;
            this.currentPaperIndex = 0;
            this.showCrossCheckModal = true;
            this.loadCurrentPaperForCrossCheck();
          } else if (enableCrossCheck) {
            this.toastService.show('warn', 'Evaluation completed but no results were returned for cross-check.');
          } else {
            this.toastService.show('success', evalRes.message || 'Evaluation completed!');
          }
          
          this.resetFormAfterSubmit();
          this.loadDashboard();
        }, 1000);
      },
      error: (err) => {
        this.isSubmitting = false;
        this.showProgressModal = false;
        this.toastService.show('error', err.error?.message || 'Evaluation failed.');
        this.addLogMessage(`Evaluation failed: ${err.error?.message || 'Unknown error'}`, 'error');
      }
    });
  }

  private simulateProgress() {
    let progress = 0;
    if (this.progressInterval) clearInterval(this.progressInterval);
    this.progressInterval = setInterval(() => {
      if (progress < 90 && this.showProgressModal) {
        progress += 10;
        this.progressPercentage = progress;
        this.processedPapers = Math.floor((progress / 100) * this.totalPapers);
        if (progress % 20 === 0) {
          this.addLogMessage(`Processing papers... ${progress}% complete`, 'info');
        }
      } else {
        clearInterval(this.progressInterval);
        this.progressInterval = undefined;
      }
    }, 800);
  }

  private resetFormAfterSubmit() {
    this.uploadForm.reset({
      evaluationMode: 'ai',
      enableCrossCheck: true,
      evaluationStrictness: 'moderate',
      academicYear: '',
      year: '',
      department: '',
      examType: '',
      semester: '',
      subject: '',
      maxMarks: ''
    });
    this.selectedStudentPapers = [];
    this.selectedModelAnswer = null;
    this.selectedSections = [];
    this.questionSet = [];
    this.isMultiQuestion = false;
  }

  loadCurrentPaperForCrossCheck() {
    if (this.currentPaperIndex >= this.crossCheckPapers.length) {
      this.closeCrossCheckModal();
      this.toastService.show('success', 'Cross-checking completed! All papers have been reviewed.');
      return;
    }
    
    const paper = this.crossCheckPapers[this.currentPaperIndex];
    this.currentEvaluationData = paper;
    
    setTimeout(() => {
      this.updateCrossCheckModal(paper);
    }, 100);
  }

  private updateCrossCheckModal(paper: any) {
    const evaluation = paper.evaluation || {};
    const extracted = paper.student_extracted?.Answer || {};

    // Phase 3.4: Show/hide low OCR confidence warning banner
    let bannerEl = document.getElementById('ocrConfidenceBanner');
    if (!bannerEl) {
      // Create it once, insert at top of modal-body
      bannerEl = document.createElement('div');
      bannerEl.id = 'ocrConfidenceBanner';
      bannerEl.style.cssText = 'background:#fff3cd;color:#856404;border:1px solid #ffc107;border-radius:8px;padding:10px 14px;margin-bottom:12px;display:none;';
      const modalBody = document.querySelector('.cross-check-modal .modal-body');
      if (modalBody) modalBody.prepend(bannerEl);
    }
    if (paper.lowConfidence) {
      bannerEl.style.display = 'block';
      bannerEl.innerHTML = `<i class="fas fa-exclamation-triangle"></i> <strong>Low OCR Confidence</strong> — ${paper.confidenceNote || 'Handwriting may be unclear. Please verify marks manually.'}`;
    } else {
      bannerEl.style.display = 'none';
    }
    
    // Update AI Score
    const aiScoreEl = document.getElementById('aiScore');
    const aiMaxMarksEl = document.getElementById('aiMaxMarks');
    if (aiScoreEl) aiScoreEl.textContent = evaluation.total_marks?.toString() || '0';
    if (aiMaxMarksEl) aiMaxMarksEl.textContent = evaluation.max_marks?.toString() || '0';
    
    // Update Manual Score input
    const manualScoreEl = document.getElementById('manualScore') as HTMLInputElement;
    const manualMaxMarksEl = document.getElementById('manualMaxMarks');
    if (manualScoreEl) {
      manualScoreEl.value = evaluation.total_marks?.toString() || '0';
      manualScoreEl.max = evaluation.max_marks || 0;
    }
    if (manualMaxMarksEl) manualMaxMarksEl.textContent = evaluation.max_marks?.toString() || '0';
    
    const hasSectionScores = evaluation.section_scores && Object.keys(evaluation.section_scores).length > 0;
    const isMock = paper?.usedMockEvaluation === true;
    // Use actual section names from the AI result (supports any custom sections)
    this.currentSectionNames = hasSectionScores ? Object.keys(evaluation.section_scores) : [];

    // Update Section-wise AI Marks
    const aiQuestionMarks = document.getElementById('aiQuestionMarks');
    if (aiQuestionMarks) {
      aiQuestionMarks.innerHTML = '';
      if (hasSectionScores) {
        const sections = this.currentSectionNames;
        sections.forEach(section => {
          const sectionData = evaluation.section_scores[section];
          if (sectionData) {
            const semanticScore = sectionData.scores?.semantic_similarity
              ? Math.round(sectionData.scores.semantic_similarity * 100)
              : 0;
            const div = document.createElement('div');
            div.className = 'question-item';
            div.innerHTML = `
              <span class="question-name">${section}</span>
              <span class="question-score">
                ${sectionData.marks_awarded}/${sectionData.max_marks}
                <small style="font-size:0.7rem; color:#6c757d; margin-left:8px;">(${semanticScore}% match)</small>
              </span>
            `;
            aiQuestionMarks.appendChild(div);
          }
        });
      } else {
        aiQuestionMarks.innerHTML = `<p style="color:#856404; background:#fff3cd; padding:8px; border-radius:6px; margin:0;">
          ${isMock ? '⚠️ Mock score used — AI was unavailable when this paper was evaluated.' : 'Section breakdown not available.'}
        </p>`;
      }
    }

    // Update Manual Adjustment Inputs
    const manualQuestionMarks = document.getElementById('manualQuestionMarks');
    if (manualQuestionMarks) {
      manualQuestionMarks.innerHTML = '';
      if (hasSectionScores) {
        const sections = this.currentSectionNames;
        sections.forEach(section => {
          const sectionData = evaluation.section_scores[section];
          if (sectionData) {
            const div = document.createElement('div');
            div.className = 'question-item';
            div.innerHTML = `
              <span class="question-name">${section}</span>
              <span class="question-score">
                <input type="number" class="mark-adjust-input"
                       id="manual_${section}"
                       value="${sectionData.marks_awarded}"
                       min="0" max="${sectionData.max_marks}"
                       step="0.5">
                <span style="margin-left: 4px;">/ ${sectionData.max_marks}</span>
              </span>
            `;
            manualQuestionMarks.appendChild(div);
          }
        });
        sections.forEach(section => {
          const input = document.getElementById(`manual_${section}`) as HTMLInputElement;
          if (input) {
            input.addEventListener('input', () => this.updateManualScore());
          }
        });
      } else {
        // No section scores — show a single manual input for the total
        const totalMaxMarks = evaluation.max_marks || 0;
        const currentScore = evaluation.total_marks || 0;
        manualQuestionMarks.innerHTML = `
          <div class="question-item">
            <span class="question-name">Total Score</span>
            <span class="question-score">
              <input type="number" class="mark-adjust-input"
                     id="manual_total"
                     value="${currentScore}"
                     min="0" max="${totalMaxMarks}"
                     step="1">
              <span style="margin-left: 4px;">/ ${totalMaxMarks}</span>
            </span>
          </div>
        `;
        const totalInput = document.getElementById('manual_total') as HTMLInputElement;
        if (totalInput) {
          totalInput.addEventListener('input', () => {
            const manualScoreEl = document.getElementById('manualScore') as HTMLInputElement;
            if (manualScoreEl) manualScoreEl.value = totalInput.value;
          });
        }
      }
    }
    
    // Update AI Feedback - IMPROVED VERSION
    const feedbackSection = document.querySelector('.feedback-section');
const feedbackContent = document.querySelector('.feedback-content');

if (feedbackContent && evaluation.feedback) {
    let feedbackHtml = '';
    
    // Display Strengths
    if (evaluation.feedback.strengths && evaluation.feedback.strengths.length > 0) {
        feedbackHtml += `
            <div class="strength-feedback" style="background: #d4edda; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <i class="fas fa-thumbs-up" style="color:#28a745; font-size: 1rem;"></i>
                    <strong style="color:#155724;">✅ Strengths</strong>
                </div>
                <ul style="margin: 0 0 0 20px; color: #155724; padding-left: 0;">
                    ${evaluation.feedback.strengths.map((s: string) => `<li style="margin: 4px 0; list-style: none;">✓ ${s.replace(/[✅👍]/g, '').trim()}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    // Display Improvements
    if (evaluation.feedback.improvements && evaluation.feedback.improvements.length > 0) {
        feedbackHtml += `
            <div class="improvement-feedback" style="background: #fff3cd; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <i class="fas fa-lightbulb" style="color:#856404; font-size: 1rem;"></i>
                    <strong style="color:#856404;">📚 Areas for Improvement</strong>
                </div>
                <ul style="margin: 0 0 0 20px; color: #856404; padding-left: 0;">
                    ${evaluation.feedback.improvements.map((i: string) => `<li style="margin: 4px 0; list-style: none;">⚠️ ${i.replace(/[📚🔑]/g, '').trim()}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    // Display Warnings
    if (evaluation.feedback.warnings && evaluation.feedback.warnings.length > 0) {
        feedbackHtml += `
            <div class="warning-feedback" style="background: #f8d7da; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <i class="fas fa-exclamation-triangle" style="color:#721c24; font-size: 1rem;"></i>
                    <strong style="color:#721c24;">⚠️ Warnings</strong>
                </div>
                <ul style="margin: 0 0 0 20px; color: #721c24; padding-left: 0;">
                    ${evaluation.feedback.warnings.map((w: string) => `<li style="margin: 4px 0; list-style: none;">! ${w.replace(/[⚠️]/gu, '').trim()}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    if (!feedbackHtml) {
        feedbackHtml = '<p class="text-muted" style="padding: 12px; color: #6c757d; margin: 0;">No additional feedback available</p>';
    }
    
    feedbackContent.innerHTML = feedbackHtml;
} else if (feedbackContent) {
    feedbackContent.innerHTML = '<p class="text-muted" style="padding: 12px; color: #6c757d; margin: 0;">No feedback available for this evaluation</p>';
}
    
    // Update Extracted Student Answer Preview (OCR text) — dynamic sections
    const extractedPreview = document.getElementById('extractedAnswerPreview');
    if (extractedPreview) {
      const sectionIconMap: Record<string, string> = {
        'Definition': 'fa-book-open', 'Body': 'fa-paragraph', 'Conclusion': 'fa-flag-checkered',
        'Given': 'fa-clipboard-list', 'Introduction': 'fa-book-open', 'Derivation': 'fa-calculator'
      };
      const sectionKeys = Object.keys(extracted).length > 0
        ? Object.keys(extracted)
        : (this.currentSectionNames.length > 0 ? this.currentSectionNames : ['Definition', 'Body', 'Conclusion']);

      extractedPreview.innerHTML = sectionKeys.map((key, idx) => {
        const text = extracted[key] || 'Not extracted';
        const icon = sectionIconMap[key] || 'fa-align-left';
        const mb = idx < sectionKeys.length - 1 ? 'margin-bottom: 15px;' : '';
        return `
          <div class="extracted-section" style="${mb}">
            <h5 style="color: var(--primary); margin-bottom: 8px;"><i class="fas ${icon}"></i> ${this.escapeHtml(key)}</h5>
            <p style="line-height: 1.5;">${this.escapeHtml(text)}</p>
          </div>`;
      }).join('');
    }

    // Phase 1.4: Show actual student answer sheet file
    const studentImagePanel = document.getElementById('studentImagePanel');
    if (studentImagePanel) {
      const answerSheetUrl = paper.studentAnswerSheetUrl || paper.studentImageUrl || '';
      const safeAnswerSheetUrl = this.escapeHtml(answerSheetUrl);
      const studentEmail = paper.studentEmail ? `<span style="font-size:0.85rem;color:#6c757d;">${this.escapeHtml(paper.studentEmail)}</span>` : '';

      if (answerSheetUrl) {
        if (paper.isStudentAnswerSheetPdf || answerSheetUrl.toLowerCase().includes('.pdf')) {
          studentImagePanel.innerHTML = `
            <div style="margin-bottom:8px;">${studentEmail}</div>
            <iframe src="${safeAnswerSheetUrl}" title="Student answer sheet PDF"
                    style="width:100%; min-height:500px; border:1px solid #dee2e6; border-radius:8px; background:#f8f9fa;"></iframe>
            <a href="${safeAnswerSheetUrl}" target="_blank" rel="noopener"
               style="display:inline-block;margin-top:8px;color:var(--primary);font-size:0.85rem;">Open PDF</a>
          `;
        } else {
          studentImagePanel.innerHTML = `
            <div style="margin-bottom:8px;">${studentEmail}</div>
            <img src="${safeAnswerSheetUrl}" alt="Student answer sheet"
                 style="width:100%; max-height:500px; object-fit:contain; border:1px solid #dee2e6; border-radius:8px; cursor:zoom-in;"
                 onclick="this.style.maxHeight = this.style.maxHeight === 'none' ? '500px' : 'none'"
                 onerror="this.parentElement.innerHTML='<p style=\\'color:#dc3545;padding:12px;\\'>Could not load image. File may have been moved.</p>'">
          `;
        }
      } else {
        studentImagePanel.innerHTML = `<p style="color:#6c757d;padding:12px;">No answer sheet available for this student.</p>`;
      }
    }
  }

  private toFileUrl(filePath: string): string {
    const normalizedPath = String(filePath || '').replace(/\\/g, '/').trim();

    if (!normalizedPath) {
      return '';
    }

    if (/^(https?:)?\/\//i.test(normalizedPath)) {
      return normalizedPath;
    }

    const backendBase = (environment.backendUrl || '').replace(/\/$/, '');
    const pathWithSlash = normalizedPath.startsWith('/') ? normalizedPath : `/${normalizedPath}`;
    return `${backendBase}${pathWithSlash}`;
  }

  private escapeHtml(text: string): string {
    if (!text) return '';
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  updateManualScore() {
    if (this.currentSectionNames.length === 0) return;
    const sections = this.currentSectionNames;
    let totalMarks = 0;
    let maxMarks = 0;

    sections.forEach(section => {
      const input = document.getElementById(`manual_${section}`) as HTMLInputElement;
      if (input) {
        totalMarks += parseFloat(input.value) || 0;
        maxMarks += parseFloat(input.max) || 0;
      }
    });
    
    const manualScoreEl = document.getElementById('manualScore') as HTMLInputElement;
    const manualMaxMarksEl = document.getElementById('manualMaxMarks');
    if (manualScoreEl) {
      manualScoreEl.value = totalMarks.toString();
    }
    if (manualMaxMarksEl) {
      manualMaxMarksEl.textContent = maxMarks.toString();
    }
  }

  previousPaper() {
    if (this.currentPaperIndex > 0) {
      this.currentPaperIndex--;
      this.loadCurrentPaperForCrossCheck();
    }
  }

  nextPaper() {
    if (this.currentPaperIndex < this.crossCheckPapers.length - 1) {
      this.currentPaperIndex++;
      this.loadCurrentPaperForCrossCheck();
    }
  }

  skipPaper() {
    this.currentPaperIndex++;
    this.loadCurrentPaperForCrossCheck();
  }

  approveEvaluation() {
    const paper = this.crossCheckPapers[this.currentPaperIndex];
    const resultId = paper?.resultId;

    if (resultId) {
      this.facultyService.updateEvaluationResult(resultId, {
        crossCheckCompleted: true,
        crossCheckNotes: 'AI evaluation approved without changes'
      }).subscribe({
        next: () => {
          this.toastService.show('success', 'Evaluation approved!');
          this.currentPaperIndex++;
          this.loadCurrentPaperForCrossCheck();
        },
        error: () => {
          // Still advance — don't block the faculty on a network error
          this.toastService.show('warn', 'Could not save approval — moving to next paper.');
          this.currentPaperIndex++;
          this.loadCurrentPaperForCrossCheck();
        }
      });
    } else {
      this.currentPaperIndex++;
      this.loadCurrentPaperForCrossCheck();
    }
  }

  saveAndContinue() {
    const paper = this.crossCheckPapers[this.currentPaperIndex];
    const resultId = paper?.resultId;

    const sections = this.currentSectionNames;
    const questionWiseMarks: any[] = [];
    let totalMarks = 0;

    sections.forEach((section, idx) => {
      const input = document.getElementById(`manual_${section}`) as HTMLInputElement;
      const sectionData = paper?.evaluation?.section_scores?.[section];
      if (input) {
        const marks = parseFloat(input.value) || 0;
        totalMarks += marks;
        questionWiseMarks.push({
          questionNumber: idx + 1,
          marksObtained: marks,
          maxMarks: parseFloat(input.max) || sectionData?.max_marks || 0,
          aiScore: sectionData?.marks_awarded ?? marks,
          remarks: section
        });
      }
    });

    if (resultId) {
      this.facultyService.updateEvaluationResult(resultId, {
        questionWiseMarks,
        crossCheckCompleted: true,
        crossCheckNotes: `Manual review: total ${totalMarks} marks`
      }).subscribe({
        next: () => {
          this.toastService.show('success', `Saved! New total: ${totalMarks} marks`);
          this.currentPaperIndex++;
          this.loadCurrentPaperForCrossCheck();
        },
        error: (err: any) => {
          this.toastService.show('error', err.error?.message || 'Failed to save adjustments.');
        }
      });
    } else {
      this.toastService.show('warn', 'No result ID — adjustments not saved to database.');
      this.currentPaperIndex++;
      this.loadCurrentPaperForCrossCheck();
    }
  }

  closeProgressModal() {
    this.showProgressModal = false;
    this.isSubmitting = false;
    this.evaluationLogs = [];
    if (this.progressInterval) {
      clearInterval(this.progressInterval);
      this.progressInterval = undefined;
    }
  }
  
  closeCrossCheckModal() { 
    this.showCrossCheckModal = false;
    this.crossCheckPapers = [];
    this.currentPaperIndex = 0;
    this.currentEvaluationData = null;
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/auth/login']);
  }
}
