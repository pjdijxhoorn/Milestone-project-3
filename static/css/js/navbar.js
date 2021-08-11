document.getElementById("navMenu").style.display = "none";

document.getElementById("nav-btn").addEventListener("click", navBarToggle);

function navBarToggle() {
    var x = document.getElementById("navMenu");
    if (x.style.display === "none") {
      x.style.display = "block";
    } else {
      x.style.display = "none";
    }
  }