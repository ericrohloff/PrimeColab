from google.colab import output
from IPython.display import display, Javascript, HTML

# Initialize an empty list to store numbers
numbers_list = []

# Process the data sent from JS
def process_data_from_js(data):
    # Process the data received from JavaScript
    print("Data received from JavaScript:", data)
    
    # Append the numerical data to numbers_list
    numbers_list.append(data)
    
    # Optionally, you can further process or manipulate the data here
    print("Stored in Python as:", data)

# Register the function to handle data from JavaScript
output.register_callback('notebook.processDataFromJS', process_data_from_js)

# HTML and JavaScript code
html_code = """
<div id="output-area"></div>
"""

js_code = """
class SerialManager {
    constructor() {
        this.port = null;
        this.reader = null;
        this.writer = null;
        this.connected = false;
    }

    async askForSerial() {
        if (!('serial' in navigator)) {
            console.log("Use Chrome please");
            return;
        }
        this.port = await navigator.serial.requestPort();
        await this.port.open({ baudRate: 115200 });
        console.log('Opened Port: ' + this.port);

        this.encoder = new TextEncoderStream();
        this.writer = this.encoder.writable.getWriter();
        this.encoder.readable.pipeTo(this.port.writable);

        this.decoder = new TextDecoderStream();
        this.port.readable.pipeTo(this.decoder.writable);
        this.reader = this.decoder.readable.getReader();

        this.connected = true;
    }

    async write(data) {
        if (this.writer) {
            await this.writer.write(data + '\\r\\n');
            console.log("Wrote to stream: " + data);
        } else {
            console.log("Writer not initialized");
        }
    }

    async readLine() {
        let reply = '';
        while (true) {
            const { value, done } = await this.reader.read();
            if (done) {
                console.log('Stream closed');
                this.reader.releaseLock();
                break;
            }
            reply += value;
            if (value.includes('\\n')) {
                break;
            }
        }
        return reply;
    }

    async readResponse() {
        let response = '';
        while (true) {
            let line = await this.readLine();
            response += line;
            if (line.includes('>>> ')) {
                break;
            }
        }
        return response;
    }

    sanitizeData(data) {
        let sanitizedData = parseFloat(data.match(/[-+]?[0-9]*\\.?[0-9]+/)[0]);
        return sanitizedData;

    }

    async uploadCode(code) {
        await this.write('\\x01' + code + '\\x04');  // Enter raw REPL mode
        let reply = await this.readLine();  // Read initial prompt
        console.log(reply);
        
        let response = '';
        while (!reply.includes('>>>')) {
            reply = await this.readLine();
            console.log(reply);
            let sanitizedData = this.sanitizeData(reply);
            google.colab.kernel.invokeFunction('notebook.processDataFromJS', [sanitizedData], {});
            response += reply + '\\n';
        }
        console.log(response);
        
        
        google.colab.kernel.invokeFunction('notebook.processDataFromJS', [sanitizedData], {});
    }
}

async function initializeSerial() {
    let serialManager = new SerialManager();

    const connectButton = document.createElement('button');
    connectButton.innerHTML = 'Connect';
    connectButton.onclick = async () => {
        await serialManager.askForSerial();
    };

    const input = document.createElement('textarea');
    input.id = 'input';
    input.rows = '5';
    input.cols = '50';
    input.placeholder = 'Type code here';

    const uploadCodeButton = document.createElement('button');
    uploadCodeButton.innerHTML = 'Upload Code';
    uploadCodeButton.onclick = async () => {
        const codeElement = document.getElementById('input');
        let code = codeElement.value;
        code = code.replace(/\\n/g, '\\r\\n');
        await serialManager.uploadCode(code);
    };

    document.querySelector("#output-area").appendChild(connectButton);
    document.querySelector("#output-area").appendChild(input);
    document.querySelector("#output-area").appendChild(uploadCodeButton);
}

initializeSerial();
"""

# Display the HTML and JavaScript in the notebook
display(HTML(html_code))
display(Javascript(js_code))