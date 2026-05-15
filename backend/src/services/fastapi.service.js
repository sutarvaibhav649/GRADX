const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

class FastAPIService {
    constructor() {
        this.baseURL = process.env.FASTAPI_URL || 'http://localhost:8000';
        this.client = axios.create({
            baseURL: this.baseURL,
            timeout: 60000, // 60 seconds for AI processing
        });
    }

    async uploadModelAnswer(imagePath) {
        try {
            const formData = new FormData();
            formData.append('file', fs.createReadStream(imagePath));
            
            const response = await this.client.post('/api/evaluation/upload-model', formData, {
                headers: { ...formData.getHeaders() }
            });
            return response.data;
        } catch (error) {
            console.error('FastAPI upload model error:', error.message);
            throw error;
        }
    }

    async evaluateStudentImage(imagePath) {
        try {
            const formData = new FormData();
            formData.append('file', fs.createReadStream(imagePath));
            
            const response = await this.client.post('/api/evaluation/evaluate-image', formData, {
                headers: { ...formData.getHeaders() }
            });
            return response.data;
        } catch (error) {
            console.error('FastAPI evaluate error:', error.message);
            throw error;
        }
    }

    async getModelAnswer() {
        try {
            const response = await this.client.get('/api/evaluation/model');
            return response.data;
        } catch (error) {
            return { success: false, model_answer: null };
        }
    }
}

module.exports = new FastAPIService();