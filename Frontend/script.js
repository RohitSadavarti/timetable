// File upload functionality
document.getElementById("file-upload-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const fileInput = document.getElementById("excelFile");
    if (!fileInput.files[0]) {
        alert("Please upload an Excel file.");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        console.log("Uploading file to backend...");

        // Send the file to the backend
        const response = await fetch("http://127.0.0.1:5000/upload", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || "File upload failed");
        }

        const result = await response.json();
        console.log("Response from backend:", result);

        if (!result.departments || !result.classes) {
            throw new Error("Departments or Classes not returned from the backend.");
        }

        // Populate dropdowns
        populateDropdown("department", result.departments);
        populateDropdown("class", result.classes);

        // Show the selection form
        document.getElementById("selection-form").style.display = "block";
        console.log("Dropdowns populated successfully.");
    } catch (error) {
        console.error("Error during upload:", error.message);
        alert(`Error: ${error.message}`);
    }
});

// Schedule generation functionality
let generatedSchedule = null; // Store the generated schedule globally

// Schedule generation functionality
document.getElementById("getButton").addEventListener("click", async () => {
    const department = document.getElementById("department").value;
    const selectedClass = document.getElementById("class").value;

    if (!department || !selectedClass) {
        alert("Please select both a department and a class.");
        return;
    }

    try {
        console.log("Requesting schedule from backend...");
        const response = await fetch("http://127.0.0.1:5000/generate_schedule", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ department, class: selectedClass }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || "Failed to generate schedule.");
        }

        const schedule = await response.json();
        console.log("Schedule received:", schedule);

        // Store the generated schedule for downloading
        generatedSchedule = schedule;

        // Display the schedule in the frontend
        displaySchedule(schedule);
    } catch (error) {
        console.error("Error fetching schedule:", error.message);
        alert(`Error: ${error.message}`);
    }
});

// File download functionality
document.getElementById("downloadButton").addEventListener("click", async () => {
    const format = document.getElementById("format").value;

    if (!format) {
        alert("Please select a format to download.");
        return;
    }

    if (!generatedSchedule) {
        alert("Please generate a schedule before downloading.");
        return;
    }

    try {
        console.log("Requesting download from backend...");
        const response = await fetch("http://127.0.0.1:5000/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ format, schedule: generatedSchedule }),
        });

        if (!response.ok) {
            throw new Error("Failed to download file.");
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `schedule.${format === "word" ? "docx" : format}`;
        a.click();
        window.URL.revokeObjectURL(url);

        console.log("File downloaded successfully.");
    } catch (error) {
        console.error("Error downloading file:", error.message);
        alert(`Error: ${error.message}`);
    }
});


// File download functionality
document.getElementById("downloadButton").addEventListener("click", async () => {
    const format = document.getElementById("format").value;
    const department = document.getElementById("department").value;
    const selectedClass = document.getElementById("class").value;

    if (!format) {
        alert("Please select a format to download.");
        return;
    }
    if (!department || !selectedClass) {
        alert("Please select both a department and a class.");
        return;
    }

    try {
        console.log("Requesting download from backend...");
        const response = await fetch("http://127.0.0.1:5000/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ format, department, class: selectedClass }),
        });

        if (!response.ok) {
            throw new Error("Failed to download file.");
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `schedule_${department}_${selectedClass}.${format === "word" ? "docx" : format}`;
        a.click();
        window.URL.revokeObjectURL(url);

        console.log("File downloaded successfully.");
    } catch (error) {
        console.error("Error downloading file:", error.message);
        alert(`Error: ${error.message}`);
    }
});


// Event listener to download the entire timetable for all branches and classes
document.getElementById("downloadEntireTimetable").addEventListener("click", async () => {
    const format = document.getElementById("format").value; // PDF, Word, or Excel

    if (!format) {
        alert("Please select a format to download.");
        return;
    }

    try {
        console.log("Requesting entire timetable from backend...");
        const response = await fetch("http://127.0.0.1:5000/download_entire_timetable", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ format })
        });

        if (!response.ok) {
            const error = await response.json();
            console.error("Error from backend:", error);  // Log the error message from backend
            alert(`Failed to download entire timetable: ${error.error}`);
            return;
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `entire_timetable.${format === "word" ? "docx" : format}`;
        a.click();
        window.URL.revokeObjectURL(url);

        console.log("Entire timetable downloaded successfully.");
    } catch (error) {
        console.error("Error during download:", error);
        alert(`Error: ${error.message}`);
    }
});
// Function to populate dropdown options dynamically
function populateDropdown(elementId, items) {
    const dropdown = document.getElementById(elementId);
    dropdown.innerHTML = `<option value="">--Select ${elementId}--</option>`;

    items.forEach((item) => {
        const option = document.createElement("option");
        option.value = item;
        option.textContent = item;
        dropdown.appendChild(option);
    });

    console.log(`Dropdown ${elementId} populated with items:`, items);
}

// Function to display the schedule in a table
function displaySchedule(schedule) {
    const container = document.getElementById("schedule-container");

    // Clear any previous content
    container.innerHTML = "";

    // Create table HTML
    const tableHTML = `
        <h3>Generated Schedule</h3>
        <table border="1" style="width:100%; text-align:center; border-collapse:collapse;">
            <thead>
                <tr>
                    <th>Time</th>
                    ${schedule.days.map((day) => `<th>${day}</th>`).join("")}
                </tr>
            </thead>
            <tbody>
                ${schedule.slots
                    .map(
                        (slot) => `
                        <tr>
                            <td>${slot.time}</td>
                            ${slot.schedule.map((item) => `<td>${item || ""}</td>`).join("")}
                        </tr>
                    `
                    )
                    .join("")}
            </tbody>
        </table>
    `;

    // Append the table to the placeholder container
    container.innerHTML = tableHTML;
}
