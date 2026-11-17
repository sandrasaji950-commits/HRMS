/* Smart HRMS Core JavaScript */

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Sidebar Toggling Logic
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');

    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.setAttribute(
            'aria-expanded',
            String(window.innerWidth >= 768 && !sidebar.classList.contains('collapsed'))
        );
    }

    function closeMobileSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove('show');
        if (sidebarBackdrop) sidebarBackdrop.classList.remove('show');
        if (sidebarToggleBtn) sidebarToggleBtn.setAttribute('aria-expanded', 'false');
    }

    window.addEventListener('resize', function() {
        if (!sidebar || !sidebarToggleBtn) return;

        const isMobile = window.innerWidth < 768;
        if (!isMobile) {
            sidebar.classList.remove('show');
            if (sidebarBackdrop) sidebarBackdrop.classList.remove('show');
        }

        sidebarToggleBtn.setAttribute(
            'aria-expanded',
            String(isMobile ? sidebar.classList.contains('show') : !sidebar.classList.contains('collapsed'))
        );
    });

    if (sidebarToggleBtn && sidebar && mainContent) {
        sidebarToggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (window.innerWidth >= 768) {
                // Collapsing on Desktop
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('expanded');
                sidebarToggleBtn.setAttribute('aria-expanded', String(!sidebar.classList.contains('collapsed')));
            } else {
                // Showing/Hiding overlay drawer on Mobile
                sidebar.classList.toggle('show');
                const isOpen = sidebar.classList.contains('show');
                if (sidebarBackdrop) sidebarBackdrop.classList.toggle('show', isOpen);
                sidebarToggleBtn.setAttribute('aria-expanded', String(isOpen));
            }
        });
    }

    if (sidebarCloseBtn && sidebar) {
        sidebarCloseBtn.addEventListener('click', function(e) {
            e.preventDefault();
            closeMobileSidebar();
        });
    }

    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener('click', closeMobileSidebar);
    }

    // Close mobile sidebar if clicking outside of it
    document.addEventListener('click', function(event) {
        const isClickInsideSidebar = sidebar && sidebar.contains(event.target);
        const isClickOnToggle = sidebarToggleBtn && sidebarToggleBtn.contains(event.target);
        
        if (window.innerWidth < 768 && sidebar && sidebar.classList.contains('show')) {
            if (!isClickInsideSidebar && !isClickOnToggle) {
                closeMobileSidebar();
            }
        }
    });

    // 2. Bootstrap HTML5 Form Validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // 3. Auto-hide Alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

});
