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

  // SVG lightbox
  var overlay = document.createElement('div');
  overlay.className = 'svg-lightbox';
  overlay.innerHTML = '<button class="svg-lightbox__close" aria-label="Close"><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M15 5L5 15M5 5l10 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg></button>';
  document.body.appendChild(overlay);

  function closeLightbox() {
    overlay.classList.remove('is-open');
    var content = overlay.querySelector('.svg-lightbox__content');
    if (content) content.remove();
  }

  overlay.querySelector('.svg-lightbox__close').addEventListener('click', closeLightbox);
  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) closeLightbox();
  });
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeLightbox();
  });

  var expandSvg = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 10v4h4M14 6V2h-4M2 6V2h4M14 10v4h-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  document.querySelectorAll('.docs-content svg[role="img"], .docs-content img[src$=".svg"]').forEach(function(el) {
    // Wrap diagram in a frame for visual prominence
    var frame = document.createElement('div');
    frame.className = 'diagram-frame';
    el.parentNode.insertBefore(frame, el);
    frame.appendChild(el);
    el.removeAttribute('style');

    // Add expand indicator
    var expandBtn = document.createElement('div');
    expandBtn.className = 'diagram-frame__expand';
    expandBtn.innerHTML = expandSvg;
    frame.appendChild(expandBtn);

    frame.addEventListener('click', function() {
      var old = overlay.querySelector('.svg-lightbox__content');
      if (old) old.remove();
      var clone;
      if (el.tagName === 'IMG') {
        clone = document.createElement('img');
        clone.src = el.src;
        clone.alt = el.alt;
      } else {
        clone = el.cloneNode(true);
      }
      clone.setAttribute('class', 'svg-lightbox__content');
      overlay.appendChild(clone);
      overlay.classList.add('is-open');
    });
  });

  // Copy-to-clipboard buttons on code blocks
  document.querySelectorAll('.code-block, div.highlighter-rouge').forEach(function(block) {
    var btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.textContent = 'Copy';
    btn.addEventListener('click', function() {
      var pre = block.querySelector('pre');
      if (!pre) return;
      navigator.clipboard.writeText(pre.textContent).then(function() {
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(function() {
          btn.textContent = 'Copy';
          btn.classList.remove('copied');
        }, 1500);
      });
    });
    block.appendChild(btn);
  });

  // Contact form (EmailJS + reCAPTCHA v3)
  var contactForm = document.getElementById('contact-form');
  if (contactForm) {
    var EMAILJS_PUBLIC_KEY = 'sJmjKtQGEPQ_pnBIe';
    var EMAILJS_SERVICE_ID = 'service_8rpifo9';
    var EMAILJS_TEMPLATE_ID = 'template_icja3qf';
    var RECAPTCHA_SITE_KEY = '6Lcws2QsAAAAABlMD58ymDrr0G3OoOU1oVwdhFD9';

    emailjs.init(EMAILJS_PUBLIC_KEY);

    contactForm.addEventListener('submit', function(e) {
      e.preventDefault();

      // Honeypot check
      if (contactForm.querySelector('[name="website"]').value) return;

      var btn = document.getElementById('contact-submit');
      var status = document.getElementById('form-status');
      btn.disabled = true;
      btn.textContent = 'Sending...';
      status.className = 'contact-form__status';
      status.textContent = '';

      grecaptcha.ready(function() {
        grecaptcha.execute(RECAPTCHA_SITE_KEY, { action: 'contact' }).then(function(token) {
          document.getElementById('g-recaptcha-response').value = token;
          emailjs.sendForm(EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID, contactForm, EMAILJS_PUBLIC_KEY).then(
            function() {
              status.textContent = 'Message sent! We will get back to you soon.';
              status.className = 'contact-form__status contact-form__status--success';
              contactForm.reset();
              btn.disabled = false;
              btn.textContent = 'Send Message';
            },
            function(err) {
              console.error('EmailJS error:', err);
              status.textContent = 'Something went wrong (' + (err.text || err) + '). Please try again or email us directly.';
              status.className = 'contact-form__status contact-form__status--error';
              btn.disabled = false;
              btn.textContent = 'Send Message';
            }
          );
        });
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
