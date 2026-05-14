import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';

@Component({
  selector: 'ui-empty-state',
  templateUrl: './ui-empty-state.component.html',
  styleUrls: ['./ui-empty-state.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule],
})
export class UiEmptyStateComponent {
  @Input() icon = 'leaf-outline';
  @Input() title = 'Sin datos';
  @Input() message = '';
  @Input() actionLabel = '';
  @Output() action = new EventEmitter<void>();
}
