import { Component, OnInit } from '@angular/core';
import { ApiService } from '../services/api.service';

@Component({
  selector: 'app-tab2',
  templateUrl: 'tab2.page.html',
  styleUrls: ['tab2.page.scss'],
  standalone: false,
})
export class Tab2Page implements OnInit {
  campos: any[] = [];

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadCampos();
  }

  loadCampos() {
    this.api.get<any[]>('core/campos/').subscribe({
      next: (data) => this.campos = data,
      error: () => this.campos = []
    });
  }
}