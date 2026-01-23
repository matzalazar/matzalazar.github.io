// Category filter functionality
document.addEventListener('DOMContentLoaded', function() {
  const categoryLinks = document.querySelectorAll('.category-link');
  const categorySections = document.querySelectorAll('.category-section');
  
  categoryLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      
      // Remove active class from all links
      categoryLinks.forEach(l => l.classList.remove('active'));
      
      // Add active class to clicked link
      this.classList.add('active');
      
      // Use data-category attribute instead of text content
      const selectedCategory = this.getAttribute('data-category');
      
      // Show/hide sections based on selection
      categorySections.forEach(section => {
        if (selectedCategory === 'todas') {
          section.style.display = 'block';
        } else {
          const sectionCategory = section.getAttribute('data-category');
          section.style.display = sectionCategory === selectedCategory ? 'block' : 'none';
        }
      });
    });
  });
});
