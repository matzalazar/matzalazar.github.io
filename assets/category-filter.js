// Category filter functionality
document.addEventListener('DOMContentLoaded', function() {
  const categoryLinks = document.querySelectorAll('.category-link');
  const categorySections = document.querySelectorAll('.category-section');
  const seriesSection = document.querySelector('.series-section');
  
  categoryLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      
      // Remove active class from all links
      categoryLinks.forEach(l => l.classList.remove('active'));
      
      // Add active class to clicked link
      this.classList.add('active');
      
      // Use data-category attribute instead of text content
      const selectedCategory = this.getAttribute('data-category');
      
      if (selectedCategory === 'series') {
        // Mostrar solo la sección de series
        categorySections.forEach(section => {
          if (section.classList.contains('series-section')) {
            section.style.display = 'block';
          } else {
            section.style.display = 'none';
          }
        });
      } else if (selectedCategory === 'todas') {
        // Mostrar todas las categorías normales, ocultar series
        categorySections.forEach(section => {
          if (section.classList.contains('series-section')) {
            section.style.display = 'none';
          } else {
            section.style.display = 'block';
          }
        });
      } else {
        // Mostrar solo la categoría seleccionada
        categorySections.forEach(section => {
          const sectionCategory = section.getAttribute('data-category');
          if (section.classList.contains('series-section')) {
            section.style.display = 'none';
          } else {
            section.style.display = sectionCategory === selectedCategory ? 'block' : 'none';
          }
        });
      }
    });
  });
});
