import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';

type CardColor = 'primary' | 'secondary' | 'tertiary' | 'success' | 'warning' | 'danger' | 'medium';

@Component({
  selector: 'ui-card',
  templateUrl: './ui-card.component.html',
  styleUrls: ['./ui-card.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule],
})
export class UiCardComponent {
  @Input() color: CardColor = 'primary';
}
