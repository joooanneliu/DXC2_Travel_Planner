document.addEventListener("DOMContentLoaded", () => {
    const cities = ["New York", "Austin", "San Francisco", "Dallas", "Chicago", "Houston"];
    
    const setupDropdown = (inputId, dropdownListId) => {
        const input = document.getElementById(inputId);
        const dropdownList = document.getElementById(dropdownListId);

        input.addEventListener("input", () => {
            const value = input.value.toLowerCase();
            dropdownList.innerHTML = "";
            if (value) {
                const filteredCities = cities.filter(city => city.toLowerCase().includes(value));
                filteredCities.forEach(city => {
                    const item = document.createElement("div");
                    item.textContent = city;
                    item.classList.add("dropdown-item");
                    item.addEventListener("click", () => {
                        input.value = city;
                        dropdownList.innerHTML = "";
                        dropdownList.classList.add("hidden");
                    });
                    dropdownList.appendChild(item);
                });
                dropdownList.classList.toggle("hidden", filteredCities.length === 0);
            } else {
                dropdownList.classList.add("hidden");
            }
        });
    };

    setupDropdown("departure-city-input", "departure-dropdown-list");
    setupDropdown("arrival-city-input", "arrival-dropdown-list");

    document.addEventListener("click", (event) => {
        const departureInput = document.getElementById("departure-city-input");
        const arrivalInput = document.getElementById("arrival-city-input");
        const departureDropdown = document.getElementById("departure-dropdown-list");
        const arrivalDropdown = document.getElementById("arrival-dropdown-list");
        
        if (!departureInput.contains(event.target) && !departureDropdown.contains(event.target) &&
            !arrivalInput.contains(event.target) && !arrivalDropdown.contains(event.target)) {
            departureDropdown.classList.add("hidden");
            arrivalDropdown.classList.add("hidden");
        }
    });
});
