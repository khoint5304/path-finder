function onClick(e) {
    if (typeof sessionStorage["beginLat"] === "undefined") {
        sessionStorage["beginLat"] = e.latlng.lat;
        sessionStorage["beginLng"] = e.latlng.lng;
    } else {
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

        window.location.search = params.toString();
    }
}
