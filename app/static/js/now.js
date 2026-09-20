function setDateTimeNow() {
  const now = new Date();
  const date = now.toISOString().split("T")[0];
  const time = now.toTimeString().split(" ")[0].slice(0, 5);
  document.getElementById("post_date").value = date;
  document.getElementById("post_time").value = time;
}
