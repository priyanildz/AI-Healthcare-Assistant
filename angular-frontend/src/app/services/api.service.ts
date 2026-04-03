import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
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
    formData.append('image', file);
    return this.http.post<any>(`${this.baseUrl}/xrays/analyze`, formData).pipe(
      map((response) => response?.data ?? response)
    );
  }

  // Medical Reports
  analyzeReport(text: string, reportType: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/reports/summarize`, {
      report_text: text,
      report_type: reportType
    }).pipe(
      map((response) => response?.data ?? response)
    );
  }

  // Medication Reviews
  analyzeMedicationReview(reviewText: string, medicationName: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/medications/analyze-review`, {
      review_text: reviewText,
      medication_name: medicationName
    }).pipe(
      map((response) => response?.data ?? response)
    );
  }

  // Health Check
  healthCheck(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl.replace('/api', '')}/health`).pipe(
      map((response) => response?.data ?? response)
    );
  }
}
