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
};

window.addEventListener("load", function(e) {
  var messagePane = document.getElementById("messagePane")
  messagePane.scrollTo(0, messagePane.scrollHeight);
});