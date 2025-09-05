async function fetchDropdownData(endpoint) {
  try {
    const response = await fetch(endpoint);
    if (!response.ok) {
      throw new Error(`Failed to fetch options from ${endpoint}, Status: ${response.status}`);
    }
    const data = await response.json();
    console.log(`Fetched data from ${endpoint}:`, data); // Debugging log
    if (!data.options || data.options.length === 0) {
      console.warn(`No options received from ${endpoint}`);
    }
    return data.options || [];
  } catch (error) {
    console.error(`Error fetching options from ${endpoint}:`, error);
    return [];
  }
}


// Utility function to populate a dropdown with options
function populateDropdown(dropdownId, options) {
  const dropdown = document.getElementById(dropdownId);
  if (!dropdown) {
    console.error(`Dropdown with ID ${dropdownId} not found in DOM.`);
    return;
  }

  dropdown.innerHTML = '<option value="">--Select--</option>'; // Clear existing options
  options.forEach(option => {
    const opt = document.createElement('option');
    opt.value = option;
    opt.textContent = option;
    dropdown.appendChild(opt);
  });

  console.log(`Populated dropdown ${dropdownId} with options:`, options); // Debugging log
}

// Fetch options for all dropdowns on page load
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const departmentOptions = await fetchDropdownData('http://127.0.0.1:5000/dropdown/department');
    populateDropdown('departmentDropdown', departmentOptions);

    const classOptions = await fetchDropdownData('http://127.0.0.1:5000/dropdown/class');
    populateDropdown('classDropdown', classOptions);

    const teacherOptions = await fetchDropdownData('http://127.0.0.1:5000/dropdown/teacher');
    populateDropdown('teacherDropdown', teacherOptions);

    console.log("Dropdowns populated successfully.");
  } catch (error) {
    console.error("Error initializing dropdowns:", error);
  }
});

// Event listener for showing the Generate Section
document.getElementById("uploadButton").addEventListener("click", async () => {
  const fileInput = document.getElementById("fileInput");
  const file = fileInput.files[0];

  if (!file) {
    alert("Please select a file first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("http://127.0.0.1:5000/upload", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();
    if (response.ok) {
      alert(result.message || "File uploaded successfully!");
    } else {
      alert(result.error || "An error occurred during upload.");
    }
  } catch (error) {
    console.error("Error during file upload:", error);
    alert("Failed to upload file. Please try again.");
  }
});



document.getElementById("generateButton").addEventListener("click", async () => {
  try {
    const response = await fetch("http://127.0.0.1:5000/generate", { method: "POST" });
    const result = await response.json();
    if (response.ok) {
      alert(result.message || "Schedule generated successfully!");
    } else {
      alert(result.error || "Failed to generate schedule.");
    }
  } catch (error) {
    console.error("Error generating schedule:", error);
    alert("Failed to generate schedule. Please try again.");
  }
});

// Toggle Advanced Section
const toggleAdvanced = document.getElementById("toggleAdvanced");
const advancedOptions = document.getElementById("advancedOptions");

if (toggleAdvanced && advancedOptions) {
  toggleAdvanced.addEventListener("click", () => {
    const isHidden = advancedOptions.classList.contains("hidden");
    advancedOptions.classList.toggle("hidden");
    toggleAdvanced.textContent = isHidden ? "Advanced v" : "Advanced >";
  });
}


document.getElementById("downloadButton").addEventListener("click", async () => {
  const fileType = document.getElementById("fileType").value;
  if (!fileType) {
    alert("Please select a file type to download.");
    return;
  }
  try {
    const response = await fetch(`http://127.0.0.1:5000/download?type=${fileType}`);
    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `timetable.${fileType}`;
      link.click();
    } else {
      const error = await response.json();
      alert(error.error || "Failed to download the timetable.");
    }
  } catch (error) {
    console.error("Error downloading timetable:", error);
    alert("Failed to download the timetable. Please try again.");
  }
});

// Add debug logs for other buttons if needed.
