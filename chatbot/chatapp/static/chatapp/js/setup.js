document.getElementById("newConvo").addEventListener("click", function(e) {
  var url = $("#newConvo").attr("data-url");
  window.location.replace(url);
});

convoButtons = document.getElementsByClassName("convo");

for (var i = 0; i < convoButtons.length; i++) {
  convoButtons.item(i).addEventListener("click", function(e) {
    var url = e.target.attributes["data-url"].value;
    window.location.replace(url);
  });
}
