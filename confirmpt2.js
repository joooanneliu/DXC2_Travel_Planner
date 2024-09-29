function addPerson() {
    const peopleContainer = document.getElementById('people-traveling');
    const select = document.createElement('select');

    select.innerHTML = `
        <option value="0-5 years">0 - 5 years</option>
        <option value="6-12 years">6 - 12 years</option>
        <option value="13-17 years">13 - 17 years</option>
        <option value="18-20 years">18 - 20 years</option>
        <option value="21-35 years">21 - 35 years</option>
        <option value="36-59 years">36 - 59 years</option>
        <option value="60+ years">60+ years</option>
    `;

    peopleContainer.insertBefore(select, peopleContainer.lastElementChild);
}