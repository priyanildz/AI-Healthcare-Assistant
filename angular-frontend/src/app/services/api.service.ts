import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) { }

  // X-ray Analysis
  analyzeXray(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.baseUrl}/xrays/analyze`, formData);
  }

  // Medical Reports
  analyzeReport(text: string, reportType: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/reports/summarize-file`, {
      text,
      report_type: reportType
    });
  }

  // Medication Reviews
  analyzeMedicationReview(reviewText: string, medicationName: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/medications/analyze-review`, {
      review_text: reviewText,
      medication_name: medicationName
    });
  }

  // Health Check
  healthCheck(): Observable<any> {
    return this.http.get(`${this.baseUrl.replace('/api', '')}/health`);
  }
}
