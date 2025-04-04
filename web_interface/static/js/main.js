// Main JavaScript for NLQ Translator web interface

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Ace editors
    const mappingEditor = ace.edit("mappingEditor");
    mappingEditor.setTheme("ace/theme/chrome");
    mappingEditor.session.setMode("ace/mode/json");
    mappingEditor.setOptions({
        fontSize: "12pt",
        showPrintMargin: false
    });

    const queryEditor = ace.edit("queryEditor");
    queryEditor.setTheme("ace/theme/chrome");
    queryEditor.session.setMode("ace/mode/json");
    queryEditor.setOptions({
        fontSize: "12pt",
        showPrintMargin: false
    });

    const resultsEditor = ace.edit("resultsEditor");
    resultsEditor.setTheme("ace/theme/chrome");
    resultsEditor.session.setMode("ace/mode/json");
    resultsEditor.setOptions({
        fontSize: "12pt",
        showPrintMargin: false,
        readOnly: true
    });

    // Elements
    const modelSelect = document.getElementById('modelSelect');
    const apiKeyContainer = document.getElementById('apiKeyContainer');
    const apiKeyInput = document.getElementById('apiKey');
    const cloudIdRadio = document.getElementById('cloudIdRadio');
    const hostsRadio = document.getElementById('hostsRadio');
    const cloudIdContainer = document.getElementById('cloudIdContainer');
    const hostsContainer = document.getElementById('hostsContainer');
    const connectButton = document.getElementById('connectButton');
    const disconnectButton = document.getElementById('disconnectButton');
    const connectionStatus = document.getElementById('connectionStatus');
    const translateButton = document.getElementById('translateButton');
    const fixButton = document.getElementById('fixButton');
    const improveButton = document.getElementById('improveButton');
    const executeButton = document.getElementById('executeButton');
    const copyButton = document.getElementById('copyButton');
    const naturalLanguageQuery = document.getElementById('naturalLanguageQuery');
    const errorMessage = document.getElementById('errorMessage');
    const improvementGoal = document.getElementById('improvementGoal');
    const resultsCard = document.getElementById('resultsCard');
    
    // Status modal
    const statusModal = new bootstrap.Modal(document.getElementById('statusModal'));
    const statusModalBody = document.getElementById('statusModalBody');

    // Connection state
    let isConnected = false;

    // Event listeners for UI interactions
    modelSelect.addEventListener('change', function() {
        if (this.value === 'openai') {
            apiKeyContainer.classList.remove('d-none');
        } else {
            apiKeyContainer.classList.add('d-none');
        }
    });

    cloudIdRadio.addEventListener('change', function() {
        if (this.checked) {
            cloudIdContainer.classList.remove('d-none');
            hostsContainer.classList.add('d-none');
        }
    });

    hostsRadio.addEventListener('change', function() {
        if (this.checked) {
            hostsContainer.classList.remove('d-none');
            cloudIdContainer.classList.add('d-none');
        }
    });

    // Connect to Elasticsearch
    connectButton.addEventListener('click', async function() {
        // Show status modal
        statusModalBody.textContent = 'Connecting to Elasticsearch...';
        statusModal.show();

        // Get connection parameters
        const connectionData = {
            index: document.getElementById('index').value
        };

        if (cloudIdRadio.checked) {
            connectionData.cloud_id = document.getElementById('cloudId').value;
        } else {
            connectionData.hosts = document.getElementById('hosts').value;
        }

        connectionData.username = document.getElementById('username').value;
        connectionData.password = document.getElementById('password').value;

        try {
            const response = await fetch('/api/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(connectionData)
            });

            const data = await response.json();

            if (data.connected) {
                isConnected = true;
                connectButton.disabled = true;
                disconnectButton.disabled = false;
                executeButton.disabled = false;
                connectionStatus.textContent = 'Connected to Elasticsearch';
                connectionStatus.classList.remove('alert-info', 'alert-danger');
                connectionStatus.classList.add('alert-success');

                // Update mapping if available
                if (data.mapping) {
                    try {
                        const mappingObj = JSON.parse(data.mapping);
                        mappingEditor.setValue(JSON.stringify(mappingObj, null, 2), -1);
                    } catch (e) {
                        console.error('Error parsing mapping:', e);
                    }
                }

                statusModalBody.textContent = 'Successfully connected to Elasticsearch!';
            } else {
                connectionStatus.textContent = `Connection failed: ${data.error || 'Unknown error'}`;
                connectionStatus.classList.remove('alert-info', 'alert-success');
                connectionStatus.classList.add('alert-danger');
                statusModalBody.textContent = `Connection failed: ${data.error || 'Unknown error'}`;
            }
        } catch (error) {
            console.error('Error connecting to Elasticsearch:', error);
            connectionStatus.textContent = `Connection error: ${error.message}`;
            connectionStatus.classList.remove('alert-info', 'alert-success');
            connectionStatus.classList.add('alert-danger');
            statusModalBody.textContent = `Connection error: ${error.message}`;
        }

        // Wait a bit before hiding modal
        setTimeout(() => {
            statusModal.hide();
        }, 1500);
    });

    // Disconnect from Elasticsearch
    disconnectButton.addEventListener('click', async function() {
        statusModalBody.textContent = 'Disconnecting from Elasticsearch...';
        statusModal.show();

        try {
            const response = await fetch('/api/disconnect', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                isConnected = false;
                connectButton.disabled = false;
                disconnectButton.disabled = true;
                executeButton.disabled = true;
                connectionStatus.textContent = 'Not connected to Elasticsearch';
                connectionStatus.classList.remove('alert-success', 'alert-danger');
                connectionStatus.classList.add('alert-info');
                statusModalBody.textContent = 'Successfully disconnected from Elasticsearch!';
            } else {
                statusModalBody.textContent = `Disconnection failed: ${data.error || 'Unknown error'}`;
            }
        } catch (error) {
            console.error('Error disconnecting from Elasticsearch:', error);
            statusModalBody.textContent = `Disconnection error: ${error.message}`;
        }

        // Wait a bit before hiding modal
        setTimeout(() => {
            statusModal.hide();
        }, 1500);
    });

    // Translate natural language to Elasticsearch query
    translateButton.addEventListener('click', async function() {
        if (!naturalLanguageQuery.value.trim()) {
            alert('Please enter a natural language query');
            return;
        }

        statusModalBody.textContent = 'Translating query...';
        statusModal.show();

        try {
            // Get mapping from editor
            let mapping = null;
            try {
                mapping = mappingEditor.getValue();
            } catch (e) {
                console.error('Error getting mapping:', e);
            }

            const translateData = {
                query: naturalLanguageQuery.value,
                mapping: mapping
            };

            // Add API key if using OpenAI
            if (modelSelect.value === 'openai' && apiKeyInput.value) {
                translateData.api_key = apiKeyInput.value;
            }

            const response = await fetch('/api/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(translateData)
            });

            const data = await response.json();

            if (data.success) {
                try {
                    const queryObj = JSON.parse(data.query);
                    queryEditor.setValue(JSON.stringify(queryObj, null, 2), -1);
                    statusModalBody.textContent = 'Translation successful!';
                } catch (e) {
                    console.error('Error parsing query:', e);
                    queryEditor.setValue(data.query, -1);
                    statusModalBody.textContent = 'Translation successful, but result may not be valid JSON.';
                }
            } else {
                statusModalBody.textContent = `Translation failed: ${data.error || 'Unknown error'}`;
            }
        } catch (error) {
            console.error('Error translating query:', error);
            statusModalBody.textContent = `Translation error: ${error.message}`;
        }

        // Wait a bit before hiding modal
        setTimeout(() => {
            statusModal.hide();
        }, 1500);
    });

    // Fix Elasticsearch query
    fixButton.addEventListener('click', async function() {
        let queryStr = queryEditor.getValue();
        if (!queryStr.trim()) {
            alert('No query to fix');
            return;
        }

        statusModalBody.textContent = 'Fixing query...';
        statusModal.show();

        try {
            // Get mapping from editor
            let mapping = null;
            try {
                mapping = mappingEditor.getValue();
            } catch (e) {
                console.error('Error getting mapping:', e);
            }

            const fixData = {
                query: queryStr,
                mapping: mapping,
                error: errorMessage.value
            };

            // Add API key if using OpenAI
            if (modelSelect.value === 'openai' && apiKeyInput.value) {
                fixData.api_key = apiKeyInput.value;
            }

            const response = await fetch('/api/fix', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(fixData)
            });

            const data = await response.json();

            if (data.success) {
                try {
                    const queryObj = JSON.parse(data.query);
                    queryEditor.setValue(JSON.stringify(queryObj, null, 2), -1);
                    statusModalBody.textContent = 'Query fixed successfully!';
                } catch (e) {
                    console.error('Error parsing fixed query:', e);
                    queryEditor.setValue(data.query, -1);
                    statusModalBody.textContent = 'Query fixed, but result may not be valid JSON.';
                }
            } else {
                statusModalBody.textContent = `Query fix failed: ${data.error || 'Unknown error'}`;
            }
        } catch (error) {
            console.error('Error fixing query:', error);
            statusModalBody.textContent = `Query fix error: ${error.message}`;
        }

        // Wait a bit before hiding modal
        setTimeout(() => {
            statusModal.hide();
        }, 1500);
    });

    // Improve Elasticsearch query
    improveButton.addEventListener('click', async function() {
        let queryStr = queryEditor.getValue();
        if (!queryStr.trim()) {
            alert('No query to improve');
            return;
        }

        statusModalBody.textContent = 'Improving query...';
        statusModal.show();

        try {
            // Get mapping from editor
            let mapping = null;
            try {
                mapping = mappingEditor.getValue();
            } catch (e) {
                console.error('Error getting mapping:', e);
            }

            const improveData = {
                query: queryStr,
                mapping: mapping,
                goal: improvementGoal.value
            };

            // Add API key if using OpenAI
            if (modelSelect.value === 'openai' && apiKeyInput.value) {
                improveData.api_key = apiKeyInput.value;
            }

            const response = await fetch('/api/improve', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(improveData)
            });

            const data = await response.json();

            if (data.success) {
                try {
                    const queryObj = JSON.parse(data.query);
                    queryEditor.setValue(JSON.stringify(queryObj, null, 2), -1);
                    statusModalBody.textContent = 'Query improved successfully!';
                } catch (e) {
                    console.error('Error parsing improved query:', e);
                    queryEditor.setValue(data.query, -1);
                    statusModalBody.textContent = 'Query improved, but result may not be valid JSON.';
                }
            } else {
                statusModalBody.textContent = `Query improvement failed: ${data.error || 'Unknown error'}`;
            }
        } catch (error) {
            console.error('Error improving query:', error);
            statusModalBody.textContent = `Query improvement error: ${error.message}`;
        }

        // Wait a bit before hiding modal
        setTimeout(() => {
            statusModal.hide();
        }, 1500);
    });

    // Execute Elasticsearch query
    executeButton.addEventListener('click', async function() {
        if (!isConnected) {
            alert('Please connect to Elasticsearch first');
            return;
        }

        let queryStr = queryEditor.getValue();
        if (!queryStr.trim()) {
            alert('No query to execute');
            return;
        }

        statusModalBody.textContent = 'Executing query...';
        statusModal.show();

        try {
            const executeData = {
                query: queryStr
            };

            const response = await fetch('/api/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(executeData)
            });

            const data = await response.json();

            if (data.success) {
                try {
                    const resultsObj = JSON.parse(data.results);
                    resultsEditor.setValue(JSON.stringify(resultsObj, null, 2), -1);
                    resultsCard.style.display = 'block';
                    statusModalBody.textContent = `Query executed successfully! Found ${data.hit_count} results.`;
                } catch (e) {
                    console.error('Error parsing results:', e);
                    resultsEditor.setValue(data.results, -1);
                    resultsCard.style.display = 'block';
                    statusModalBody.textContent = 'Query executed, but results may not be valid JSON.';
                }
            } else {
                statusModalBody.textContent = `Query execution failed: ${data.error || 'Unknown error'}`;
            }
        } catch (error) {
            console.error('Error executing query:', error);
            statusModalBody.textContent = `Query execution error: ${error.message}`;
        }

        // Wait a bit before hiding modal
        setTimeout(() => {
            statusModal.hide();
        }, 1500);
    });

    // Copy query to clipboard
    copyButton.addEventListener('click', function() {
        const queryText = queryEditor.getValue();
        navigator.clipboard.writeText(queryText).then(
            function() {
                // Success
                const originalText = copyButton.textContent;
                copyButton.textContent = 'Copied!';
                setTimeout(() => {
                    copyButton.textContent = originalText;
                }, 2000);
            },
            function(err) {
                console.error('Could not copy text: ', err);
                alert('Failed to copy query to clipboard');
            }
        );
    });

    // Validate query when editor content changes
    queryEditor.session.on('change', debounce(function() {
        try {
            const queryStr = queryEditor.getValue();
            if (!queryStr.trim()) return;
            
            // Try to parse as JSON
            JSON.parse(queryStr);
            
            // If successful, remove error markers
            queryEditor.session.clearAnnotations();
        } catch (e) {
            // Mark as error
            queryEditor.session.setAnnotations([{
                row: 0,
                column: 0,
                text: "Invalid JSON: " + e.message,
                type: "error"
            }]);
        }
    }, 500));

    // Validate mapping when editor content changes
    mappingEditor.session.on('change', debounce(function() {
        try {
            const mappingStr = mappingEditor.getValue();
            if (!mappingStr.trim()) return;
            
            // Try to parse as JSON
            JSON.parse(mappingStr);
            
            // If successful, remove error markers
            mappingEditor.session.clearAnnotations();
        } catch (e) {
            // Mark as error
            mappingEditor.session.setAnnotations([{
                row: 0,
                column: 0,
                text: "Invalid JSON: " + e.message,
                type: "error"
            }]);
        }
    }, 500));

    // Helper function for debouncing
    function debounce(func, wait) {
        let timeout;
        return function() {
            const context = this, args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                func.apply(context, args);
            }, wait);
        };
    }
});
