import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';

@Component({
  selector: 'ui-header',
  templateUrl: './ui-header.component.html',
  styleUrls: ['./ui-header.component.scss'],
  standalone: true,
  imports: [CommonModule, IonicModule],
})
export class UiHeaderComponent {
  @Input() title = '';
  @Input() showAdd = true;
  @Input() addIcon = 'add-circle';
  @Output() add = new EventEmitter<void>();
}
