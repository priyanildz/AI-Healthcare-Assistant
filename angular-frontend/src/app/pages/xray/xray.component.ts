import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-xray',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './xray.component.html',
  styleUrl: './xray.component.css'
})
export class XrayComponent {
  isDragging = signal(false);
  isLoading = signal(false);
  analysisResult = signal<any>(null);

  constructor(private api: ApiService) { }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragging.set(true);
  }

  onDragLeave() {
    this.isDragging.set(false);
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragging.set(false);
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.analyzeImage(files[0]);
    }
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.analyzeImage(input.files[0]);
    }
  }

  analyzeImage(file: File) {
    this.isLoading.set(true);
    this.api.analyzeXray(file).subscribe({
      next: (result) => {
        this.analysisResult.set(result);
        this.isLoading.set(false);
      },
      error: (error) => {
        console.error('Error:', error);
        alert('Error analyzing image. Please try again.');
        this.isLoading.set(false);
      }
    });
  }

  getFormattedProbabilities() {
    const result = this.analysisResult();
    if (!result?.probabilities) return [];
    return Object.entries(result.probabilities).map(([key, value]: [string, any]) => ({
      label: key,
      value
    }));
  }

  resetAnalysis() {
    this.analysisResult.set(null);
  }
}

