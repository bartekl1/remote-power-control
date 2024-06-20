const tooltipTriggerList = Array.from(document.querySelectorAll(['[data-bs-toggle="tooltip"]', ".toggle-tooltip"]));
tooltipTriggerList.forEach((tooltipTriggerEl) => {
    new bootstrap.Tooltip(tooltipTriggerEl);
});
