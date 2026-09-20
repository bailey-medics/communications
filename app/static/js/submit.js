function submitFunc(event) {
  // Prevent the default form submission
  event.preventDefault();

  // Disable the form elements
  document.querySelectorAll(".form-group, button").forEach((element) => {
    element.style.opacity = "0.5";
    element.disabled = true;
  });

  // Show the spinner
  document.getElementById("spinner").classList.remove("d-none");

  // Submit the form
  document.getElementById("form").submit();
}

document.addEventListener("keydown", function (event) {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    event.preventDefault();
    submitFunc(event);
  }
});

// Reset the form layout when the page is shown (including when navigating back)
window.addEventListener("pageshow", function (event) {
  if (
    event.persisted ||
    (window.performance && window.performance.navigation.type === 2)
  ) {
    // Enable the form elements
    document.querySelectorAll(".form-group, button").forEach((element) => {
      element.style.opacity = "1";
      element.disabled = false;
    });

    // Hide the spinner
    document.getElementById("spinner").classList.add("d-none");
  }
});
