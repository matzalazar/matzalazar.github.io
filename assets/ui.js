document.addEventListener('DOMContentLoaded', () => {
    const menu = document.querySelector('.menu');
    const menuToggle = document.querySelector('.menu-toggle');
    const menuLinks = document.querySelector('.menu-links');

    if (menu && menuToggle && menuLinks) {
        const closeMenu = () => {
            menu.classList.remove('is-open');
            menuToggle.setAttribute('aria-expanded', 'false');
            menuToggle.setAttribute('aria-label', 'Abrir menú');
        };

        const toggleMenu = () => {
            const isOpen = menu.classList.toggle('is-open');
            menuToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            menuToggle.setAttribute('aria-label', isOpen ? 'Cerrar menú' : 'Abrir menú');
        };

        menu.classList.add('is-collapsible');
        closeMenu();

        menuToggle.addEventListener('click', toggleMenu);

        menuLinks.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', closeMenu);
        });

        window.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                closeMenu();
            }
        });

        if (typeof window.matchMedia === 'function') {
            const desktopBreakpoint = window.matchMedia('(min-width: 641px)');
            const handleBreakpointChange = (event) => {
                if (event.matches) {
                    closeMenu();
                }
            };

            if (typeof desktopBreakpoint.addEventListener === 'function') {
                desktopBreakpoint.addEventListener('change', handleBreakpointChange);
            } else if (typeof desktopBreakpoint.addListener === 'function') {
                desktopBreakpoint.addListener(handleBreakpointChange);
            }
        }
    }

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
