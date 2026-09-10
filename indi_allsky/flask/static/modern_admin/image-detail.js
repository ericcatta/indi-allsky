/* Display the saved image without changing its pixels or capture settings. */
(function () {
    "use strict";
    const image = document.getElementById("image-detail-preview");
    const status = document.getElementById("image-detail-preview-status");
    if (!image || !status) return;
    function loaded() {
        image.hidden = false;
        status.hidden = true;
        status.textContent = "";
    }
    function failed() {
        image.hidden = true;
        status.hidden = false;
        status.textContent = "Preview unavailable. The file may have been removed, access may be restricted, or the media server may be unreachable. Capture metadata is still available.";
    }
    image.addEventListener("load", loaded);
    image.addEventListener("error", failed);
    if (image.complete) {
        if (image.naturalWidth > 0) loaded();
        else failed();
    } else {
        status.hidden = false;
        status.textContent = "Loading image…";
    }
}());
