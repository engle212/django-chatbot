document.getElementById("newConvo").addEventListener("click", function(e) {
  var url = $("#newConvo").attr("data-url");
  window.location.replace(url);
});