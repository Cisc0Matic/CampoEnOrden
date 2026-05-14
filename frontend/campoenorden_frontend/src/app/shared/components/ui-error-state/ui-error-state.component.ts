import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';

@Component({
  selector: 'ui-error-state',
  templateUrl: './ui-error-state.component.html',
  styleUrls: ['./ui-error-state.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule],
})
export class UiErrorStateComponent {
  @Input() message = 'Ha ocurrido un error';
  @Input() showRetry = true;
  @Output() retry = new EventEmitter<void>();
}
