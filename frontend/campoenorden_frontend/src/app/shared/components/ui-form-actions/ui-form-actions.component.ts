import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';

@Component({
  selector: 'ui-form-actions',
  templateUrl: './ui-form-actions.component.html',
  styleUrls: ['./ui-form-actions.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule],
})
export class UiFormActionsComponent {
  @Input() submitLabel = 'Guardar';
  @Input() loading = false;
  @Input() disabled = false;
  @Output() submit = new EventEmitter<void>();
  @Output() cancel = new EventEmitter<void>();
}
