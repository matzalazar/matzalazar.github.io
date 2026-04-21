document.addEventListener('DOMContentLoaded', () => {
    // Reveal elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
            }
        });
    }, observerOptions);

    // Elements to animate
    const elementsToAnimate = document.querySelectorAll('section, .service-item, .about-section, .about-intro, .project-card, article');
    
    elementsToAnimate.forEach(el => {
        el.classList.add('reveal');
        observer.observe(el);
    });

    // Services carousel
    const track = document.querySelector('.carousel-track');
    if (track) {
        const slides = track.querySelectorAll('.carousel-slide');
        const dots = document.querySelectorAll('.carousel-dot');
        const prevBtn = document.querySelector('.carousel-prev');
        const nextBtn = document.querySelector('.carousel-next');
        let current = 0;

        // Fix track height to the tallest slide so controls don't jump
        const heights = Array.from(slides).map(slide => {
            const hidden = !slide.classList.contains('active');
            if (hidden) { slide.style.display = 'block'; slide.style.visibility = 'hidden'; }
            const h = slide.offsetHeight;
            if (hidden) { slide.style.display = ''; slide.style.visibility = ''; }
            return h;
        });
        track.style.minHeight = Math.max(...heights) + 'px';

        function goTo(index) {
            slides[current].classList.remove('active');
            dots[current].classList.remove('active');
            current = (index + slides.length) % slides.length;
            slides[current].classList.add('active');
            dots[current].classList.add('active');
        }

        prevBtn.addEventListener('click', () => goTo(current - 1));
        nextBtn.addEventListener('click', () => goTo(current + 1));
        dots.forEach((dot, i) => dot.addEventListener('click', () => goTo(i)));
    }

    // Smooth page transitions for links (optional, subtle fade out)
    const links = document.querySelectorAll('a:not([target="_blank"]):not([href^="mailto:"]):not([href^="#"])');
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href && !href.startsWith('#')) {
                e.preventDefault();
                document.body.classList.add('fade-out');
                setTimeout(() => {
                    window.location.href = href;
                }, 150);
            }
        });
    });
});
