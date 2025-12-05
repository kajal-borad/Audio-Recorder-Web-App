
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

            // default 128k
            select.innerHTML = `<option value="128k" selected>default (128k)</option>`;

            if (!data.bitrates || data.bitrates.length === 0) return;

            // Filter out 128 and 129
            let filtered = data.bitrates.filter(b => b !== 128 && b !== 129);

            filtered.forEach(b => {
                select.innerHTML += `<option value="${b}k">${b}k</option>`;
            });
        });
    }, 400);
});

document.querySelector("form").addEventListener("submit", function (e) {
    e.preventDefault();

    let form = this;
    let formData = new FormData(form);

    // Disable all inputs
    document.querySelectorAll("input, select, button").forEach(el => {
        el.disabled = true;
        el.classList.add("blur-input");
    });

    // Show loader
    document.getElementById("loader").style.display = "block";

    fetch(form.action, {
        method: form.method,
        body: formData
    })
    .then(async res => {
        let blob = await res.blob();

        // Extract filename
        let filename = "downloaded_file";
        let disposition = res.headers.get("Content-Disposition");

        if (disposition && disposition.includes("filename=")) {
            filename = disposition.split("filename=")[1].replace(/"/g, "");
        }

        // Download file
        let a = document.createElement("a");
        let url = URL.createObjectURL(blob);
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);

        // Hide loader & enable inputs
        document.getElementById("loader").style.display = "none";
        document.querySelectorAll("input, select, button").forEach(el => {
            el.disabled = false;
            el.classList.remove("blur-input");
        });
    });
});
