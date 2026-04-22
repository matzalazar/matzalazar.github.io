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

    // Services refined tabs / carousel
    const refinedServices = document.querySelector('.services-refined');
    if (refinedServices) {
        const tabs = Array.from(refinedServices.querySelectorAll('.services-refined-tab'));
        const slides = Array.from(refinedServices.querySelectorAll('.service-panel-slide'));
        const refinedStage = refinedServices.querySelector('.services-refined-stage');
        const refinedTrack = refinedServices.querySelector('.services-refined-track');
        let current = Array.from(tabs).findIndex(tab => tab.classList.contains('is-active'));
        if (current < 0) current = 0;

        function setActiveTab(index) {
            tabs.forEach((tab, tabIndex) => {
                const isActive = tabIndex === index;
                tab.classList.toggle('is-active', isActive);
                tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
                tab.setAttribute('tabindex', isActive ? '0' : '-1');
            });
        }

        function setStageHeight(index) {
            if (refinedStage && slides[index]) {
                refinedStage.style.height = `${slides[index].offsetHeight}px`;
            }
        }

        function goTo(index) {
            if (!tabs.length || !slides.length || !refinedTrack || !refinedStage) return;

            const nextIndex = (index + slides.length) % slides.length;
            if (nextIndex === current) return;

            setActiveTab(nextIndex);
            slides.forEach((slide, slideIndex) => {
                const isActive = slideIndex === nextIndex;
                slide.classList.toggle('is-active', isActive);
                slide.setAttribute('aria-hidden', isActive ? 'false' : 'true');
            });
            refinedTrack.style.transform = `translateX(-${nextIndex * 100}%)`;
            setStageHeight(nextIndex);
            current = nextIndex;
        }

        setActiveTab(current);
        slides.forEach((slide, slideIndex) => {
            const isActive = slideIndex === current;
            slide.classList.toggle('is-active', isActive);
            slide.setAttribute('aria-hidden', isActive ? 'false' : 'true');
        });
        refinedTrack.style.transition = 'none';
        refinedStage.style.transition = 'none';
        refinedTrack.style.transform = `translateX(-${current * 100}%)`;
        setStageHeight(current);
        requestAnimationFrame(() => {
            refinedTrack.style.transition = '';
            refinedStage.style.transition = '';
        });

        tabs.forEach((tab, index) => {
            tab.setAttribute('tabindex', index === current ? '0' : '-1');
            tab.addEventListener('click', () => goTo(index));
            tab.addEventListener('keydown', (event) => {
                if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
                    event.preventDefault();
                    goTo(index + 1);
                    tabs[(index + 1) % tabs.length].focus();
                }

                if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
                    event.preventDefault();
                    goTo(index - 1);
                    tabs[(index - 1 + tabs.length) % tabs.length].focus();
                }

                if (event.key === 'Home') {
                    event.preventDefault();
                    goTo(0);
                    tabs[0].focus();
                }

                if (event.key === 'End') {
                    event.preventDefault();
                    const lastIndex = tabs.length - 1;
                    goTo(lastIndex);
                    tabs[lastIndex].focus();
                }
            });
        });

        if (typeof ResizeObserver !== 'undefined') {
            const resizeObserver = new ResizeObserver(() => {
                setStageHeight(current);
            });
            slides.forEach(slide => resizeObserver.observe(slide));
        } else {
            window.addEventListener('resize', () => {
                setStageHeight(current);
            });
        }

        window.addEventListener('load', () => {
            setStageHeight(current);
        });
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
