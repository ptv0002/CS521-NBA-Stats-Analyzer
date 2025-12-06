document.addEventListener("DOMContentLoaded", () => {
    const playerSelect = document.getElementById("playerSelect");
    const tableHead = document.getElementById("tableHead");
    const tableBody = document.getElementById("tableBody");

    const modalEl = document.getElementById("playerModal");
    const modalTitle = document.getElementById("playerModalLabel");
    const modalDetails = document.getElementById("playerDetails");
    let bsModal = null;

    if (window.bootstrap && bootstrap.Modal) {
        bsModal = new bootstrap.Modal(modalEl);
    }

    let allPlayers = [];

    // 1) Load all player records
    fetch("/api/players")
        .then(res => res.json())
        .then(players => {
            allPlayers = players;

            // 2) Load just the names for the dropdown
            return fetch("/api/player-names");
        })
        .then(res => res.json())
        .then(names => {
            // Populate the dropdown
            names.forEach(name => {
                const opt = document.createElement("option");
                opt.value = name;
                opt.textContent = name;
                playerSelect.appendChild(opt);
            });

            // Auto-select first player and trigger change
            if (names.length > 0) {
                playerSelect.value = names[0];
                playerSelect.dispatchEvent(new Event("change"));
            }
        })
        .catch(err => {
            console.error("Error loading players:", err);
        });

    // 3) When user selects a player, show their row in the main table
    playerSelect.addEventListener("change", () => {
        const selectedName = playerSelect.value;
        const playerData = allPlayers.find(p => p.FullName === selectedName);

        if (!playerData) {
            tableHead.innerHTML = "";
            tableBody.innerHTML = "<tr><td colspan='10'>No data for this player</td></tr>";
            return;
        }

        // Build table header from keys
        const headers = Object.keys(playerData);
        tableHead.innerHTML = headers.map(h => `<th>${h}</th>`).join("");

        // Build table row
        tableBody.innerHTML =
            "<tr>" + headers.map(h => `<td>${playerData[h]}</td>`).join("") + "</tr>";

        // Make the player name clickable to open modal
        const firstCell = tableBody.querySelector("td");
        if (firstCell) {
            firstCell.innerHTML = `<a href="#" id="playerLink">${playerData.FullName}</a>`;
            document.getElementById("playerLink").addEventListener("click", (e) => {
                e.preventDefault();
                showPlayerBoxscore(playerData.FullName);
            });
        }
    });

    // -------- Show player's basic boxscore stats in the modal --------
    function showPlayerBoxscore(playerName) {
        fetch(`/api/player-averages/${encodeURIComponent(playerName)}`)
            .then(res => res.json())
            .then(stats => {
                if (stats.error) {
                    modalDetails.innerHTML = "<tr><td colspan='3'>No stats available</td></tr>";
                    modalTitle.textContent = "Player Stats";
                    if (bsModal) bsModal.show();
                    return;
                }

                // Modal title
                modalTitle.textContent = playerName;

                // Build a simple 3-column table for stats
                const tableData = Object.entries(stats).filter(([k]) => k !== "FullName");

                let html = "<tr>";
                tableData.forEach(([key, value], i) => {
                    html += `
                        <td>
                            <div class="stat-label">${key}</div>
                            <div class="stat-value">${value}</div>
                        </td>
                    `;
                    if ((i + 1) % 3 === 0) html += "</tr><tr>";
                });
                html += "</tr>";

                modalDetails.innerHTML = html;

                if (bsModal) bsModal.show();
            })
            .catch(err => console.error("Error loading player stats:", err));
    }
});
