import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';

@Component({
  selector: 'ui-loading-state',
  templateUrl: './ui-loading-state.component.html',
  styleUrls: ['./ui-loading-state.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule],
})
export class UiLoadingStateComponent {
  @Input() message = 'Cargando...';
}
