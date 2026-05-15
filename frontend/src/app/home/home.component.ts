import { Component, ElementRef, OnInit, OnDestroy } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-home',
  imports: [RouterLink],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class HomeComponent implements OnInit, OnDestroy {
  private scrollHandler = () => {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 50) {
      navbar!.classList.add('scrolled');
    } else {
      navbar!.classList.remove('scrolled');
    }
  };

  private throttledScrollHandler = this.throttle(this.scrollHandler, 16); // ~60fps

  constructor() {}

  ngOnInit() {
    window.addEventListener('scroll', this.throttledScrollHandler, { passive: true });
  }

  ngOnDestroy() {
    window.removeEventListener('scroll', this.throttledScrollHandler);
  }

  private throttle(func: Function, limit: number) {
    let inThrottle: boolean;
    return function(this: any) {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    }
  }
}
