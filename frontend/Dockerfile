FROM node:20-alpine

WORKDIR /app

# Menyalin package.json dan package-lock.json terlebih dahulu untuk memanfaatkan Docker cache
COPY package*.json ./

# Menginstal seluruh dependencies
RUN npm install

# Menyalin sisa kode sumber frontend
COPY . .

# Mengekspos port 3000 (port default Next.js)
EXPOSE 3000

# Menjalankan Next.js dev server
CMD ["npm", "run", "dev"]
