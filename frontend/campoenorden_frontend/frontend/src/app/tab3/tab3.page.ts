import { Component, OnInit } from '@angular/core';
import { ApiService } from '../services/api.service';

@Component({
  selector: 'app-tab3',
  templateUrl: 'tab3.page.html',
  styleUrls: ['tab3.page.scss'],
  standalone: false,
})
export class Tab3Page implements OnInit {
  fletes: any[] = [];
  selectedSegment = 'fletes';

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadFletes();
  }

  loadFletes() {
    this.api.get<any[]>('logistica/').subscribe({
      next: (data) => this.fletes = data,
      error: () => this.fletes = []
    });
  }

  segmentChanged(event: any) {
    this.selectedSegment = event.detail.value;
  }
}