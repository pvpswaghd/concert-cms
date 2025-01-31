const API_BASE = 'http://localhost:8000/api';

function showSection(sectionId) {
    document.querySelectorAll('.form-section').forEach(el => 
        el.classList.remove('active'));
    document.getElementById(sectionId).classList.add('active');
}

function showStatus(message, isError = false) {
    const statusDiv = document.getElementById('status');
    statusDiv.className = isError ? 'error' : 'success';
    statusDiv.textContent = message;
    setTimeout(() => statusDiv.textContent = '', 3000);
}

let currentEditingVenue = null;

async function loadVenues() {
    try {
        const response = await fetch(`${API_BASE}/venues/`);
        const venues = await response.json();
        console.log(venues);
        renderVenues(venues);
    } catch (error) {
        showStatus(error.message, true);
    }
}

function renderVenues(venues) {
    const listDiv = document.getElementById('venue-list');
    console.log("venues", venues);
    listDiv.innerHTML = venues.map(venue => `
        <div class="list-item">
            <div>
                <h4>${venue.name}</h4>
                <p>${venue.address}<br>
                Capacity: ${venue.capacity} | Mode: ${venue.admission_mode}</p>
            </div>
            <div class="button-group">
                <button class="edit-btn" onclick="editVenue('${venue.slug}')">Edit</button>
                <button class="delete-btn" onclick="deleteVenue('${venue.slug}')">Delete</button>
            </div>
        </div>
    `).join('');
}

function showVenueForm() {
    document.getElementById('venue-form').style.display = 'block';
    document.getElementById('form-title').textContent = 'Add New Venue';
    document.getElementById('venueForm').reset();
    currentEditingVenue = null;
}

function hideVenueForm() {
    document.getElementById('venue-form').style.display = 'none';
}

function addZoneField() {
    const zoneFields = document.getElementById('zone-fields');
    const newZone = document.createElement('div');
    newZone.className = 'zone-form';
    newZone.innerHTML = `
        <div class="form-group">
            <label>Zone Name:</label>
            <input type="text" name="zone-name" required>
        </div>
        <div class="form-group">
            <label>Zone Type:</label>
            <select name="zone-type" required onchange="toggleZoneFields(this)">
                <option value="assigned">Assigned Seating</option>
                <option value="general">General Admission</option>
            </select>
        </div>
        <div class="assigned-fields">
            <div class="form-group">
                <label>Row Start:</label>
                <input type="text" name="row-start" pattern="[A-Za-z]">
            </div>
            <div class="form-group">
                <label>Row End:</label>
                <input type="text" name="row-end" pattern="[A-Za-z]">
            </div>
            <div class="form-group">
                <label>Seat Start:</label>
                <input type="number" name="seat-start">
            </div>
            <div class="form-group">
                <label>Seat End:</label>
                <input type="number" name="seat-end">
            </div>
        </div>
        <div class="general-fields" style="display: none;">
            <div class="form-group">
                <label>Capacity:</label>
                <input type="number" name="ga-capacity">
            </div>
        </div>
        <button type="button" onclick="this.parentElement.remove()">Remove Zone</button>
    `;
    zoneFields.appendChild(newZone);
}

function toggleZoneFields(select) {
    const parent = select.closest('.zone-form');
    parent.querySelector('.assigned-fields').style.display = 
        select.value === 'assigned' ? 'block' : 'none';
    parent.querySelector('.general-fields').style.display = 
        select.value === 'general' ? 'block' : 'none';
}

