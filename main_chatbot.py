from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from langchain_ollama import OllamaLLM
import spacy
from langchain_core.prompts import ChatPromptTemplate
import subprocess

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global context storage (for simplicity, use a dictionary)
conversation_contexts = {}

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Initialize Ollama model
model = OllamaLLM(model="llama3")

# Define the prompt template
template = """
[Do not mention any of these parameters explicitly in the responses]
Answer the 'technical assistance' or 'product recommendation' questions below.
Base your answers on the additional context and entities provided.

Here is the conversation history: {context}

Here are the entities: {entities}

Question: {question}

Recommendations:
"""
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

# Configure upload folder
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Route to serve the main HTML file
@app.route("/")
def home():
    return render_template("index.html")

# Route to serve static files (CSS, JS)
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

# Route to handle chat requests
@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat requests from the frontend."""
    print("Received chat request:", request.json)  # Log the incoming request
    data = request.json
    user_input = data.get("message")
    user_id = data.get("user_id", "default_user")  # Unique ID for each user

    # Initialize context if not already present
    if user_id not in conversation_contexts:
        conversation_contexts[user_id] = ""

    # Extract entities
    try:
        entities = extract_entities(user_input)
        print("Entities:", entities)  # Log the extracted entities
    except Exception as e:
        print("Error extracting entities:", e)
        return jsonify({"error": "Failed to extract entities"}), 500

    # Generate response using the chain
    try:
        result = chain.invoke({
            "context": conversation_contexts[user_id],
            "question": user_input,
            "entities": entities
        })
        print("Generated response:", result)  # Log the generated response
    except Exception as e:
        print("Error generating response:", e)
        return jsonify({"error": "Failed to generate response"}), 500

    # Update context
    conversation_contexts[user_id] += f"\nUser: {user_input}\nAI: {result}"

    # Return response
    return jsonify({
        "message": result,
        "products": []  # Add product recommendations here if needed
    })

# Route to handle image upload requests
@app.route("/upload", methods=["POST"])
def upload_image():
    """Handle image upload requests from the frontend."""
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Save the uploaded file temporarily
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    try:
        # Call YOLOv5 detection script
        detected_objects = run_yolov5_detection(file_path)
        return jsonify({"detected_objects": detected_objects})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up: Delete the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

def extract_entities(user_input):
    """Extract entities from user input using SpaCy."""
    doc = nlp(user_input)
    entities = {ent.label_: ent.text for ent in doc.ents}
    return entities

def run_yolov5_detection(image_path):
    """Run YOLOv5 detection on the uploaded image."""
    # Path to the YOLOv5 detection script
    yolov5_script = os.path.abspath("../yolov5/detectImg.py")

    # Run the YOLOv5 detection script
    command = [
        "python",
        yolov5_script,
        "--source", image_path,
        "--conf", "0.25",  # Confidence threshold
        "--save-txt",  # Save results to text file
        "--project", app.config["UPLOAD_FOLDER"],  # Save results in the upload folder
    ]
    result = subprocess.run(command, capture_output=True, text=True)

    # Check for errors
    if result.returncode != 0:
        raise Exception(f"YOLOv5 detection failed: {result.stderr}")

    # Parse the detection results
    detected_objects = parse_detection_results(image_path)
    return detected_objects

def parse_detection_results(image_path):
    """Parse YOLOv5 detection results."""
    # Example: Read the detection results from the saved text file
    results_file = os.path.splitext(image_path)[0] + ".txt"
    if not os.path.exists(results_file):
        return []

    detected_objects = []
    with open(results_file, "r") as f:
        for line in f:
            # Parse each line (format: class_id x_center y_center width height)
            class_id = int(line.split()[0])
            detected_objects.append(f"object_{class_id}")

    return detected_objects

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)