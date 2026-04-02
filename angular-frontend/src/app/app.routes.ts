import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home.component';
import { XrayComponent } from './pages/xray/xray.component';
import { ReportsComponent } from './pages/reports/reports.component';
import { MedicationsComponent } from './pages/medications/medications.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'xray', component: XrayComponent },
  { path: 'reports', component: ReportsComponent },
  { path: 'medications', component: MedicationsComponent },
  { path: '**', redirectTo: '' }
];
