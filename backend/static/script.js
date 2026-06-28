const cards = document.querySelectorAll(".difficulty");

let selected = "easy";

cards.forEach(card=>{

    card.addEventListener("click",()=>{

        cards.forEach(c=>{
            c.classList.remove("active");
        });

        card.classList.add("active");

        selected = card.dataset.mode;

    });

});

document.getElementById("readyBtn")
.addEventListener("click",()=>{

    localStorage.setItem(
        "difficulty",
        selected
    );

    window.location.href="game.html";

});