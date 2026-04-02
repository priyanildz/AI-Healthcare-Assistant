import { Injectable } from '@angular/core';
import { signal } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private darkMode = signal(this.loadTheme());

  constructor() {
    this.applyTheme();
  }

  isDarkMode() {
    return this.darkMode;
  }

  toggleTheme() {
    this.darkMode.set(!this.darkMode());
    this.saveTheme();
    this.applyTheme();
  }

  private loadTheme(): boolean {
    const saved = localStorage.getItem('theme');
    if (saved !== null) {
      return saved === 'dark';
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  private saveTheme() {
    localStorage.setItem('theme', this.darkMode() ? 'dark' : 'light');
  }

  private applyTheme() {
    const isDark = this.darkMode();
    if (isDark) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.setAttribute('data-theme', 'light');
    }
  }
}
