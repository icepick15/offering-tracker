document.addEventListener("DOMContentLoaded", () => {
    const hamburger = document.querySelector(".hamburger");
    const sidebar = document.querySelector(".sidebar");

    // Toggle the sidebar on hamburger click
    hamburger.addEventListener("click", () => {
        sidebar.classList.toggle("open");
    });
});
