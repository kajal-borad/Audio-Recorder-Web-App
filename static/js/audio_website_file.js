
const darkToggle = document.getElementById("darkToggle");

darkToggle.onclick = () => {
    document.body.classList.toggle("dark");

    if (document.body.classList.contains("dark")) {
        // Dark Mode
        document.body.style.background = "#111";
        document.body.style.color = "#fff";
        darkToggle.textContent = "Light Mode ☀️";

        // Navbar
        document.querySelector(".navbar").style.background = "#222";
        document.querySelectorAll(".navbar a").forEach(a => a.style.color = "#fff");
        darkToggle.style.backgroundColor = "#555";
        darkToggle.style.color = "#fff";

        // Container
        document.querySelectorAll(".container").forEach(c => {
            c.style.background = "#222";
            c.style.color = "#fff";
            c.style.boxShadow = "0 0 15px rgba(255,255,255,0.1)";
        });
    } else {
        // Light Mode
        document.body.style.background = "#fafafa";
        document.body.style.color = "#000";
        darkToggle.textContent = "Dark Mode 🌙";

        // Navbar
        document.querySelector(".navbar").style.background = "#eee";
        document.querySelectorAll(".navbar a").forEach(a => a.style.color = "#000");
        darkToggle.style.backgroundColor = "#ddd";
        darkToggle.style.color = "#000";

        // Container
        document.querySelectorAll(".container").forEach(c => {
            c.style.background = "#f9f9f9";
            c.style.color = "#000";
            c.style.boxShadow = "0 0 15px rgba(0,0,0,0.1)";
        });
    }
};



let timer = null;

document.querySelector("input[name='youtube_url']").addEventListener("input", function () {
    clearTimeout(timer);
    let url = this.value;

    if (!url) return;

    timer = setTimeout(() => {
        fetch("/get_info", {
            method: "POST",
            headers: {"Content-Type": "application/x-www-form-urlencoded"},
            body: "youtube_url=" + encodeURIComponent(url)
        })
        .then(res => res.json())
        .then(data => {
            let select = document.getElementById("qualitySelect");
            select.innerHTML = "";

            if (!data.bitrates || data.bitrates.length === 0) {
                select.innerHTML = "<option>No qualities found</option>";
                return;
            }

            data.bitrates.forEach(b => {
                select.innerHTML += `<option value="${b}k">${b}k</option>`;
            });
        });
    }, 400); // 0.4 sec delay to prevent spam calls
});

