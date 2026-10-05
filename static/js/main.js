document.addEventListener('DOMContentLoaded', () => {
    // Sidebar toggle for mobile
    const openSidebarBtn = document.getElementById('openSidebar');
    const closeSidebarBtn = document.getElementById('closeSidebar');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (openSidebarBtn && sidebar && overlay) {
        openSidebarBtn.addEventListener('click', () => {
            sidebar.classList.add('open');
            overlay.classList.add('active');
        });
        
        const closeSidebar = () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        };
        
        if (closeSidebarBtn) {
            closeSidebarBtn.addEventListener('click', closeSidebar);
        }
        
        overlay.addEventListener('click', closeSidebar);
    }

    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(msg => {
                msg.style.opacity = '0';
                msg.style.transition = 'opacity 0.5s ease';
                setTimeout(() => msg.remove(), 500);
            });
        }, 5000);
    }
});