async function handleVenueSubmit(event) {
    event.preventDefault();
    const formData = {
        name: document.getElementById('venue-name').value,
        address: document.getElementById('venue-address').value,
        capacity: document.getElementById('venue-capacity').value,
        admission_mode: document.getElementById('venue-admission-mode').value,
        seat_zones: []
    };

    // Collect zone data
    document.querySelectorAll('.zone-form').forEach(zone => {
        const zoneData = {
            name: zone.querySelector('[name="zone-name"]').value,
            type: zone.querySelector('[name="zone-type"]').value
        };

        if (zoneData.type === 'assigned') {
            zoneData.row_start = zone.querySelector('[name="row-start"]').value;
            zoneData.row_end = zone.querySelector('[name="row-end"]').value;
            zoneData.seat_start = zone.querySelector('[name="seat-start"]').value;
            zoneData.seat_end = zone.querySelector('[name="seat-end"]').value;
        } else {
            zoneData.ga_capacity = zone.querySelector('[name="ga-capacity"]').value;
        }

        formData.seat_zones.push(zoneData);
    });

    try {
        const url = currentEditingVenue ? 
            `${API_BASE}/venues/${currentEditingVenue}/` : 
            `${API_BASE}/venues/`;
            
        const response = await fetch(url, {
            method: currentEditingVenue ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (!response.ok) throw new Error(await response.text());
        showStatus(`Venue ${currentEditingVenue ? 'updated' : 'created'} successfully!`);
        hideVenueForm();
        loadVenues();
    } catch (error) {
        showStatus(error.message, true);
    }
}

async function editVenue(slug) {
    try {
        currentEditingVenue = slug;
        const response = await fetch(`${API_BASE}/venues/${slug}/`);
        const venue = await response.json();
        console.log("editVenue", venue); 
        // Populate form fields
        document.getElementById('venue-name').value = venue.name;
        document.getElementById('venue-address').value = venue.address;
        document.getElementById('venue-capacity').value = venue.capacity;
        document.getElementById('venue-admission-mode').value = venue.admission_mode;

        // Clear existing zones and populate
        const zoneFields = document.getElementById('zone-fields');
        zoneFields.innerHTML = '';
        
        venue.zones.forEach(zone => {
            addZoneField();
            const lastZone = zoneFields.lastElementChild;
            lastZone.querySelector('[name="zone-name"]').value = zone.name;
            lastZone.querySelector('[name="zone-type"]').value = zone.type;
            toggleZoneFields(lastZone.querySelector('[name="zone-type"]'));
            
            if (zone.type === 'assigned') {
                lastZone.querySelector('[name="row-start"]').value = zone.row_start;
                lastZone.querySelector('[name="row-end"]').value = zone.row_end;
                lastZone.querySelector('[name="seat-start"]').value = zone.seat_start;
                lastZone.querySelector('[name="seat-end"]').value = zone.seat_end;
            } else {
                lastZone.querySelector('[name="ga-capacity"]').value = zone.ga_capacity;
            }
        });

        document.getElementById('form-title').textContent = 'Edit Venue';
        document.getElementById('venue-form').style.display = 'block';
    } catch (error) {
        showStatus(error.message, true);
    }
}

async function deleteVenue(slug) {
    if (!confirm('Are you sure you want to delete this venue?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/venues/${slug}/`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error(await response.text());
        showStatus('Venue deleted successfully!');
        loadVenues();
    } catch (error) {
        showStatus(error.message, true);
    }
}

let currentEditingConcert = null;

async function loadConcerts(venueSlug) {
    try {
        const response = await fetch(`${API_BASE}/venues/${venueSlug}/concerts/`);
        const concerts = await response.json();
        renderConcerts(concerts);
    } catch (error) {
        showStatus(error.message, true);
    }
}

function renderConcerts(concerts) {
    const listDiv = document.getElementById('concert-list');
    console.log("concerts", concerts);
    listDiv.innerHTML = concerts.map(concert => `
        <div class="list-item">
            <div>
                <h4>${concert.title}</h4>
                <p>${concert.artist} - ${new Date(concert.date).toLocaleDateString()}</p>
            </div>
            <div class="button-group">
                <button class="edit-btn" onclick="editConcert('${concert.slug}')">Edit</button>
                <button class="delete-btn" onclick="deleteConcert('${concert.slug}')">Delete</button>
            </div>
        </div>
    `).join('');
}

function showConcertForm() {
    document.getElementById('concert-form').style.display = 'block';
    document.getElementById('concert-form-title').textContent = 'Add New Concert';
    document.getElementById('concertForm').reset();
    currentEditingConcert = null;
    
    // Clear existing ticket types and add one default
    const ticketTypeFields = document.getElementById('ticket-type-fields');
    ticketTypeFields.innerHTML = '';
    addTicketTypeField(); // Add initial ticket type field
    
    // Trigger zone load for the currently selected venue
    const venueSlug = document.getElementById('venue-select').value;
    loadZonesForCurrentVenue(venueSlug);
}

function hideConcertForm() {
    document.getElementById('concert-form').style.display = 'none';
}

async function loadZonesForCurrentVenue(venueSlug) {
    try {
        const response = await fetch(`${API_BASE}/venues/${venueSlug}/zones/`);
        const zones = await response.json();
        window.currentVenueZones = zones;
    } catch (error) {
        showStatus(error.message, true);
    }
}

async function handleConcertSubmit(event) {
    event.preventDefault();
    const venueSlug = document.getElementById('venue-select').value;
    
    // Basic Form Data
    const formData = {
        name: document.getElementById('concert-name').value,
        date: document.getElementById('concert-date').value,
        artist: document.getElementById('concert-artist').value,
        start_time: document.getElementById('concert-start-time').value,
        ticket_types: []
    };

    // Simple Ticket Type Collection
    document.querySelectorAll('.ticket-type-form').forEach(form => {
        const type = form.querySelector('select[name="ticket-type"]').value;
        const price = parseFloat(form.querySelector('input[name="ticket-price"]').value);
        
        formData.ticket_types.push({
            type,
            price: price.toFixed(2),
            ...(type === 'general' && { 
                ga_capacity: parseInt(form.querySelector('input[name="ga-capacity"]').value)
            })
        });
    });

    try {
        const url = currentEditingConcert 
            ? `${API_BASE}/venues/${venueSlug}/concerts/${currentEditingConcert}/`
            : `${API_BASE}/venues/${venueSlug}/concerts/`;
        
        console.log(formData);

        const response = await fetch(url, {
            method: currentEditingConcert ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (!response.ok) throw new Error(await response.text());
        
        showStatus(`Concert ${currentEditingConcert ? 'updated' : 'created'} successfully!`);
        hideConcertForm();
        loadConcerts(venueSlug);
    } catch (error) {
        showStatus(error.message, true);
    }

    currentEditingConcert = null; // Reset after submission
}

async function loadZonesForCurrentVenue(venueSlug) {
    if (!venueSlug) {
        showStatus('Please select a venue first', true);
        return;
    }
    try {
        console.log(`Loading zones for venue: ${venueSlug}`);
        const response = await fetch(`${API_BASE}/venues/${venueSlug}/zones/`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const zones = await response.json();
        window.currentVenueZones = zones;
        console.log(`Loaded ${zones.length} zones for venue ${venueSlug}`);
    } catch (error) {
        console.error('Zone loading failed:', error);
        showStatus(`Failed to load zones: ${error.message}`, true);
    }
}

function fillConcertForm(concertData) {
    console.log('Filling concert form with:', concertData);
    try {
        document.getElementById('concert-name').value = concertData.name || '';
        document.getElementById('concert-date').value = concertData.date ? concertData.date.split('T')[0] : '';
        document.getElementById('concert-artist').value = concertData.artist || '';
        
        function parseISOTime(timeString) {
            if (!timeString) return '';
            try {
                // Handle different time formats
                const parts = timeString.split('T');
                const timePart = parts.length > 1 ? parts[1] : timeString;
                return timePart.slice(0, 5);
            } catch (error) {
                console.error('Invalid time format:', timeString, error);
                return '';
            }
        }

        document.getElementById('concert-start-time').value = parseISOTime(concertData.start_time);
        if (concertData.end_time) {
            document.getElementById('concert-end-time').value = parseISOTime(concertData.end_time);
        } else {
            document.getElementById('concert-end-time').value = '';
        }
        
        if (concertData.description) {
            document.getElementById('concert-description').value = concertData.description;
        }

        if (concertData.genre) {
            document.getElementById('concert-genre').value = concertData.genre;
        }

        // Ticket type handling
        const ticketTypeFields = document.getElementById('ticket-type-fields');
        ticketTypeFields.innerHTML = '';
        
        if (concertData.ticket_types?.length > 0) {
            console.log('Processing ticket types:', concertData.ticket_types);
            concertData.ticket_types.forEach(ticketType => {
                try {
                    console.log('Adding ticket type:', ticketType);
                    addTicketTypeField({
                        type: ticketType.type,
                        price: ticketType.price,
                        ga_capacity: ticketType.ga_capacity,
                        seat_zone: ticketType.seat_zone
                    });
                } catch (error) {
                    console.error('Error adding ticket type:', ticketType, error);
                }
            });
        } else {
            console.warn('No ticket types found in concert data');
            addTicketTypeField();
        }

    } catch (error) {
        console.error('Error filling concert form:', error);
        showStatus('Failed to load concert data', true);
    }
}

// Parse ISO time safely
function parseISOTime(isoString) {
    if (!isoString) return '';
    try {
        return isoString.split('T')[1].split('.')[0].slice(0, 5);
    } catch (error) {
        console.error('Error parsing ISO time:', isoString, error);
        return '';
    }
}

function updateVenueSelectorForConcerts(venueSlug) {
    const venueSelect = document.getElementById('venue-select');
    if (venueSelect.value !== venueSlug) {
        venueSelect.value = venueSlug;
        loadZonesForCurrentVenue(venueSlug);
    }
}

async function editConcert(slug) {
    try {
        currentEditingConcert = slug;
        const venueSlug = document.getElementById('venue-select').value;
        
        console.log('Starting concert edit for:', slug);
        const response = await fetch(`${API_BASE}/venues/${venueSlug}/concerts/${slug}/`);
        const concertData = await response.json();
        console.log('Fetched concert data:', concertData);

        // Check if response is valid
        if (!concertData || !concertData.ticket_types) {
            throw new Error('Invalid concert data received');
        }

        // Set up the form
        showConcertForm();
        document.getElementById('concert-form-title').textContent = 'Edit Concert';
        fillConcertForm(concertData);
        
    } catch (error) {
        console.error('Error in editConcert:', error);
        showStatus(error.message, true);
    }
}

async function deleteConcert(slug) {
    if (!confirm('Are you sure you want to delete this concert?')) return;
    
    try {
        const venueSlug = document.getElementById('venue-select').value;
        const response = await fetch(`${API_BASE}/venues/${venueSlug}/concerts/${slug}/`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error(await response.text());
        showStatus('Concert deleted successfully!');
        loadConcerts(venueSlug);
    } catch (error) {
        showStatus(error.message, true);
    }
}

// Initialize the application
async function initialize() {
    await loadVenues();
    const venues = await fetch(`${API_BASE}/venues/`).then(r => r.json());
    const venueSelect = document.getElementById('venue-select');
    venueSelect.innerHTML = venues.map(v => 
        `<option value="${v.slug}">${v.name}</option>`
    ).join('');
    if (venues.length) loadConcerts(venues[0].slug);
}

function addTicketTypeField(ticketType = {}) {
    const container = document.getElementById('ticket-type-fields');
    const newField = document.createElement('div');
    newField.className = 'ticket-type-form';
    newField.innerHTML = `
        <div class="form-group">
            <label>Ticket Type:</label>
            <select name="ticket-type" required onchange="toggleTicketTypeFields(this)">
                <option value="assigned">Assigned Seating</option>
                <option value="general">General Admission</option>
            </select>
        </div>
        <div class="form-group">
            <label>Price:</label>
            <input type="number" step="0.01" name="ticket-price" value="${ticketType.price || ''}" required>
        </div>
        <div class="assigned-ticket-fields" style="display: ${ticketType.type === 'assigned' ? 'block' : 'none'}">
            <div class="form-group">
                <label>Seat Zone:</label>
                <select name="seat-zone">
                    ${window.currentVenueZones?.map(zone => 
                        `<option value="${zone.slug}" ${ticketType.zone === zone.slug ? 'selected' : ''}>
                            ${zone.name} (${zone.total_seats} seats)
                        </option>`
                    ).join('')}
                </select>
            </div>
        </div>
        <div class="general-ticket-fields" style="display: ${ticketType.type === 'general' ? 'block' : 'none'}">
            <div class="form-group">
                <label>Capacity:</label>
                <input type="number" name="ga-capacity" value="${ticketType.ga_capacity || ''}">
            </div>
        </div>
        <button type="button" class="delete-btn" onclick="this.parentElement.remove()">
            Remove Ticket Type
        </button>
    `;

    if (ticketType.type) {
        newField.querySelector('select[name="ticket-type"]').value = ticketType.type;
    }
    
    // Initialize zone selector using cached zone data
    const zoneOptions = window.currentVenueZones?.map(zone => 
        `<option value="${zone.slug}" ${ticketType.seat_zone === zone.slug ? 'selected' : ''}>
            ${zone.name} (${zone.total_seats} seats)
        </option>`
    ).join('') || '';
    newField.querySelector('select[name="seat-zone"]').innerHTML = zoneOptions;

    container.appendChild(newField);
    toggleTicketTypeFields(newField.querySelector('select[name="ticket-type"]'));
}

async function populateZoneSelections(container) {
    const venueSlug = document.getElementById('venue-select').value;
    if (!venueSlug) {
        showStatus('Please select a venue before configuring zones', true);
        return;
    }

    try {
        console.log(`Populating zones for venue ${venueSlug}`);
        const response = await fetch(`${API_BASE}/venues/${venueSlug}/zones/`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const zones = await response.json();
        const select = container.querySelector('select[name="seat-zone"]');
        select.innerHTML = zones.map(z => 
            `<option value="${z.slug}">${z.name} (${z.total_seats} seats)</option>`
        ).join('');
        console.log(`Populated ${zones.length} zones in selector`);
    } catch (error) {
        console.error('Zone population failed:', error);
        showStatus(error.message, true);
    }
}

function toggleTicketTypeFields(select) {
    const parent = select.closest('.ticket-type-form');
    parent.querySelector('.assigned-ticket-fields').style.display = 
        select.value === 'assigned' ? 'block' : 'none';
    parent.querySelector('.general-ticket-fields').style.display = 
        select.value === 'general' ? 'block' : 'none';
}

window.addEventListener('load', initialize);