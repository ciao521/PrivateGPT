document.addEventListener('DOMContentLoaded', function () {
    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-viewport');
            } else {
                entry.target.classList.remove('in-viewport'); // Optional: remove class if out of viewport
            }
        });
    });

    document.querySelectorAll('.fade-in').forEach(element => {
        observer.observe(element);
    });
});
