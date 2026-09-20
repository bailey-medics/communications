document.addEventListener("DOMContentLoaded", function () {
  const dropArea = document.getElementById("drop-area");
  const fileInput = document.getElementById("image");
  const imagePreview = document.getElementById("image-preview");

  // Prevent default drag behaviors
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });

  // Highlight drop area when item is dragged over it
  ["dragenter", "dragover"].forEach((eventName) => {
    dropArea.addEventListener(eventName, highlight, false);
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropArea.addEventListener(eventName, unhighlight, false);
  });

  // Handle dropped files
  dropArea.addEventListener("drop", handleDrop, false);

  // Handle click to select files
  dropArea.addEventListener("click", () => fileInput.click());

  // Handle file selection
  fileInput.addEventListener("change", handleFiles, false);

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  function highlight() {
    dropArea.classList.add("highlight");
  }

  function unhighlight() {
    dropArea.classList.remove("highlight");
  }

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles({ target: { files } });
  }

  function handleFiles(e) {
    const files = e.target.files;
    if (files.length) {
      fileInput.files = files; // Update the file input with the selected files
      const file = files[0];
      const fileName = file.name;
      dropArea.querySelector("p").textContent = `Selected file: ${fileName}`;
      previewFile(file);
    }
  }

  function previewFile(file) {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onloadend = function () {
      imagePreview.src = reader.result;
      imagePreview.style.display = "block";
    };
  }
});
