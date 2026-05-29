import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-page-not-exist',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './page-not-exist.component.html',
  styleUrls: ['./page-not-exist.component.css'],
})
export class PageNotExistComponent {
}
