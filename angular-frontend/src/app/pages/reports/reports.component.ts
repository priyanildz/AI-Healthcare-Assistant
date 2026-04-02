import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './reports.component.html',
  styleUrl: './reports.component.css'
})
export class ReportsComponent {
  reportType = '';
  reportText = '';
  isLoading = signal(false);
  analysisResult = signal<any>(null);

  constructor(private api: ApiService) { }

  analyzeReport() {
    if (!this.reportText || !this.reportType) return;
    this.isLoading.set(true);
    this.api.analyzeReport(this.reportText, this.reportType).subscribe({
      next: (result) => {
        this.analysisResult.set(result);
        this.isLoading.set(false);
      },
      error: (error) => {
        console.error('Error:', error);
        alert('Error analyzing report. Please try again.');
        this.isLoading.set(false);
      }
    });
  }

  resetAnalysis() {
    this.analysisResult.set(null);
    this.reportText = '';
    this.reportType = '';
  }
}

