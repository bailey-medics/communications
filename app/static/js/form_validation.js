function validateForm() {
  const title = document.getElementById("title").value.trim();
  const longBlurb = document.getElementById("long_blurb").value.trim();
  const shortBlurb = document.getElementById("short_blurb").value.trim();

  if (!title) {
    alert("Title is required.");
    return false;
  }

  if (!longBlurb && !shortBlurb) {
    alert("Either Long Form Blurb or Short Form Blurb must have text.");
    return false;
  }

  return true;
}
