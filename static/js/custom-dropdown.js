document.addEventListener('DOMContentLoaded', function () {
    const submenus = document.querySelectorAll('.dropdown-submenu');

    submenus.forEach(function (submenu) {
        const toggle = submenu.querySelector('.dropdown-toggle');
        const menu = submenu.querySelector('.dropdown-menu');

        toggle.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            const isVisible = menu.classList.contains('show');
            menu.classList.toggle('show', !isVisible);
        });
    });
});
