import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

app.use(cors({
    origin: 'http://localhost:5173', 
    credentials: true
}));
app.use(express.json()); 
app.use(express.urlencoded({ extended: true }));

app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

app.get('/', (req, res) => {
    res.json({
        message: "Selamat datang di API E-Office Kampus!",
        status: "Aktif"
    });
});

app.listen(PORT, () => {
    console.log(`=========================================`);
    console.log(`🚀 Server E-Office Berjalan Lancar!`);
    console.log(`📱 URL Server: http://localhost:${PORT}`);
    console.log(`=========================================`);
});