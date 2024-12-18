function onClick(e) {
    let clickCount = parseInt(sessionStorage.getItem("clickCount") || "0");
    clickCount++;

    if (clickCount === 1) {
        sessionStorage["beginLat"] = e.latlng.lat;
        sessionStorage["beginLng"] = e.latlng.lng;
        sessionStorage["clickCount"] = clickCount;

    } else if (clickCount === 2) {
        sessionStorage["endLat"] = e.latlng.lat;
        sessionStorage["endLng"] = e.latlng.lng;

        let params = new URL(window.location).searchParams;
        params.set("begin_lat", sessionStorage["beginLat"]);
        params.set("begin_lng", sessionStorage["beginLng"]);
        params.set("end_lat", sessionStorage["endLat"]);
        params.set("end_lng", sessionStorage["endLng"]);

        sessionStorage.removeItem("beginLat");
        sessionStorage.removeItem("beginLng");
        sessionStorage.removeItem("endLat");
        sessionStorage.removeItem("endLng");
        sessionStorage.removeItem("clickCount");

        // Show loader
        const overlay = document.createElement("div");
        overlay.id = "overlay";
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;

        const spinner = document.createElement("div");
        spinner.style.cssText = `
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 2s linear infinite;
        `;
        spinner.className = "progress-spinner";

        overlay.appendChild(spinner);

        const style = document.createElement("style");
        style.innerHTML = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        `;
        document.head.appendChild(style);
        document.body.appendChild(overlay);

        window.location.search = params.toString();
    }
}
