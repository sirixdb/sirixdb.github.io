(function() {
  'use strict';

  // Mobile nav toggle
  var menuToggle = document.getElementById('menu-toggle');
  var siteNav = document.getElementById('site-nav');

  if (menuToggle && siteNav) {
    menuToggle.addEventListener('click', function() {
      var isOpen = siteNav.classList.toggle('is-open');
      menuToggle.setAttribute('aria-expanded', isOpen);
    });
  }

  // Close mobile nav on link click
  if (siteNav) {
    siteNav.addEventListener('click', function(e) {
      if (e.target.tagName === 'A') {
        siteNav.classList.remove('is-open');
        if (menuToggle) menuToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // GUI showcase — auto-cycling slideshow
  var showcase = document.getElementById('gui-showcase');
  if (showcase) {
    var tabs = showcase.querySelectorAll('.gui-showcase__tab');
    var slides = showcase.querySelectorAll('.gui-showcase__slide');
    var captions = showcase.querySelectorAll('.gui-showcase__caption');
    var current = 0;
    var interval;

    function showSlide(i) {
      tabs.forEach(function(t) { t.classList.remove('active'); });
      slides.forEach(function(s) { s.classList.remove('active'); });
      captions.forEach(function(c) { c.classList.remove('active'); });
      tabs[i].classList.add('active');
      slides[i].classList.add('active');
      captions[i].classList.add('active');
      current = i;
    }

    function nextSlide() { showSlide((current + 1) % slides.length); }

    function startCycle() { interval = setInterval(nextSlide, 5000); }
    startCycle();

    tabs.forEach(function(tab, i) {
      tab.addEventListener('click', function() {
        clearInterval(interval);
        showSlide(i);
        startCycle();
      });
    });

    showcase.addEventListener('mouseenter', function() { clearInterval(interval); });
    showcase.addEventListener('mouseleave', startCycle);
  }

  // Query showcase tabs
  var queryShowcase = document.getElementById('query-showcase');
  if (queryShowcase) {
    var qTabs = queryShowcase.querySelectorAll('.query-showcase__tab');
    var qPanels = queryShowcase.querySelectorAll('.query-showcase__panel');
    qTabs.forEach(function(tab, i) {
      tab.addEventListener('click', function() {
        qTabs.forEach(function(t) { t.classList.remove('active'); });
        qPanels.forEach(function(p) { p.classList.remove('active'); });
        tab.classList.add('active');
        qPanels[i].classList.add('active');
      });
    });
  }

  // Auto-scroll terminal during animation
  var termBody = document.querySelector('.terminal__body');
  if (termBody) {
    termBody.querySelectorAll('.t-block').forEach(function(block) {
      block.addEventListener('animationstart', function() {
        termBody.scrollTo({ top: block.offsetTop - 16, behavior: 'smooth' });
      });
    });
  }

  // Fade-in on scroll
  var fadeEls = document.querySelectorAll('.fade-in');
  if (fadeEls.length && 'IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    fadeEls.forEach(function(el) { observer.observe(el); });
  } else {
    // Fallback: show everything immediately
    fadeEls.forEach(function(el) { el.classList.add('is-visible'); });
  }
})();
