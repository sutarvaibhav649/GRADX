import { Component, OnDestroy, OnInit, AfterViewInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { UpperCasePipe, CommonModule } from '@angular/common';
import { AuthService } from '../../shared/services/auth.service';
import { FacultyService } from '../../shared/services/faculty.service';
import { ToastService } from '../../shared/toast.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-faculty-dashboard',
  imports: [ReactiveFormsModule, UpperCasePipe, CommonModule],
  templateUrl: './faculty-dashboard.component.html',
  styleUrl: './faculty-dashboard.component.css',
})
export class FacultyDashboardComponent implements OnInit, OnDestroy, AfterViewInit {
  finalizeS!: Subscription;

  uploadForm!: FormGroup;

  stats = { papersUploaded: 0, aiEvaluated: 0, manuallyEvaluated: 0, pendingEvaluation: 0 };
  recentExams: any[] = [];

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
  }

  ngOnInit() {
    this.loadDashboard();
  }

  ngAfterViewInit() {
    // Bind the method to window so it can be called from HTML
    (window as any).updateManualScoreFromComponent = () => {
      this.updateManualScore();
    };
  }

  loadDashboard() {
    this.uploadForm = this.fb.group({
      academicYear: ['', Validators.required],
      year: ['', Validators.required],
      department: ['', Validators.required],
      examType: ['', Validators.required],
      semester: ['', Validators.required],
      maxMarks: [{ value: '', disabled: true }],
      subject: ['', Validators.required],
      evaluationMode: ['ai'],
      enableCrossCheck: [true],
      evaluationStrictness: ['moderate']
    });
    this.facultyService.getDashboard().subscribe({
      next: (res) => {
        console.log('Dashboard data:', res);
        this.stats = res.data.stats;
        this.recentExams = res.data.recentExams;
        this.toastService.show('success', 'Dashboard data loaded successfully.');
      },
      error: (err: any) => {
        console.error('Error loading dashboard:', err);
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
    const examType = this.uploadForm.get('examType')?.value;
    const marks: Record<string, number> = { mse: 30, ese: 80, makeup: 80, quiz: 20 };
    this.uploadForm.patchValue({ maxMarks: marks[examType] ?? '' });
  }

  onStudentPapersChange(event: Event) {
    const input = event.target as HTMLInputElement;
    const files = Array.from(input.files || []);
    const newPapers = files.map((file) => ({ file, email: '' }));
    this.selectedStudentPapers = [...this.selectedStudentPapers, ...newPapers];
    input.value = '';
  }

  updateStudentPaperEmail(index: number, email: string) {
    if (index < 0 || index >= this.selectedStudentPapers.length) {
      return;
    }
    this.selectedStudentPapers[index].email = email;
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
      this.toastService.show('error', 'Please upload at least one student answer sheet image.');
      return;
    }
    if (this.selectedStudentPapers.some((paper) => !paper.email?.trim())) {
      this.toastService.show('error', 'Please enter the student email for each uploaded sheet.');
      return;
    }
    const invalidEmail = this.selectedStudentPapers.some((paper) => !/^\S+@\S+\.\S+$/.test(paper.email.trim()));
    if (invalidEmail) {
      this.toastService.show('error', 'Please enter a valid email address for each student.');
      return;
    }
    if (!this.selectedModelAnswer) {
      this.toastService.show('error', 'Please select the model answer image.');
      return;
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
    fd.append('modelAnswer', this.selectedModelAnswer);

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
        this.updateProgress(100, this.totalPapers, this.totalPapers);
        
        setTimeout(() => {
          this.isSubmitting = false;
          this.showProgressModal = false;
          
          const enableCrossCheck = this.uploadForm.get('enableCrossCheck')?.value;
          
          if (enableCrossCheck && evalRes.data?.results) {
            // Transform results to include extracted answers
            this.crossCheckPapers = evalRes.data.results.map((result: any) => {
              const extractedAnswer = result.extractedAnswer || {};
              const aiDetails = result.aiEvaluationDetails || {};
              
              return {
                success: true,
                student_extracted: {
                  Answer: {
                    Definition: extractedAnswer.Definition || aiDetails.student_text?.Definition || 'Not extracted',
                    Body: extractedAnswer.Body || aiDetails.student_text?.Body || 'Not extracted',
                    Conclusion: extractedAnswer.Conclusion || aiDetails.student_text?.Conclusion || 'Not extracted'
                  }
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
            
            console.log('Cross-check papers with extracted data:', this.crossCheckPapers);
            
            this.currentPaperTotal = this.crossCheckPapers.length;
            this.currentPaperIndex = 0;
            this.showCrossCheckModal = true;
            this.loadCurrentPaperForCrossCheck();
          } else if (enableCrossCheck) {
            this.loadMockEvaluationData();
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

  private loadMockEvaluationData() {
    const mockEvaluation = {
      success: true,
      student_extracted: {
        question_No: "1",
        Answer: {
          Definition: "Deep Learning is a type of Machine Learning with multiple layers",
          Body: "It has input, hidden, and output layers. The network learns features from data automatically.",
          Conclusion: "Used in image recognition and language processing."
        }
      },
      evaluation: {
        total_marks: 3,
        max_marks: 7,
        percentage: 42.9,
        section_scores: {
          Definition: {
            marks_awarded: 1,
            max_marks: 2,
            percentage: 50.0,
            scores: { semantic_similarity: 0.689, coherence: 1.0, concept_coverage: 0.667, depth_score: 0.777 },
            cheating_detection: { is_suspicious: false, keyword_density: 0.3 }
          },
          Body: {
            marks_awarded: 1,
            max_marks: 3,
            percentage: 33.3,
            scores: { semantic_similarity: 0.6, coherence: 0.8, concept_coverage: 0.0, depth_score: 0.639 },
            cheating_detection: { is_suspicious: false, keyword_density: 0.0 }
          },
          Conclusion: {
            marks_awarded: 1,
            max_marks: 2,
            percentage: 50.0,
            scores: { semantic_similarity: 0.383, coherence: 1.0, concept_coverage: 0.2, depth_score: 0.527 },
            cheating_detection: { is_suspicious: false, keyword_density: 0.143 }
          }
        },
        feedback: {
          strengths: ["👍 Definition: Good understanding", "👍 Conclusion: Good understanding"],
          improvements: ["📚 Body: Needs improvement", "🔑 Body: Missing key concepts", "🔑 Conclusion: Missing key concepts"],
          warnings: []
        },
        config_used: "Extracted Model Answer"
      },
      saved_to_json: "evaluation_20260515_210655.json"
    };
    
    this.crossCheckPapers = [mockEvaluation];
    this.currentPaperTotal = this.crossCheckPapers.length;
    this.currentPaperIndex = 0;
    this.showCrossCheckModal = true;
    this.loadCurrentPaperForCrossCheck();
  }

  private simulateProgress() {
    let progress = 0;
    const interval = setInterval(() => {
      if (progress < 100 && this.showProgressModal) {
        progress += 10;
        this.progressPercentage = progress;
        this.processedPapers = Math.floor((progress / 100) * this.totalPapers);
        if (progress % 20 === 0) {
          this.addLogMessage(`Processing papers... ${progress}% complete`, 'info');
        }
      } else {
        clearInterval(interval);
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
      subject: ''
    });
    this.uploadForm.get('maxMarks')?.disable();
    this.selectedStudentPapers = [];
    this.selectedModelAnswer = null;
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
    
    console.log('Updating modal with:', { evaluation, extracted });
    
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
    
    // Update Section-wise AI Marks
    const aiQuestionMarks = document.getElementById('aiQuestionMarks');
    if (aiQuestionMarks && evaluation.section_scores) {
      aiQuestionMarks.innerHTML = '';
      const sections = ['Definition', 'Body', 'Conclusion'];
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
              <small style="font-size:0.7rem; color:#6c757d; margin-left:8px;">
                (${semanticScore}% match)
              </small>
            </span>
          `;
          aiQuestionMarks.appendChild(div);
        }
      });
    }
    
    // Update Manual Adjustment Inputs
    const manualQuestionMarks = document.getElementById('manualQuestionMarks');
    if (manualQuestionMarks && evaluation.section_scores) {
      manualQuestionMarks.innerHTML = '';
      const sections = ['Definition', 'Body', 'Conclusion'];
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
      
      // Add event listeners
      sections.forEach(section => {
        const input = document.getElementById(`manual_${section}`) as HTMLInputElement;
        if (input) {
          input.addEventListener('input', () => this.updateManualScore());
        }
      });
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
                    ${evaluation.feedback.warnings.map((w: string) => `<li style="margin: 4px 0; list-style: none;">! ${w}</li>`).join('')}
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
    
    // Update Extracted Student Answer Preview
    const extractedPreview = document.getElementById('extractedAnswerPreview');
    if (extractedPreview) {
      const definitionText = extracted.Definition || extracted.definition || 'Not extracted';
      const bodyText = extracted.Body || extracted.body || 'Not extracted';
      const conclusionText = extracted.Conclusion || extracted.conclusion || 'Not extracted';
      
      extractedPreview.innerHTML = `
        <div class="extracted-section" style="margin-bottom: 15px;">
          <h5 style="color: var(--primary); margin-bottom: 8px;"><i class="fas fa-book-open"></i> Definition</h5>
          <p style="line-height: 1.5;">${this.escapeHtml(definitionText)}</p>
        </div>
        <div class="extracted-section" style="margin-bottom: 15px;">
          <h5 style="color: var(--primary); margin-bottom: 8px;"><i class="fas fa-paragraph"></i> Body</h5>
          <p style="line-height: 1.5;">${this.escapeHtml(bodyText)}</p>
        </div>
        <div class="extracted-section">
          <h5 style="color: var(--primary); margin-bottom: 8px;"><i class="fas fa-flag-checkered"></i> Conclusion</h5>
          <p style="line-height: 1.5;">${this.escapeHtml(conclusionText)}</p>
        </div>
      `;
    }
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
    const sections = ['Definition', 'Body', 'Conclusion'];
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
    // Save approved evaluation
    this.currentPaperIndex++;
    this.loadCurrentPaperForCrossCheck();
  }

  saveAndContinue() {
    const sections = ['Definition', 'Body', 'Conclusion'];
    let totalMarks = 0;
    const adjustments: any = {};
    
    sections.forEach(section => {
      const input = document.getElementById(`manual_${section}`) as HTMLInputElement;
      if (input) {
        adjustments[section] = parseFloat(input.value);
        totalMarks += adjustments[section];
      }
    });
    
    console.log('Saving adjustments:', adjustments, 'Total:', totalMarks);
    this.toastService.show('success', `Adjustments saved! New total: ${totalMarks} marks`);
    
    this.currentPaperIndex++;
    this.loadCurrentPaperForCrossCheck();
  }

  closeProgressModal() { 
    this.showProgressModal = false;
    this.evaluationLogs = [];
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