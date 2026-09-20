const dropdownContainer = document.getElementById(
  "multiselectDropdownContainer"
);
const dropdownButton = document.getElementById(
  "multiselectDropdownContainerButton"
);
const dropdownMenu = dropdownContainer.querySelector(".dropdown-menu");
const hiddenInputsContainer = document.getElementById(
  "multiselectDropdownContainerHiddenInputsContainer"
);

// Update the button text based on selected options
function updateButtonText() {
  const selectedOptions = [];
  const selectedValues = [];
  const selectedItems = dropdownMenu.querySelectorAll(
    ".dropdown-item.selected"
  );
  selectedItems.forEach((item) => {
    selectedOptions.push(item.textContent.trim());
    selectedValues.push(item.getAttribute("data-value"));
  });
  if (selectedOptions.length > 0) {
    dropdownButton.textContent = selectedOptions.join(" ");
  } else {
    dropdownButton.textContent = "Select Options";
  }
  dropdownButton.classList.remove("d-none");

  // Update hidden input fields
  hiddenInputsContainer.innerHTML = ""; // Clear existing inputs
  let clients = [];
  selectedValues.forEach((value) => {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "selected_clients[]";
    input.value = value;
    clients.push(value);
    hiddenInputsContainer.appendChild(input);
  });
}

// Run updateButtonText on page load
document.addEventListener("DOMContentLoaded", function () {
  updateButtonText();
});

// Toggle dropdown manually on button click
dropdownButton.addEventListener("click", function (e) {
  e.preventDefault(); // Prevent Bootstrap's default toggle behavior
  dropdownMenu.classList.toggle("show");
});

// Prevent dropdown from closing when clicking inside it
dropdownMenu.addEventListener("click", function (e) {
  e.stopPropagation();
});

// Close dropdown and update button text when clicking outside
document.addEventListener("click", function (e) {
  if (!dropdownContainer.contains(e.target)) {
    dropdownMenu.classList.remove("show");
    updateButtonText();
  }
});

// Make entire row clickable for selecting/deselecting options
const dropdownItems = dropdownMenu.querySelectorAll(".dropdown-item");
dropdownItems.forEach((item) => {
  item.addEventListener("click", function (e) {
    item.classList.toggle("selected");
    updateButtonText();
  });
});
