function addPerson() {
    const peopleContainer = document.getElementById('people-traveling');
    const select = document.createElement('select');

    select.innerHTML = `
        <option value="0-5">0 - 5</option>
        <option value="6-12">6 - 12</option>
        <option value="13-17">13 - 17</option>
        <option value="18-20">18 - 20</option>
        <option value="21-35">21 - 35</option>
        <option value="36-59">36 - 59</option>
        <option value="60+">60+</option>
    `;

    peopleContainer.insertBefore(select, peopleContainer.lastElementChild);
}