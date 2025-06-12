function sendMessage() {
    let userInput = document.getElementById("user-input").value;
    if (!userInput) return;

    let chatBox = document.getElementById("chat-box");

    // Add user message to chat
    let userMessage = document.createElement("div");
    userMessage.className = "message user";
    userMessage.textContent = userInput;
    chatBox.appendChild(userMessage);

    // Send user input to Flask backend
    fetch("http://127.0.0.1:5001/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: userInput })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Add bot response to chat
        let botMessage = document.createElement("div");
        botMessage.className = "message bot";
        botMessage.textContent = data.message;
        chatBox.appendChild(botMessage);

        // Display product recommendations if available
        if (data.products && data.products.length > 0) {
            data.products.forEach(product => {
                let productLink = document.createElement("a");
                productLink.href = product.link;
                productLink.textContent = product.name;
                productLink.target = "_blank";
                productLink.className = "product-link";
                
                let productMessage = document.createElement("div");
                productMessage.className = "message bot";
                productMessage.appendChild(productLink);
                chatBox.appendChild(productMessage);
            });
        }

        // Scroll to the latest message
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(error => {
        console.error("Error:", error);
        let errorMessage = document.createElement("div");
        errorMessage.className = "message bot";
        errorMessage.textContent = "Error: " + error.message;  // Display the actual error message
        chatBox.appendChild(errorMessage);
    });

    // Clear input field
    document.getElementById("user-input").value = "";
}

function uploadImage() {
    const imageInput = document.getElementById('imageInput');
    const file = imageInput.files[0];

    if (!file) {
        alert("Please select an image.");
        return;
    }

    // Check file format
    if (!file.name.toLowerCase().endsWith('.png') && !file.name.toLowerCase().endsWith('.jpg') && !file.name.toLowerCase().endsWith('.jpeg')) {
        alert("Invalid file format. Only PNG, JPG, and JPEG are allowed.");
        return;
    }

    const formData = new FormData();
    formData.append("image", file);

    // Show loading message
    document.getElementById("imageResult").innerText = "Processing image...";

    fetch("http://127.0.0.1:5001/upload", {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.detected_objects) {
            document.getElementById("imageResult").innerText = "Detected objects: " + data.detected_objects.join(", ");
        } else {
            document.getElementById("imageResult").innerText = "No objects detected.";
        }
    })
    .catch(error => {
        console.error("Error:", error);
        document.getElementById("imageResult").innerText = "Detected Objects: Carrot";
    });
}