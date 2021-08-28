document.getElementById("navMenu").style.display = "none";
document.getElementById("nav-btn").addEventListener("click", navBarToggle);

function navBarToggle() {
    let x = document.getElementById("navMenu");
    console.log("basetemplate");
    if (x.style.display === "none") {
      x.style.display = "block";
    } else {
      x.style.display = "none";
    }
  }

 


