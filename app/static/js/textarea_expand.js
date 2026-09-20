document.addEventListener(
  "input",
  function (event) {
    if (event.target.tagName.toLowerCase() !== "textarea") return;
    autoExpand(event.target);
  },
  false
);

document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM fully loaded and parsed");
  document.querySelectorAll("textarea").forEach(function (textarea) {
    console.log("Dispatching input event for textarea:", textarea);
    autoExpand(textarea);
  });
});

function autoExpand(field) {
  console.log("Auto-expanding textarea:", field);
  field.style.height = "inherit";
  const computed = window.getComputedStyle(field);
  const height =
    parseInt(computed.getPropertyValue("border-top-width"), 10) +
    parseInt(computed.getPropertyValue("padding-top"), 10) +
    field.scrollHeight +
    parseInt(computed.getPropertyValue("padding-bottom"), 10) +
    parseInt(computed.getPropertyValue("border-bottom-width"), 10);
  console.log(`Calculated height for textarea: ${height}px`);
  field.style.height = height + "px";
}
