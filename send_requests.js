// This script uses the 'axios' library to send a POST request to your local Flask server.

// 1. Import the axios library
const axios = require('axios');

// 2. Define the URL of your local API endpoint
const url = 'http://127.0.0.1:5000/api/process';

// 3. Define the data (the payload) you want to send.
// This is the same JSON object you used in curl and the .http file.
const data = {
    "query": "I am a 46-year-old male. I was in a car accident last week and required immediate knee surgery. My insurance policy is only 3 months old. Is the hospitalization for the surgery covered?"
};

// 4. Define an async function to make the request
const sendRequest = async () => {
    console.log("Sending POST request to the local server...");
    try {
        // Use axios.post to send the request. It returns a promise.
        const response = await axios.post(url, data, {
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // 5. If the request is successful, print the response data
        console.log("\n--- SERVER RESPONSE ---");
        // We use JSON.stringify to "pretty-print" the JSON object
        console.log(JSON.stringify(response.data, null, 2));

    } catch (error) {
        // 6. If an error occurs, print the error details
        console.error("\n--- AN ERROR OCCURRED ---");
        if (error.response) {
            // The request was made and the server responded with a status code
            // that falls out of the range of 2xx
            console.error("Status:", error.response.status);
            console.error("Data:", error.response.data);
        } else if (error.request) {
            // The request was made but no response was received
            console.error("No response received from the server. Is it running?");
            console.error(error.request);
        } else {
            // Something happened in setting up the request that triggered an Error
            console.error('Error', error.message);
        }
    }
};

// 7. Call the function to execute the request
sendRequest();