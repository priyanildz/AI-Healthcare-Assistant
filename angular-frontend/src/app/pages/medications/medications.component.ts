import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-medications',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './medications.component.html',
  styleUrl: './medications.component.css'
})
export class MedicationsComponent {
  medicationName = '';
  reviewText = '';
  isLoading = signal(false);
  analysisResult = signal<any>(null);

  constructor(private api: ApiService) { }

  analyzeMedication() {
    if (!this.medicationName || !this.reviewText) return;
    this.isLoading.set(true);
    this.api.analyzeMedicationReview(this.reviewText, this.medicationName).subscribe({
      next: (result) => {
        this.analysisResult.set(result);
        this.isLoading.set(false);
      },
      error: (error) => {
        console.error('Error:', error);
        alert('Error analyzing review. Please try again.');
        this.isLoading.set(false);
      }
    });
  }

  getSentimentClass() {
    const sentiment = this.analysisResult()?.sentiment?.toLowerCase() || '';
    if (sentiment.includes('positive')) return 'positive';
    if (sentiment.includes('negative')) return 'negative';
    return 'neutral';
  }

  resetAnalysis() {
    this.analysisResult.set(null);
    this.medicationName = '';
    this.reviewText = '';
  }
}

