// Fetch and display concerts
async function fetchConcerts() {
    const response = await fetch('http://127.0.0.1:8000/api/v2/pages/?type=api.ConcertIndexPage&fields=_,id,title,artist,date,location,sold_out');
    const data = await response.json();
    const concertList = document.getElementById('concert-list');
    concertList.innerHTML = '';

    data.items.forEach(concert => {
        const li = document.createElement('li');
        console.log(concert)
        li.innerHTML = `
            <p>ID:${concert.id}</p>
            <span>${concert.title} - ${concert.date} - ${concert.artist} - ${concert.sold_out ? "Sold Out" : "Available"}</span>
            <div>
                <button onclick="editConcert(${concert.id})">Edit</button>
                <button onclick="deleteConcert(${concert.id})">Delete</button>
            </div>
        `;
        concertList.appendChild(li);
    });
}

// Create Concert
document.getElementById('create-concert-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const concertData = {
        title: document.getElementById('title').value,
        name: document.getElementById('name').value,
        date: document.getElementById('date').value,
        location: document.getElementById('location').value,
        price: document.getElementById('price').value,
        description: document.getElementById('description').value,
        start_time: document.getElementById('start-time').value,
        end_time: document.getElementById('end-time').value,
        concert_type: document.getElementById('concert-type').value,
        artist: document.getElementById('artist').value,
        sold_out: document.getElementById('sold-out').checked, // Add sold_out field
    };

    console.log(concertData);

    const response = await fetch('http://localhost:8000/api/create-concert/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(concertData),
    });

    if (response.ok) {
        alert('Concert created successfully!');
        fetchConcerts();
    } else {
        alert('Error creating concert.');
    }
});

// Edit Concert
async function editConcert(id) {
    const response = await fetch(`http://localhost:8000/api/v2/pages/${id}/`);
    const concert = await response.json();

    document.getElementById('update-id').value = concert.id;
    document.getElementById('update-title').value = concert.title;
    document.getElementById('update-name').value = concert.name;
    document.getElementById('update-date').value = concert.date;
    document.getElementById('update-location').value = concert.location;
    document.getElementById('update-price').value = concert.price;
    document.getElementById('update-description').value = concert.description;
    document.getElementById('update-start-time').value = concert.start_time;
    document.getElementById('update-end-time').value = concert.end_time;
    document.getElementById('update-concert-type').value = concert.concert_type;
    document.getElementById('update-artist').value = concert.artist;
    document.getElementById('update-sold-out').checked = concert.sold_out; // Populate sold_out field

    document.getElementById('update-concert-form').style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Update Concert
document.getElementById('update-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('update-id').value;
    const concertData = {
        title: document.getElementById('update-title').value,
        name: document.getElementById('update-name').value,
        date: document.getElementById('update-date').value,
        location: document.getElementById('update-location').value,
        price: document.getElementById('update-price').value,
        description: document.getElementById('update-description').value,
        start_time: document.getElementById('update-start-time').value,
        end_time: document.getElementById('update-end-time').value,
        concert_type: document.getElementById('update-concert-type').value,
        artist: document.getElementById('update-artist').value,
        sold_out: document.getElementById('update-sold-out').checked, // Add sold_out field
    };

    console.log(concertData);

    const response = await fetch(`http://localhost:8000/api/update-concert/${id}/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(concertData),
    });

    if (response.ok) {
        alert('Concert updated successfully!');
        fetchConcerts();
        cancelUpdate();
    } else {
        alert('Error updating concert.');
    }
});

// Cancel Update
function cancelUpdate() {
    document.getElementById('update-concert-form').style.display = 'none';
}

// Delete Concert
async function deleteConcert(id) {
    if (confirm('Are you sure you want to delete this concert?')) {
        const response = await fetch(`http://localhost:8000/api/remove-concert/${id}/`, {
            method: 'DELETE',
        });

        if (response.ok) {
            alert('Concert deleted successfully!');
            fetchConcerts();
        } else {
            alert('Error deleting concert.');
        }
    }
}

// Initial fetch
fetchConcerts();